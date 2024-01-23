import asyncio
import json
import os

import aiofiles
import aiohttp
from dotenv import load_dotenv

from logging_engine import get_logger
from tools import yaml_parser

load_dotenv()


logger = get_logger()


class OpenAISSTAPI:
    def __init__(self):
        self.openai_token = os.environ['OPENAI_TOKEN']
        self.sst_config = yaml_parser.read_yaml_file(os.path.join("config", "api.yml"))['openai']

    def update(self):
        self.sst_config = yaml_parser.read_yaml_file(os.path.join("config", "api.yml"))['openai']

    async def post_speech_to_text(self, file_path) -> dict | int:
        self.update()
        url = self.sst_config['urls']['stt']
        headers = {
            "Authorization": f"Bearer {self.openai_token}",
        }

        data = aiohttp.FormData()
        data.add_field('model', 'whisper-1')
        data.add_field('file', open(file_path, 'rb'))
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self.sst_config['timeout'])) as session:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status not in self.sst_config['success_codes']:
                        logger.error(response.content)
                        try:
                            logger.error(await response.json())
                        except Exception:
                            pass
                        return response.status
                    await session.close()
                    return await response.json()
        except TimeoutError:
            return -1
