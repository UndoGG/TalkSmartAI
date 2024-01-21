import asyncio
import json
import os
import aiohttp
from dotenv import load_dotenv
import logging_engine
from tools import yaml_parser


api_config = yaml_parser.read_yaml_file(os.path.join("config", "api.yml"))
logger = logging_engine.get_logger()

load_dotenv()


class ChatGPTAPI:
    def __init__(self):
        self.token = os.environ['CHAT_GPT_TOKEN']
        self.gpt_config = yaml_parser.read_yaml_file(os.path.join("config", "api.yml"))['chat_gpt']

    async def post_ask(self, prompt: str):
        url = self.gpt_config['urls']['ask']
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        payload = {"model": self.gpt_config['model'],
                   "messages": [
                       {
                           "role": "user",
                           "content": prompt
                       }
                   ]}

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(900)) as session:
            async with session.post(url, data=json.dumps(payload), headers=headers) as response:
                if response.status not in self.gpt_config['success_codes']:
                    logger.error(response.content)
                    return response.status

                await session.close()
                return await response.json()


# async def main():
#     api = ChatGPTAPI()
#     print(await api.post_ask('Hi!'))
#
# asyncio.run(main())
