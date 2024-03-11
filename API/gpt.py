import asyncio
import json
import os
from typing import List

import aiohttp
from dotenv import load_dotenv

import enums
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
        self.logical_config = yaml_parser.read_yaml_file(os.path.join("config", "logical.yml"))

    def update(self):
        self.gpt_config = yaml_parser.read_yaml_file(os.path.join("config", "api.yml"))['openai']

    async def post_ask(self, prompt: str, history: List[ConversationHistory] = None, skip_parse: bool = False):
        self.update()

        if not history:
            history = []

        url = self.gpt_config['urls']['gpt']
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.gpt_token}'
        }

        history = [{"role": item.role, "content": item.message} for item in history]
        new_history = []
        for item in history:
            if str(item['role']) != str(enums.SpeakerRoleEnum.RATE.value):
                new_history.append(item)
        history = new_history


        payload = {"model": self.gpt_config['gpt-model'],
                   "messages": [
                       *history,
                       {
                           "role": "user",
                           "content": prompt
                       }
                   ]}

        logger.debug(f'[green]Requesting GPT Generation with payload: [cyan]\n{payload}')

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self.gpt_config['gpt_timeout'] + len(prompt))) as session:
                async with session.post(url, data=json.dumps(payload), headers=headers) as response:
                    logger.debug('[green]Got GPT Response')
                    if response.status not in self.gpt_config['success_codes']:
                        try:
                            logger.error(response.content)
                        except Exception:
                            pass
                        try:
                            logger.error(await response.json())
                        except Exception:
                            pass
                        try:
                            logger.error(await response.read())
                        except Exception:
                            pass
                        return response.status

                    js = await response.json()

                    if not skip_parse:
                        new_content = ''
                        for letter in js['choices'][0]['message']['content']:
                            if letter in self.logical_config['system']['reserved_chars']:
                                new_content += '\\' + letter
                            else:
                                new_content += letter


                        js['choices'][0]['message']['content'] = new_content

                    return js
        except TimeoutError:
            return -1

# async def main():
#     api = ChatGPTAPI()
#     print(await api.post_ask('Hi!'))
#
# asyncio.run(main())
