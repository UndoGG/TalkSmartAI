import os
from typing import List

from aiogram import Bot, types
from aiogram.enums import ChatAction
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, InputFile, BufferedInputFile
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
            await mes.reply(self.config['messages']['generation_in_progress'])

        await self.bot.send_chat_action(mes.chat.id, action='record_voice')

        response = await self.post_ask(user_text, history=conversation)
        if isinstance(response, int):
            await self.send(mes.chat.id,
                            f'Unable to generate response. Server responded with status code: {response}.\nPlease, contact with developers!')
            return
        try:
            text = response['choices'][0]['message']['content'].replace('\n', '')
        except KeyError:
            logger.error(f'[bold red]Unserializable JSON: \n{response}')
            await mes.reply(
                'Unable to generate response. Server responded with unserializable JSON. \nPlease, try again\nIf this issue continues, contact with developers')
            return

        await ConversationManagement.create(ConversationForm(user_id=self.user.id,
                                                             text=user_text,
                                                             role=enums.SpeakerRoleEnum.USER))

        phrase = await ConversationManagement.create(ConversationForm(user_id=self.user.id,
                                                                      text=text,
                                                                      role=enums.SpeakerRoleEnum.ASSISTANT))

        await self.bot.send_chat_action(mes.chat.id, action='upload_voice')

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

    async def start_conversation(self, mes: Message, scenario_data: dict, topic: str, user_position: str = None):
        command_buttons = [
            types.KeyboardButton(text='Stop'),
        ]
        markup = types.ReplyKeyboardMarkup(keyboard=[command_buttons], resize_keyboard=True, one_time_keyboard=True)
        await mes.reply(self.config['messages']['generation_in_progress'], reply_markup=markup)
        try:
            request = self.config['requests'][scenario_data['request_name']]
        except KeyError:
            await mes.reply(
                f'Unable to find request with name {scenario_data["request_name"]}. Please, contact with developers')
            return

        if user_position:
            prompt = request['prompt'].format(topic, user_position) + "\n" + request['rules']
        else:
            prompt = request['prompt'].format(topic) + "\n" + request['rules']

        await ConversationManagement.create(ConversationForm(user_id=self.user.id,
                                                             text=prompt,
                                                             role=enums.SpeakerRoleEnum.SYSTEM))

        response = await self.post_ask(prompt)
        if isinstance(response, int):
            await self.send(mes.chat.id,
                            f'Unable to generate response. Server responded with status code: {response}.\nPlease, contact with developers!')
            return
        try:
            text = response['choices'][0]['message']['content'].replace('\n', '')
        except KeyError:
            logger.error(f'[bold red]Unserializable JSON: \n{response}')
            await mes.reply(
                'Unable to generate response. Server responded with unserializable JSON. \nPlease, try again\nIf this issue continues, contact with developers')
            return

        tts_response = await self.post_text_to_speech(text)
        if isinstance(tts_response, int):
            await self.send(mes.chat.id,
                            f'Unable to convert TTS. Server responded with status code: {tts_response}.\nPlease, contact with developers!')
            return

        with open(tts_response, 'rb') as voice_file:
            voice = BufferedInputFile(voice_file.read(), tts_response)

        phrase = await ConversationManagement.create(ConversationForm(user_id=self.user.id,
                                                                      text=text,
                                                                      role=enums.SpeakerRoleEnum.ASSISTANT))

        buttons = [
            [InlineKeyboardButton(text=self.config['buttons']['transcript'], callback_data=f'trc_{phrase.id}')]
        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

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

        await mes.reply(self.config['messages']['provide_topics'], reply_markup=keyboard)

    async def response_scenario(self, scenario_data: dict, mes: Message, scenario_name: str):
        self.update()

        prompt = scenario_data['request']['prompt'] + "\n" + scenario_data['request']['rules']

        response = await self.post_ask(prompt)
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
        await mes.reply(self.config['messages']['select_topic'], reply_markup=keyboard)
