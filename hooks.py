import os
from aiogram import Router, Bot, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

import enums
from database.promises import PromiseManagement
from engine.dialogue import Dialogue
from engine.start import Start
import logging_engine
from pydantic_models.promises import PromiseForm
from pydantic_models.users import UserForm
from tools.yaml_parser import read_yaml_file
from database.users import UserManagement

logger = logging_engine.get_logger()
config = read_yaml_file(os.path.join('config', 'telegram.yml'))
router = Router()
load_dotenv()
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = Bot(TOKEN)


@router.startup()
async def trigger_startup():
    logger.info("[bold green]Started up successful")


@router.message(Command("start"))
async def start(msg: Message):
    user = await UserManagement.get(id=msg.chat.id, by=enums.GetByEnum.TELEGRAM_ID, create_user=UserForm(telegram_id=msg.chat.id))
    await Start(bot).response_welcome(msg)


@router.message()
async def message_handler(mes: Message):
    user = await UserManagement.get(id=mes.chat.id, by=enums.GetByEnum.TELEGRAM_ID,
                                    create_user=UserForm(telegram_id=mes.chat.id))
    promise = await PromiseManagement.get(id=user.id, by=enums.GetByEnum.USER_ID)

    TEXT = mes.text  # CONVERT VOICE TO TEXT

    if not promise:
        print(404)
        return
    dialogue = Dialogue(bot, user)
    match promise.type:
        case enums.PromiseTypeEnum.PROVIDE_TOPIC:
            try:
                scenario_data = config['scenarios'][promise.scenario_name]
            except (KeyError, TypeError, ValueError):
                await mes.message.reply(
                    f'Unable to find scenario with id: {promise.scenario_name}. Please, contact with developer')
                return

            if scenario_data['user_first'] is True:
                await mes.reply(config['messages']['provide_position'])
            else:
                await mes.reply(config['messages']['topic_accepted'])
                await dialogue.start_conversation(mes, scenario_data, TEXT)
    await PromiseManagement.delete(promise.id)


@router.callback_query()
async def process_callback(callback_query: types.CallbackQuery):
    user = await UserManagement.get(id=callback_query.message.chat.id, by=enums.GetByEnum.TELEGRAM_ID,
                                    create_user=UserForm(telegram_id=callback_query.message.chat.id))

    scenario_name = None
    callback_index = None
    try:
        scenario_name = callback_query.data.split('_')[1]
        int(callback_query.data.split('_')[0])
        callback_index = int(callback_query.data.split('_')[0])
    except (ValueError, IndexError):
        pass
    dialogue = Dialogue(bot, user)
    button_name = None
    for row in callback_query.message.reply_markup.inline_keyboard:
        for button in row:
            if button.callback_data == callback_query.data:
                button_name = button.text

    await callback_query.message.reply(f'Selected {button_name}')

    if callback_index is not None:
        try:
            scenario_data = config['scenarios'][scenario_name]
        except (KeyError, TypeError, ValueError):
            await callback_query.message.reply(
                f'Unable to find scenario with id: {scenario_name}. Please, contact with developer')
            await bot.answer_callback_query(callback_query.id)
            return

        if scenario_data['user_first'] is True:
            await callback_query.message.reply(config['messages']['provide_position'])
        else:
            await dialogue.start_conversation(callback_query.message, scenario_data, button_name)
        await bot.answer_callback_query(callback_query.id)
        return

    for scenario in config['scenarios']:
        scenario_data = config['scenarios'][scenario]
        if scenario == callback_query.data:
            await dialogue.ask_topic_provider(callback_query.message, scenario)
            await bot.answer_callback_query(callback_query.id)

    if callback_query.data.split('_')[0] == 'gen':
        scenario = callback_query.data.split('_')[1]
        try:
            scenario_data = config['scenarios'][scenario]
        except KeyError:
            await callback_query.message.reply(f'Unable to find scenario with id: {scenario}. Please, contact with developer')
            await bot.answer_callback_query(callback_query.id)
            return
        await dialogue.response_scenario(scenario_data, callback_query.message, scenario)
        await bot.answer_callback_query(callback_query.id)

    if callback_query.data.split('_')[0] == 'pro':
        await PromiseManagement.create(PromiseForm(user_id=user.id,
                                                   type=enums.PromiseTypeEnum.PROVIDE_TOPIC,
                                                   scenario_name=callback_query.data.split('_')[1]))
        await callback_query.message.reply(config['messages']['provide_topic'])
        await bot.answer_callback_query(callback_query.id)
