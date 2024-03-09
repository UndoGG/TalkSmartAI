import asyncio
import logging
import os
from tortoise import Tortoise
import logging_engine
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from tools import yaml_parser
from hooks import router
from dotenv import load_dotenv


config = yaml_parser.read_yaml_file(os.path.join("config", "bot.yml"))
logger = logging_engine.start_logger(config['log_level']['global'])

logger.info("[bold cyan]Starting up...")

load_dotenv()
TOKEN = os.environ.get('TELEGRAM_TOKEN')
logger.debug("[cyan]Loaded dotenv")

logging.getLogger('tortoise').setLevel(logging.WARN)
logging.getLogger('tortoise').setLevel(logging.WARN)
logging.getLogger('aiosqlite').setLevel(logging.WARN)
logging.getLogger('aiohttp').setLevel(logging.INFO)
logging.getLogger('requests').setLevel(logging.INFO)
logging.getLogger('hpack').setLevel(logging.INFO)
logging.getLogger('httpcore').setLevel(logging.INFO)
logging.getLogger('httpx').setLevel(logging.INFO)
logging.getLogger('concurrent').setLevel(logging.INFO)
logging.getLogger('httpcore').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger('aiogram').setLevel(eval("logging." + config['log_level']['aiogram']))


# all_loggers = logging.Logger.manager.loggerDict.keys()
# print("Список логгеров:", list(all_loggers))


async def main():
    await Tortoise.init(config_file='tortoise_config.json')
    await Tortoise.generate_schemas()

    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


asyncio.run(main())
