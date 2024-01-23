import asyncio
import json
import os
from typing import List

import aiohttp
from dotenv import load_dotenv
import logging_engine
from pydantic_models.conversations import ConversationHistory
from tools import yaml_parser


api_config = yaml_parser.read_yaml_file(os.path.join("config", "api.yml"))
logger = logging_engine.get_logger()

load_dotenv()


class ChatGPTAPI:
    def __init__(self):
        self.gpt_token = os.environ['OPENAI_TOKEN']
        self.gpt_config = yaml_parser.read_yaml_file(os.path.join("config", "api.yml"))['openai']

    def update(self):
        self.gpt_config = yaml_parser.read_yaml_file(os.path.join("config", "api.yml"))['openai']

    # async def post_ask(self, prompt: str, history: List[ConversationHistory] = None):
    #     self.update()
    #
    #     if not history:
    #         history = []
    #
    #     url = self.gpt_config['urls']['ask']
    #     headers = {
    #         'Content-Type': 'application/json',
    #         'Authorization': f'Bearer {self.gpt_token}'
    #     }
    #
    #
    #
    #     history = [{"role": item.role, "content": item.message} for item in history]
    #
    #
    #     payload = {"model": self.gpt_config['model'],
    #                "messages": [
    #                    *history,
    #                    {
    #                        "role": "user",
    #                        "content": prompt
    #                    }
    #                ]}
    #
    #     try:
    #         async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self.gpt_config['timeout'])) as session:
    #             async with session.post(url, data=json.dumps(payload), headers=headers) as response:
    #                 if response.status not in self.gpt_config['success_codes']:
    #                     logger.error(response.content)
    #                     try:
    #                         logger.error(await response.json())
    #                     except Exception:
    #                         pass
    #                     return response.status
    #
    #                 await session.close()
    #                 return await response.json()
    #     except TimeoutError:
    #         return -1

    async def post_ask(self, prompt: str, history: List[ConversationHistory] = None):
        self.update()

        if not history:
            history = []

        url = self.gpt_config['urls']['gpt']
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.gpt_token}'
        }

        history = [{"role": item.role, "content": item.message} for item in history]


        payload = {"model": self.gpt_config['gpt-model'],
                   "messages": [
                       *history,
                       {
                           "role": "user",
                           "content": prompt
                       }
                   ]}

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self.gpt_config['timeout'])) as session:
                async with session.post(url, data=json.dumps(payload), headers=headers) as response:
                    if response.status not in self.gpt_config['success_codes']:
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

# async def main():
#     api = ChatGPTAPI()
#     print(await api.post_ask('Hi!'))
#
# asyncio.run(main())
