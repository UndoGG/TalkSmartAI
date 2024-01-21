import os
from typing import List
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from tools.yaml_parser import read_yaml_file


class Start:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config: dict = read_yaml_file(os.path.join('config', 'telegram.yml'))

    async def update(self):
        self.config: dict = read_yaml_file(os.path.join('config', 'telegram.yml'))

    async def send(self, chat_id: int, message: str):
        """
        Shortcut to self.bot.send_message
        """
        return await self.bot.send_message(chat_id, message)

    async def multi_reply(self, msg: Message, messages: List[str], reply: bool = True):
        for message_index, message in enumerate(messages):
            if reply:
                sent = await msg.reply(message)
                if message_index + 1 == len(messages):
                    return sent
            else:
                sent = await self.send(msg.chat.id, message)
                if message_index + 1 == len(messages):
                    return sent

    async def response_welcome(self, msg: Message):
        for message_index, message in enumerate(self.config['messages']['welcome']):
            if message_index + 1 != len(self.config['messages']['welcome']):
                await msg.reply(message)
            else:
                break

        # Last message sending with buttons

        buttons = []

        for scenario in self.config['scenarios']:
            scenario_data = self.config['scenarios'][scenario]
            buttons.append([InlineKeyboardButton(text=scenario_data['name'], callback_data=scenario)])

        inline_kb1 = InlineKeyboardMarkup(inline_keyboard=buttons)
        await msg.reply(self.config['messages']['welcome'][-1], reply_markup=inline_kb1)
