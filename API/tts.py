import asyncio
import json
import os
import uuid

import aiofiles
import aiohttp
from dotenv import load_dotenv

from logging_engine import get_logger
from tools import yaml_parser

load_dotenv()


logger = get_logger()


class OpenAITTSAPI:
    def __init__(self):
        self.openai_token = os.environ['OPENAI_TOKEN']
        self.tts_config = yaml_parser.read_yaml_file(os.path.join("config", "api.yml"))['openai']

    def update(self):
        self.tts_config = yaml_parser.read_yaml_file(os.path.join("config", "api.yml"))['openai']

    async def post_text_to_speech(self, text) -> str | int:
        self.update()
        url = self.tts_config['urls']['tts']

        headers = {
            "Authorization": f"Bearer {self.openai_token}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.tts_config['tts-model'],
            "input": text,
            "voice": self.tts_config['voice'],
        }

        if not os.path.exists('temp'):
            os.mkdir('temp')

        temp_path = os.path.join('temp', str(uuid.uuid1()) + '.mp3')

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self.tts_config['timeout'])) as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status not in self.tts_config['success_codes']:
                        logger.error(response.content)
                        try:
                            logger.error(await response.json())
                        except Exception:
                            pass
                        try:
                            logger.error(await response.read())
                        except Exception:
                            pass
                        return response.status

                    with open(temp_path, "wb") as f:
                        f.write(await response.read())
                    return temp_path
        except TimeoutError:
            return -1
