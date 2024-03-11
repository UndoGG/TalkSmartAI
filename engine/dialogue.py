import asyncio
import os
from typing import List

from aiogram import Bot, types
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, BufferedInputFile
from dotenv import load_dotenv

import enums
import logging_engine
from API.gpt import ChatGPTAPI
from API.tts import OpenAITTSAPI
from database.conversations import ConversationManagement
from pydantic_models.conversations import ConversationForm, Conversation, ConversationHistory
from pydantic_models.users import User
from tools.yaml_parser import read_yaml_file

load_dotenv()
logger = logging_engine.get_logger()



class Dialogue(ChatGPTAPI, OpenAITTSAPI):
    def __init__(self, bot: Bot, user: User):
        ChatGPTAPI.__init__(self)
        OpenAITTSAPI.__init__(self)
        self.bot = bot
        self.user = user
        self.config = read_yaml_file(os.path.join('config', 'logical.yml'))

        new_messages = {}
        for key, value in self.config['messages'].items():
            if isinstance(value, list):
                for ind, list_item in enumerate(value):
                    new_item = ''
                    for letter in list_item:
                        if letter in self.config['system']['reserved_chars']:
                            new_item += '\\' + letter
                        else:
                            new_item += letter
                    value[ind] = new_item
                new_messages[key] = value
            else:
                new_value = ''
                for letter in value:
                    if letter in self.config['system']['reserved_chars']:
                        new_value += '\\' + letter
                    else:
                        new_value += letter
                new_messages[key] = new_value
        self.config['messages'] = new_messages

    def update(self):
        self.config = read_yaml_file(os.path.join('config', 'logical.yml'))

    async def cleanup(self):
        conversation = await ConversationManagement.get(id=self.user.id, by=enums.GetByEnum.USER_ID)
        if conversation:
            for item in conversation:
                if not item.closed:
                    await ConversationManagement.edit(item.id, closed=True)



    async def continue_conversation(self, mes: Message, conversation: List[Conversation], user_text: str):
        conversation = [ConversationHistory(role=conv.role, message=conv.text) for conv in conversation]
        if self.config['preferences']['show_generating_response_text'] is True:
            await mes.reply(self.config['messages']['generation_in_progress'], parse_mode="MarkdownV2")

        await self.bot.send_chat_action(mes.chat.id, action='record_voice')

        tasks = []

        async def gpt():
            return await self.post_ask(user_text, history=conversation)

        tasks.append(gpt())

        if self.config['preferences']['rate_speech'] is True:
            tasks.append(self.rate_speech(mes, user_text))



        response = (await asyncio.gather(*tasks))[0]  # gpt() response
        if isinstance(response, int):
            if response == -1:
                await mes.reply('Response generation failed cause of Network failure!\n Please, try again!')
                return
            await self.send(mes.chat.id,
                            f'Unable to generate response. Server responded with status code: {response}.\nPlease, contact with developers!')
            return
        try:
            text = response['choices'][0]['message']['content']
        except KeyError:
            logger.error(f'[bold red]Unserializable JSON: \n{response}')
            await mes.reply(
                'Unable to generate response. Server responded with unserializable JSON. \nPlease, try again\nIf this issue continues, contact with developers')
            return

        user_phrase = await ConversationManagement.create(ConversationForm(user_id=self.user.id,
                                                                           text=user_text,
                                                                           role=enums.SpeakerRoleEnum.USER))

        phrase = await ConversationManagement.create(ConversationForm(user_id=self.user.id,
                                                                      text=text,
                                                                      role=enums.SpeakerRoleEnum.ASSISTANT))

        tts_response = await self.post_text_to_speech(text)
        if isinstance(tts_response, int):
            await self.send(mes.chat.id,
                            f'Unable to convert TTS. Server responded with status code: {tts_response}.\nPlease, contact with developers!')
            return

        with open(tts_response, 'rb') as voice_file:
            voice = BufferedInputFile(voice_file.read(), tts_response)

        buttons = [
            [InlineKeyboardButton(text=self.config['buttons']['transcript'], callback_data=f'trc_{phrase.id}')]
        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await self.bot.send_voice(mes.chat.id, voice=voice, reply_markup=keyboard)
        try:
            os.remove(tts_response)
        except Exception:
            logger.exception('[bold red]Unable to remove temp TTS')

    async def rate_speech(self, original_mes: Message, decoded_text: str):
        prompt = self.config['requests']['rate_user_speak']['prompt'].format(decoded_text) + '\n' + \
                 self.config['requests']['rate_user_speak']['rules']
        await self.bot.send_chat_action(original_mes.chat.id, action='record_voice')
        response = await self.post_ask(prompt)
        if isinstance(response, int):
            if response == -1:
                await original_mes.reply('Speech rating failed cause of Network failure!\n Please, try again!')
                return
            await self.send(original_mes.chat.id,
                            f'Unable to rate speech. Server responded with status code: {response}.\nPlease, contact with developers!')
            return
        try:
            text = response['choices'][0]['message']['content']
        except KeyError:
            logger.error(f'[bold red]Unserializable JSON: \n{response}')
            await original_mes.reply(
                'Unable to rate speech. Server responded with unserializable JSON. \nPlease, try again\nIf this issue continues, contact with developers')
            return

        await ConversationManagement.create(ConversationForm(user_id=self.user.id,
                                                             text=text,
                                                             role=enums.SpeakerRoleEnum.RATE))

        await original_mes.reply(self.config['messages']['speech_rate_title'] + text, parse_mode="MarkdownV2")

    async def start_conversation(self, mes: Message, scenario_data: dict, topic: str | None, addition: str = None,
                                 skip_rate: bool = False):
        command_buttons = [
            types.KeyboardButton(text='Stop'),
        ]
        markup = types.ReplyKeyboardMarkup(keyboard=[command_buttons], resize_keyboard=True, one_time_keyboard=True)
        await mes.reply(self.config['messages']['generation_in_progress'], reply_markup=markup, parse_mode="MarkdownV2")
        await self.bot.send_chat_action(mes.chat.id, action='record_voice')
        try:
            request = self.config['requests'][scenario_data['request_name']]
        except KeyError:
            await mes.reply(
                f'Unable to find request with name {scenario_data["request_name"]}. Please, contact with developers')
            return

        if addition:
            prompt = request['prompt'].format(topic, addition) + "\n" + request['rules']
        else:
            prompt = request['prompt'].format(topic) + "\n" + request['rules']

        await ConversationManagement.create(ConversationForm(user_id=self.user.id,
                                                             text=prompt,
                                                             role=enums.SpeakerRoleEnum.SYSTEM))
        await self.bot.send_chat_action(mes.chat.id, action='record_voice')

        response = None

        tasks = []

        async def gpt():
            return await self.post_ask(prompt)

        tasks.append(gpt())

        if all((self.config['preferences']['rate_speech_on_user_opinion'],
                self.config['preferences']['rate_speech'])) and addition is not None and not skip_rate:
            tasks.append(self.rate_speech(mes, addition))

        response = (await asyncio.gather(*tasks))[0]  # gpt() response

        if isinstance(response, int):
            if response == -1:
                await mes.reply('Response generation failed cause of Network failure!\n Please, try again!')
                return
            await self.send(mes.chat.id,
                            f'Unable to generate response. Server responded with status code: {response}.\nPlease, contact with developers!')
            return
        try:
            text = response['choices'][0]['message']['content']
        except KeyError:
            logger.error(f'[bold red]Unserializable JSON: \n{response}')
            await mes.reply(
                'Unable to generate response. Server responded with unserializable JSON. \nPlease, try again\nIf this issue continues, contact with developers')
            return

        await self.bot.send_chat_action(mes.chat.id, action='record_voice')
        tts_response = await self.post_text_to_speech(text)
        if isinstance(tts_response, int):
            await self.send(mes.chat.id,
                            f'Unable to convert TTS. Server responded with status code: {tts_response}.\nPlease, contact with developers!')
            return
        await self.bot.send_chat_action(mes.chat.id, action='record_voice')
        with open(tts_response, 'rb') as voice_file:
            voice = BufferedInputFile(voice_file.read(), tts_response)

        phrase = await ConversationManagement.create(ConversationForm(user_id=self.user.id,
                                                                      text=text,
                                                                      role=enums.SpeakerRoleEnum.ASSISTANT))

        buttons = [
            [InlineKeyboardButton(text=self.config['buttons']['transcript'], callback_data=f'trc_{phrase.id}')]
        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await self.bot.send_chat_action(mes.chat.id, action='record_voice')
        await self.bot.send_voice(mes.chat.id, voice=voice, reply_markup=keyboard)

        try:
            os.remove(tts_response)
        except Exception:
            logger.exception('[bold red]Unable to remove temp TTS')

    async def send(self, chat_id: int, message: str, reply_markup=None):  # Shortcut
        return await self.bot.send_message(chat_id, message, reply_markup=reply_markup)

    async def ask_topic_provider(self, mes: Message, option: str):
        self.update()

        buttons = [
            [InlineKeyboardButton(text=self.config['buttons']['generate_topics'], callback_data=f'gen_{option}')],
            [InlineKeyboardButton(text=self.config['buttons']['provide_topic'], callback_data=f'pro_{option}')]

        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await mes.reply(self.config['messages']['provide_topics'], reply_markup=keyboard, parse_mode="MarkdownV2")

    async def response_scenario(self, scenario_data: dict, mes: Message, scenario_name: str):
        self.update()

        prompt = scenario_data['request']['prompt'] + "\n" + scenario_data['request']['rules']

        response = await self.post_ask(prompt, skip_parse=True)
        if isinstance(response, int):
            if response == -1:
                await mes.reply('Response generation failed cause of Network failure!\n Please, try again!')
                return
            await mes.reply(
                f'Unable to generate response. Server responded with status code: {response}.\nPlease, try again\nIf this issue continues, contact with developers')
            return
        try:
            topics = response['choices'][0]['message']['content'].replace('\n', '')
        except KeyError:
            logger.error(f'Unable to serialize response!\n{response}')
            await mes.reply(
                'Unable to generate response. Server responded with unserializable data. \nPlease, try again\nIf this issue continues, contact with developers')
            return

        try:
            topics = eval(topics)
        except Exception:
            logger.error(f'Unable to serialize response!\n{response}')
            await mes.reply(
                'Unable to generate response. Server responded with unserializable data. \nPlease, try again\nIf this issue continues, contact with developers')
            return

        buttons = []
        for topic_index, topic in enumerate(topics):
            buttons.append([InlineKeyboardButton(text=topic, callback_data=str(topic_index) + "_" + scenario_name)])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await mes.reply(self.config['messages']['select_topic'], reply_markup=keyboard, parse_mode="MarkdownV2")
