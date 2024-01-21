import os
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

import enums
import logging_engine
from API.gpt import ChatGPTAPI
from database.conversations import ConversationManagement
from pydantic_models.conversations import ConversationForm
from pydantic_models.users import User
from tools.yaml_parser import read_yaml_file


load_dotenv()
logger = logging_engine.get_logger()


class Dialogue(ChatGPTAPI):
    def __init__(self, bot: Bot, user: User):
        super().__init__()
        self.bot = bot
        self.user = user
        self.config = read_yaml_file(os.path.join('config', 'telegram.yml'))

    def update(self):
        self.config = read_yaml_file(os.path.join('config', 'telegram.yml'))

    async def start_conversation(self, mes: Message, scenario_data: dict, topic: str):
        try:
            request = self.config['requests'][scenario_data['request_name']]
        except KeyError:
            await mes.reply(f'Unable to find request with name {scenario_data["request_name"]}. Please, contact with developers')
            return

        prompt = request['prompt'].format(topic) + "\n" + request['rules']
        response = await self.post_ask(prompt)
        if isinstance(response, int):
            await self.send(mes.chat.id, f'Unable to generate response. Server responded with status code: {response}.\nPlease, contact with developers!')
            return
        text = response['choices'][0]['message']['content'].replace('\n', '')
        await mes.reply(text=text)
        await ConversationManagement.create(ConversationForm(user_id=self.user.id,
                                                             text=text,
                                                             role=enums.SpeakerRoleEnum.ASSISTANT))

    async def send(self, chat_id: int, message: str, reply_markup=None):  # Shortcut
        return await self.bot.send_message(chat_id, message, reply_markup=reply_markup)

    async def ask_topic_provider(self, mes: Message, option: str):
        self.update()

        buttons = [
            [InlineKeyboardButton(text=self.config['buttons']['generate_topics'], callback_data=f'gen_{option}')],
            [InlineKeyboardButton(text=self.config['buttons']['provide_topic'], callback_data=f'pro_{option}')]

        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await self.send(mes.chat.id, self.config['messages']['provide_topics'], reply_markup=keyboard)

    async def response_scenario(self, scenario_data: dict, mes: Message, scenario_name: str):
        self.update()

        prompt = scenario_data['request']['prompt'] + "\n" + scenario_data['request']['rules']

        response = await self.post_ask(prompt)
        if isinstance(response, int):
            await self.send(mes.chat.id, f'Unable to generate response. Server responded with status code: {response}.\nPlease, contact with developers!')
            return
        try:
            topics = response['choices'][0]['message']['content'].replace('\n', '')
        except KeyError:
            logger.error(f'Unable to serialize response!\n{response}')
            await self.send(mes.chat.id, 'Unable to generate response. Server responded with unserializable data. \nPlease, contact with developers')
            return

        try:
            topics = eval(topics)
        except Exception:
            logger.error(f'Unable to serialize response!\n{response}')
            await self.send(mes.chat.id, 'Unable to generate response. Please, try again! If this issue continues, contact with developers')
            return

        buttons = []
        for topic_index, topic in enumerate(topics):
            buttons.append([InlineKeyboardButton(text=topic, callback_data=str(topic_index) + "_" + scenario_name)])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await mes.reply(self.config['messages']['select_topic'], reply_markup=keyboard)
