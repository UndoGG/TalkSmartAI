import os

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from fastapi import APIRouter, Request

import enums
from database.invoices import InvoiceManagement
from database.user_courses import UserCoursesManagement
from database.users import UserManagement
from engine.payment.main import PaymentEngine
from enums import GetByEnum
from logging_engine import get_logger
from pydantic_models.system.payment import PaymentAuth
from pydantic_models.user_courses import UserCourseForm

main_router = APIRouter(tags=["Ratings"])
logger = get_logger()
load_dotenv()
bot = Bot(token=os.environ.get('TELEGRAM_TOKEN'), default=DefaultBotProperties(parse_mode='HTML'))


@main_router.post('/')
async def main(request: Request):
    raw_payload = (await request.body()).decode()

    payload = {}
    for item in raw_payload.split('&'):
        if len(item.split('=')) < 2:
            logger.warning(f'[bold yellow]Skipped {item} item payload parsing, cause no value provided')
            continue

        param = item.split('=')[0]
        value = item.split('=')[1]
        payload[param] = value

    logger.info(f'[bold green]Received payment payload: {payload}')

    engine = PaymentEngine(auth=PaymentAuth(
        merchant_login=os.environ.get('ROBOKASSA_MERCHANT_LOGIN'),
        merchant_password_1=os.environ.get('ROBOKASSA_MERCHANT_PASSWORD_1'),
        merchant_password_2=os.environ.get('ROBOKASSA_MERCHANT_PASSWORD_2'),
    ))

    try:
        check_result = engine.result_payment(payload)
        status = check_result[0]
        success = check_result[1]
    except Exception:
        logger.exception('[bold red]Unable to check signature')
        return 'sign check error'

    invoice = await InvoiceManagement.get(id=str(payload['inv_id']), by=GetByEnum.VALUE)
    if not invoice:
        await InvoiceManagement.edit(invoice.id, status=enums.InvoiceInternalStatusEnum.FAILED)
        logger.error('[bold red]Unknown invoice!')
        return 'Invoice not found in internal database'
    user = await UserManagement.get(id=invoice.user_id)

    buttons = [
        [InlineKeyboardButton(
            text='В меню',
            callback_data='start')]
    ]

    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    if success:

        await InvoiceManagement.edit(invoice.id, status=enums.InvoiceInternalStatusEnum.SUCCESS)
        await bot.send_message(user.telegram_id, f'Спасибо за покупку! Курс выдан на ваш аккаунт!\n<i>ID Чека: {invoice.id}</i>', parse_mode='HTML', reply_markup=markup)

        await UserCoursesManagement.create(UserCourseForm(user_id=user.id,
                                                          course_name=invoice.course_name))
    else:
        logger.error('[bold red]Signature failed')
        await bot.send_message(user.telegram_id,
                               f'Нам не удалось выдать вам курс из-за неверной подписи. Свяжитесь с поддержкой\n<i>ID Чека: {invoice.id}</i>', parse_mode='HTML', reply_markup=markup)

    return status
