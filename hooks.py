import os
<<<<<<< Updated upstream
from aiogram import Router, Bot, types
from aiogram.filters import Command
from aiogram.types import Message
=======
import shutil
from typing import List

from aiogram import Router, Bot, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile
>>>>>>> Stashed changes
from dotenv import load_dotenv
import enums
<<<<<<< Updated upstream
=======
from database.conversations import ConversationManagement
from database.promises import PromiseManagement
from engine.dialogue import Dialogue
from engine.dump import Dumper
from engine.start import Start
>>>>>>> Stashed changes
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


<<<<<<< Updated upstream
@router.message(Command("start"))
async def start(msg: Message):
    user = await UserManagement.get(id=msg.chat.id, by=enums.GetByEnum.TELEGRAM_ID,
                                    create_user=UserForm(telegram_id=msg.chat.id,
                                                         telegram_name=msg.from_user.first_name))

=======
@router.message(Command("dump"))
async def dump(msg: Message):
    user = await UserManagement.get(id=msg.chat.id, by=enums.GetByEnum.TELEGRAM_ID,
                                    create_user=UserForm(telegram_id=msg.chat.id,
                                                         telegram_name=msg.from_user.first_name))

    if user.access != enums.AccessEnum.ADMIN:
        logger.error(f"[yellow]{user.telegram_name} {user.telegram_id}: /dump access denied")
        return

    await msg.reply('In progress...')

    dumper = Dumper()
    try:
        zip_path = await dumper.dump_all()
    except Exception:
        logger.exception('[bold red]Unable to dump data!')
        return await msg.reply('Unable to create data dump. Please, contact with developer')

    zip_file = FSInputFile(zip_path[0])

    await bot.send_document(msg.chat.id, zip_file)

    os.remove(zip_path[0])
    shutil.rmtree(zip_path[1])


@router.message(Command("start"))
async def start(msg: Message):
    user = await UserManagement.get(id=msg.chat.id, by=enums.GetByEnum.TELEGRAM_ID,
                                    create_user=UserForm(telegram_id=msg.chat.id,
                                                         telegram_name=msg.from_user.first_name))
    cmd = Start(bot, user)
    await cmd.cleanup()
    await cmd.response_welcome(msg)


@router.message(Command("stop"))
async def stop(msg: Message):
    user = await UserManagement.get(id=msg.chat.id, by=enums.GetByEnum.TELEGRAM_ID,
                                    create_user=UserForm(telegram_id=msg.chat.id,
                                                         telegram_name=msg.from_user.first_name))
>>>>>>> Stashed changes
    cmd = Start(bot, user)
    await cmd.welcome(msg)


@router.message()
async def message_handler(mes: Message):
    user = await UserManagement.get(id=mes.chat.id, by=enums.GetByEnum.TELEGRAM_ID,
                                    create_user=UserForm(telegram_id=mes.chat.id,
                                                         telegram_name=mes.from_user.first_name))
<<<<<<< Updated upstream
=======
    promise = await PromiseManagement.get(id=user.id, by=enums.GetByEnum.USER_ID)
    conversation: List[Conversation] = await ConversationManagement.get(id=user.id, by=enums.GetByEnum.USER_ID)

    if mes.voice is not None and (len(conversation) > 0 or promise is not None):
        voice_client = VoiceEngine(user)
        voice_info = await bot.get_file(file_id=mes.voice.file_id)
        voice_download = await bot.download_file(voice_info.file_path)

        response = await voice_client.decode_voice(voice_download)
        if isinstance(response, int):
            if response == -1:
                await mes.reply('Voice transcription failed cause of Network failure!\n Please, try again!')
                return
            await mes.reply(
                f'Unable to transcript voice message. Server responded with status code: {response}.\nPlease, try again\nIf this issue continues, contact with developers')
            return
        try:
            TEXT = response['text']
        except KeyError:
            await mes.reply(
                'Unable to transcript message. Server responded with unserializable JSON. \nPlease, try again\nIf this issue continues, contact with developers')
            return
    else:
        TEXT = mes.text

    dialogue = Dialogue(bot, user)
    if TEXT is not None and TEXT.lower() == 'stop':
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
        # noinspection PyTypeChecker
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
                await mes.reply(config['messages']['provide_position'].format(mes.text))
                await PromiseManagement.create(PromiseForm(user_id=user.id,
                                                           type=enums.PromiseTypeEnum.PROVIDE_OPINION,
                                                           scenario_name=promise.scenario_name,
                                                           topic=TEXT))
            else:
                await dialogue.cleanup()
                # noinspection PyTypeChecker
                await dialogue.start_conversation(mes, scenario_data, TEXT)
        case enums.PromiseTypeEnum.PROVIDE_OPINION:
            if not mes.voice:
                if config['preferences']['allow_text'] is False:
                    return await mes.reply(config['messages']['voice_expected'])
                elif config['preferences']['warn_on_text'] is True:
                    await mes.reply(config['messages']['voice_expected_warning'])

            await dialogue.cleanup()
            await dialogue.start_conversation(mes, scenario_data, promise.topic, TEXT)
        case enums.PromiseTypeEnum.UPLOAD_FILE:
            if not mes.document:
                return
            if mes.document.mime_type not in config['preferences']['allowed_mime_types'] and "*" not in \
                    config['preferences']['allowed_mime_types']:
                return await mes.reply(config['messages']['unsupported_mimetype'].format(mes.document.mime_type))

            file_info = await bot.get_file(file_id=mes.document.file_id)
            file_download = await bot.download_file(file_info.file_path)

            try:
                file_text = file_download.read().decode()
            except UnicodeDecodeError:
                return await mes.reply(config['messages']['unable_to_decode'])

            await dialogue.cleanup()
            await dialogue.start_conversation(mes, scenario_data,
                                              topic=mes.document.file_name,
                                              addition=file_text,
                                              skip_rate=True)
>>>>>>> Stashed changes


@router.callback_query()
async def process_callback(callback_query: types.CallbackQuery):
    user = await UserManagement.get(id=callback_query.message.chat.id, by=enums.GetByEnum.TELEGRAM_ID,
                                    create_user=UserForm(telegram_id=callback_query.message.chat.id,
                                                         telegram_name=callback_query.message.from_user.first_name))

<<<<<<< Updated upstream
    callback = Callback(callback_query, user, bot)
    await callback.process()
=======
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
            await callback_query.message.reply(config['messages']['provide_position'].format(button_name))
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
            if scenario_data['file_mode']:
                await PromiseManagement.create(PromiseForm(user_id=user.id,
                                                           type=enums.PromiseTypeEnum.UPLOAD_FILE,
                                                           scenario_name=scenario))
                await callback_query.message.reply(config['messages']['provide_file'])
            else:
                await dialogue.ask_topic_provider(callback_query.message, scenario)
            await bot.answer_callback_query(callback_query.id)

    if callback_query.data.split('_')[0] == 'gen':
        if config['preferences']['show_generating_response_text'] is True:
            await callback_query.message.reply(config['messages']['generation_in_progress'])
        scenario = callback_query.data.split('_')[1]
        try:
            scenario_data = config['scenarios'][scenario]
        except KeyError:
            await callback_query.message.reply(
                f'Unable to find scenario with id: {scenario}. Please, contact with developer')
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
            MAX_MESSAGE_LENGTH = 2000

            text = conv[0].text
            while len(text) > 0:
                message = text[:MAX_MESSAGE_LENGTH]
                text = text[MAX_MESSAGE_LENGTH:]
                await callback_query.message.reply(message)
            await bot.answer_callback_query(callback_query.id)
>>>>>>> Stashed changes
