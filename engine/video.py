import os

from aiogram import Bot
from aiogram.types import FSInputFile


class VideoHelper:
    @staticmethod
    async def send_video(chat_id, video_name, caption, bot: Bot, reply_to: int = None, **kwargs):
        file = os.path.join('videos', video_name)
        await bot.send_chat_action(chat_id, action='upload_video')

        with open(file, 'rb') as video_file:
            video = FSInputFile(file)
            await bot.send_chat_action(chat_id, action='upload_video')
            if reply_to:
                await bot.send_video(chat_id, video, caption=caption, reply_to_message_id=reply_to, **kwargs)
            else:
                await bot.send_video(chat_id, video, caption=caption, **kwargs)

    @staticmethod
    async def send_photo(chat_id, photo_name, caption, bot: Bot, reply_to: int = None, **kwargs):
        file = os.path.join('photos', photo_name)
        await bot.send_chat_action(chat_id, action='upload_photo')

        with open(file, 'rb') as photo_file:
            photo = FSInputFile(file)
            await bot.send_chat_action(chat_id, action='upload_photo')
            if reply_to:
                await bot.send_photo(chat_id, photo, caption=caption, reply_to_message_id=reply_to, **kwargs)
            else:
                await bot.send_photo(chat_id, photo, caption=caption, **kwargs)

    @staticmethod
    async def send_document(chat_id, document_name, caption, bot: Bot, reply_to: int = None, **kwargs):
        file = os.path.join('documents', document_name)
        await bot.send_chat_action(chat_id, action='upload_document')

        with open(file, 'rb') as document_file:
            document = FSInputFile(file)
            await bot.send_chat_action(chat_id, action='upload_document')
            if reply_to:
                await bot.send_document(chat_id, document, caption=caption, reply_to_message_id=reply_to, **kwargs)
            else:
                await bot.send_document(chat_id, document, caption=caption, **kwargs)
