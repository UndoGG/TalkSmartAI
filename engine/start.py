import os
from typing import List
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

import enums
<<<<<<< Updated upstream
from database.user_courses import UserCoursesManagement
from logging_engine import get_logger
=======
from database.conversations import ConversationManagement
from logging_engine import get_logger
from models.promises import PromisesModel
>>>>>>> Stashed changes
from pydantic_models.users import User
from tools.yaml_parser import read_yaml_file


logger = get_logger()


class Start:
    def __init__(self, bot: Bot, user: User):
        self.bot = bot
        self.user = user
        self.messages_config: dict = read_yaml_file(os.path.join('config', 'messages.yml'))
        self.courses_config: dict = read_yaml_file(os.path.join('config', 'courses.yml'))

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

    async def update(self):
        self.messages_config: dict = read_yaml_file(os.path.join('config', 'messages.yml'))

    async def send(self, chat_id: int, message: str):
        """
        Shortcut to self.bot.send_message
        """
        return await self.bot.send_message(chat_id, message)

<<<<<<< Updated upstream
    async def start(self, msg):
=======
    async def cleanup(self):
        conversation = await ConversationManagement.get(id=self.user.id, by=enums.GetByEnum.USER_ID)
        if conversation:
            for item in conversation:
                if not item.closed:
                    await ConversationManagement.edit(item.id, closed=True)

        promises = await PromisesModel.filter(user_id=self.user.id)
        for promise in promises:
            await promise.delete()

    async def multi_reply(self, msg: Message, messages: List[str], reply: bool = True):
        for message_index, message in enumerate(messages):
            if reply:
                sent = await msg.reply(message, parse_mode="MarkdownV2")
                if message_index + 1 == len(messages):
                    return sent
            else:
                sent = await self.send(msg.chat.id, message)
                if message_index + 1 == len(messages):
                    return sent

    async def response_welcome(self, msg: Message):
        for message_index, message in enumerate(self.config['messages']['welcome']):
            if message_index + 1 != len(self.config['messages']['welcome']):
                print(message)
                print(message_index)
                await msg.reply(message, parse_mode="MarkdownV2")
            else:
                break

        # Last message sending with buttons

>>>>>>> Stashed changes
        buttons = []
        for name, data in self.courses_config['courses'].items():
            user_courses = await UserCoursesManagement.get(id=self.user.id, by=enums.GetByEnum.USER_ID)
            if name in [i.course_name for i in user_courses]:
                price_element = '✅'
            else:
                price_element = data['display_price']
            buttons.append([InlineKeyboardButton(text=self.messages_config['course_name_format'].format(data['display_name'], price_element), callback_data=f"CRS_{name}")])

        inline = InlineKeyboardMarkup(inline_keyboard=buttons)
        await msg.reply(self.messages_config['welcome_after_start'], parse_mode="HTML")
        await msg.reply(self.messages_config['select_course'], reply_markup=inline, parse_mode="HTML")

<<<<<<< Updated upstream
    async def welcome(self, msg: Message):
        buttons = [[InlineKeyboardButton(text=self.messages_config['start_button'], callback_data='start')]]

        inline = InlineKeyboardMarkup(inline_keyboard=buttons)
        await msg.reply(self.messages_config['welcome'], reply_markup=inline, parse_mode="HTML")
=======
        inline_kb1 = InlineKeyboardMarkup(inline_keyboard=buttons)
        await msg.reply(self.config['messages']['welcome'][-1], reply_markup=inline_kb1, parse_mode="MarkdownV2")
>>>>>>> Stashed changes
