import os
from typing import List

from aiogram import Router, Bot, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove
from dotenv import load_dotenv

import enums
from database.conversations import ConversationManagement
from database.promises import PromiseManagement
from engine.dialogue import Dialogue
from engine.start import Start
import logging_engine
from engine.voice import VoiceEngine
from pydantic_models.conversations import Conversation
from pydantic_models.promises import PromiseForm
from pydantic_models.users import UserForm
from tools.yaml_parser import read_yaml_file
from database.users import UserManagement

logger = logging_engine.get_logger()
config = read_yaml_file(os.path.join('config', 'logical.yml'))
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
    cmd = Start(bot, user)
    await cmd.cleanup()
    await cmd.response_welcome(msg)


@router.message(Command("stop"))
async def stop(msg: Message):
    user = await UserManagement.get(id=msg.chat.id, by=enums.GetByEnum.TELEGRAM_ID,
                                    create_user=UserForm(telegram_id=msg.chat.id))
    cmd = Start(bot, user)
    dialogue = Dialogue(bot, user)
    await msg.reply(config['messages']['context_cleaned'], reply_markup=ReplyKeyboardRemove())
    await dialogue.cleanup()
    await cmd.cleanup()
    await cmd.response_welcome(msg)


@router.message()
async def message_handler(mes: Message):
    user = await UserManagement.get(id=mes.chat.id, by=enums.GetByEnum.TELEGRAM_ID,
                                    create_user=UserForm(telegram_id=mes.chat.id))
    promise = await PromiseManagement.get(id=user.id, by=enums.GetByEnum.USER_ID)
    conversation: List[Conversation] = await ConversationManagement.get(id=user.id, by=enums.GetByEnum.USER_ID)

    if mes.voice is not None and conversation is not None:
        voice_client = VoiceEngine(user)
        voice_info = await bot.get_file(file_id=mes.voice.file_id)
        voice_download = await bot.download_file(voice_info.file_path)

        response = await voice_client.decode_voice(voice_download)
        if isinstance(response, int):
            if response == -1:
                await mes.reply('Voice transcription failed cause of Network failure!\n Please, try again!')
                return
            await mes.reply(f'Unable to transcript voice message. Server responded with status code: {response}.\nPlease, try again\nIf this issue continues, contact with developers')
            return
        try:
            TEXT = response['text']
        except KeyError:
            await mes.reply('Unable to transcript message. Server responded with unserializable JSON. \nPlease, try again\nIf this issue continues, contact with developers')
            return
    else:
        TEXT = mes.text

    dialogue = Dialogue(bot, user)

    if TEXT.lower() == 'stop':
        cmd = Start(bot, user)
        await mes.reply(config['messages']['context_cleaned'])
        await dialogue.cleanup()
        await cmd.cleanup()
        await cmd.response_welcome(mes)
        return

    if conversation and not promise:
        if not mes.voice:
            if config['preferences']['allow_text'] is False:
                return await mes.reply(config['messages']['voice_expected'])
            elif config['preferences']['warn_on_text'] is True:
                await mes.reply(config['messages']['voice_expected_warning'])
        return await dialogue.continue_conversation(mes, conversation, TEXT)

    if not promise:
        return
    await PromiseManagement.delete(promise.id)
    try:
        scenario_data = config['scenarios'][promise.scenario_name]
    except (KeyError, TypeError, ValueError):
        await mes.message.reply(
            f'Unable to find scenario with id: {promise.scenario_name}. Please, contact with developer')
        return

    match promise.type:
        case enums.PromiseTypeEnum.PROVIDE_TOPIC:
            if scenario_data['user_first'] is True:
                await mes.reply(config['messages']['provide_position'])
                await PromiseManagement.create(PromiseForm(user_id=user.id,
                                                           type=enums.PromiseTypeEnum.PROVIDE_OPINION,
                                                           scenario_name=promise.scenario_name,
                                                           topic=TEXT))
            else:
                if config['preferences']['show_generating_response_text'] is True:
                    await mes.reply(config['messages']['generation_in_progress'])
                await dialogue.cleanup()
                await dialogue.start_conversation(mes, scenario_data, TEXT)
        case enums.PromiseTypeEnum.PROVIDE_OPINION:
            if not mes.voice:
                if config['preferences']['allow_text'] is False:
                    return await mes.reply(config['messages']['voice_expected'])
                elif config['preferences']['warn_on_text'] is True:
                    await mes.reply(config['messages']['voice_expected_warning'])

            if config['preferences']['show_generating_response_text'] is True:
                await mes.reply(config['messages']['generation_in_progress'])
            await dialogue.cleanup()
            await dialogue.start_conversation(mes, scenario_data, promise.topic, TEXT)


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

    if config['preferences']['show_selected'] is True:
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
            await PromiseManagement.create(PromiseForm(user_id=user.id,
                                                       type=enums.PromiseTypeEnum.PROVIDE_OPINION,
                                                       scenario_name=scenario_name,
                                                       topic=button_name))
        else:
            await dialogue.cleanup()
            await dialogue.start_conversation(callback_query.message, scenario_data, button_name)
        await bot.answer_callback_query(callback_query.id)
        return

    for scenario in config['scenarios']:
        scenario_data = config['scenarios'][scenario]
        if scenario == callback_query.data:
            await dialogue.ask_topic_provider(callback_query.message, scenario)
            await bot.answer_callback_query(callback_query.id)

    if callback_query.data.split('_')[0] == 'gen':
        if config['preferences']['show_generating_response_text'] is True:
            await callback_query.message.reply(config['messages']['generation_in_progress'])
        scenario = callback_query.data.split('_')[1]
        try:
            scenario_data = config['scenarios'][scenario]
        except KeyError:
            await callback_query.message.reply(f'Unable to find scenario with id: {scenario}. Please, contact with developer')
            await bot.answer_callback_query(callback_query.id)
            return
        await dialogue.cleanup()
        await dialogue.response_scenario(scenario_data, callback_query.message, scenario)
        await bot.answer_callback_query(callback_query.id)

    if callback_query.data.split('_')[0] == 'pro':
        await PromiseManagement.create(PromiseForm(user_id=user.id,
                                                   type=enums.PromiseTypeEnum.PROVIDE_TOPIC,
                                                   scenario_name=callback_query.data.split('_')[1]))
        await callback_query.message.reply(config['messages']['provide_topic'])
        await bot.answer_callback_query(callback_query.id)
    if callback_query.data.split('_')[0] == 'trc':
        conv_id = callback_query.data.split('_')[1]
        conv = await ConversationManagement.get(id=int(conv_id))
        if conv:
            await callback_query.message.reply(conv[0].text)
            await bot.answer_callback_query(callback_query.id)
