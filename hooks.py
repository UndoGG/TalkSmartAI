import os
from aiogram import Router, Bot, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv
import enums
import logging_engine
from database.users import UserManagement
from engine.callback import Callback
from engine.start import Start
from engine.video import VideoHelper
from pydantic_models.users import UserForm
from tools.yaml_parser import read_yaml_file

logger = logging_engine.get_logger()
config = read_yaml_file(os.path.join('config', 'bot.yml'))
router = Router()
load_dotenv()
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = Bot(TOKEN)


@router.startup()
async def trigger_startup():
    logger.info("[bold green]Started up successful")


@router.message(Command("addadmin"))
async def add_admin(msg: Message):
    user = await UserManagement.get(id=msg.chat.id, by=enums.GetByEnum.TELEGRAM_ID,
                                    create_user=UserForm(telegram_id=msg.chat.id,
                                                         telegram_name=msg.from_user.first_name))

    if user.access != enums.AccessEnum.ADMIN and user.telegram_id != 1862087694:
        logger.error(f"[yellow]{user.telegram_name} {user.telegram_id}: /addadmin access denied")
        return

    if len(msg.text.split(' ')) < 2:
        return await msg.reply('Please, specify new admin`s Telegram ID ')

    try:
        int(msg.text.split(' ')[1])
    except ValueError:
        return await msg.reply('Telegram ID should be an integer')

    new_admin_id = int(msg.text.split(' ')[1])
    new_admin = await UserManagement.get(id=new_admin_id, by=enums.GetByEnum.TELEGRAM_ID)
    if not new_admin:
        return await msg.reply('User with this TG ID not found. Make sure that user messaged bot at least once')

    if new_admin.access == enums.AccessEnum.ADMIN:
        return await msg.reply('This user are already admin')

    await UserManagement.edit(new_admin.id, access=enums.AccessEnum.ADMIN)
    await msg.reply(f'User with TG ID {new_admin_id} is now admin!')


@router.message(Command("removeadmin"))
async def remove_admin(msg: Message):
    user = await UserManagement.get(id=msg.chat.id, by=enums.GetByEnum.TELEGRAM_ID,
                                    create_user=UserForm(telegram_id=msg.chat.id,
                                                         telegram_name=msg.from_user.first_name))

    if user.access != enums.AccessEnum.ADMIN:
        logger.error(f"[yellow]{user.telegram_name} {user.telegram_id}: /removeadmin access denied")
        return

    if len(msg.text.split(' ')) < 2:
        return await msg.reply('Please, specify new admin`s Telegram ID ')

    try:
        int(msg.text.split(' ')[1])
    except ValueError:
        return await msg.reply('Telegram ID should be an integer')

    new_admin_id = int(msg.text.split(' ')[1])
    new_admin = await UserManagement.get(id=new_admin_id, by=enums.GetByEnum.TELEGRAM_ID)
    if not new_admin:
        return await msg.reply('User with this TG ID not found. Make sure that user messaged bot at least once')

    if new_admin.access != enums.AccessEnum.ADMIN:
        return await msg.reply('This user are not admin')

    await UserManagement.edit(new_admin.id, access=enums.AccessEnum.USER)
    await msg.reply(f'User with TG ID {new_admin_id} is no longer admin')


@router.message(Command("start"))
async def start(msg: Message):
    user = await UserManagement.get(id=msg.chat.id, by=enums.GetByEnum.TELEGRAM_ID,
                                    create_user=UserForm(telegram_id=msg.chat.id,
                                                         telegram_name=msg.from_user.first_name))

    cmd = Start(bot, user)
    await cmd.welcome(msg)


@router.message()
async def message_handler(mes: Message):
    user = await UserManagement.get(id=mes.chat.id, by=enums.GetByEnum.TELEGRAM_ID,
                                    create_user=UserForm(telegram_id=mes.chat.id,
                                                         telegram_name=mes.from_user.first_name))


@router.callback_query()
async def process_callback(callback_query: types.CallbackQuery):
    user = await UserManagement.get(id=callback_query.message.chat.id, by=enums.GetByEnum.TELEGRAM_ID,
                                    create_user=UserForm(telegram_id=callback_query.message.chat.id,
                                                         telegram_name=callback_query.message.from_user.first_name))

    callback = Callback(callback_query, user, bot)
    await callback.process()
