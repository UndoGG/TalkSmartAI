import os
from typing import List
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

import enums
from database.user_courses import UserCoursesManagement
from logging_engine import get_logger
from pydantic_models.users import User
from tools.yaml_parser import read_yaml_file


logger = get_logger()


class Start:
    def __init__(self, bot: Bot, user: User):
        self.bot = bot
        self.user = user
        self.messages_config: dict = read_yaml_file(os.path.join('config', 'messages.yml'))
        self.courses_config: dict = read_yaml_file(os.path.join('config', 'courses.yml'))

    async def update(self):
        self.messages_config: dict = read_yaml_file(os.path.join('config', 'messages.yml'))

    async def send(self, chat_id: int, message: str):
        """
        Shortcut to self.bot.send_message
        """
        return await self.bot.send_message(chat_id, message)

    async def start(self, msg):
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

    async def welcome(self, msg: Message):
        buttons = [[InlineKeyboardButton(text=self.messages_config['start_button'], callback_data='start')]]

        inline = InlineKeyboardMarkup(inline_keyboard=buttons)
        await msg.reply(self.messages_config['welcome'], reply_markup=inline, parse_mode="HTML")
