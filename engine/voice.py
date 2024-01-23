import asyncio
import os
import uuid
from typing import BinaryIO
import logging_engine
from API.sst import OpenAISSTAPI
from pydantic_models.users import User


logger = logging_engine.get_logger()


class VoiceEngine(OpenAISSTAPI):
    def __init__(self, user: User):
        super().__init__()
        self.user = user

    # noinspection PyAsyncCall
    async def save_voice(self, voice_bytes: BinaryIO):
        if not os.path.exists('temp'):
            os.mkdir('temp')

        temp_path = os.path.join('temp', str(uuid.uuid1()) + '.mp3')
        #TODO: Add database Voice saving

        with open(temp_path, 'wb') as voice_file:
            voice_file.write(voice_bytes.read())
        return temp_path


    async def decode_voice(self, voice_bytes: BinaryIO):
        saved_path = await self.save_voice(voice_bytes)
        response = await self.post_speech_to_text(saved_path)
        try:
            os.remove(saved_path)
        except Exception:
            logger.exception('Unable to remove temp file')
        return response
