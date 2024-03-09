from aiogram import types, Bot

from engine.course import Course
from engine.start import Start
from logging_engine import get_logger
from pydantic_models.users import User


logger = get_logger()


class Callback(Start):
    def __init__(self, callback_query: types.CallbackQuery, user: User, bot: Bot):
        Start.__init__(self, bot, user)
        logger.info(f'[cyan]Got callback with data [green]{callback_query.data}')
        self.callback_query = callback_query
        self.user = user
        self.bot = bot

    async def process(self):
        query = self.callback_query.data

        button_name = None
        for row in self.callback_query.message.reply_markup.inline_keyboard:
            for button in row:
                if button.callback_data == self.callback_query.data:
                    button_name = button.text

        if query == 'start':
            await self.start(self.callback_query.message)

        if query.startswith('CRS_'):
            course_name = query.removeprefix('CRS_')
            course = Course(course_name, self.user, self.bot)
            try:
                await course.welcome(self.callback_query.message)
            except KeyError:
                logger.exception(f'Unable to find course with name {course_name}')
                await self.callback_query.message.reply(f'Не удалось найти этот курс. Обратитесь к администратору!\nТехническое имя курса: {course_name}')

        if query.startswith('CONT_'):
            phrase_data = query.removeprefix('CONT_').split('_')
            course_name = phrase_data[0]
            phrase_index = int(phrase_data[1])

            course = Course(course_name, self.user, self.bot)
            await course.continue_welcome(self.callback_query.message, phrase_index)
            try:
                await self.callback_query.message.edit_reply_markup()
            except Exception:
                pass

        if query.startswith('FINB_'):
            phrase_data = query.removeprefix('FINB_').split('_')
            course_name = phrase_data[0]
            button_index = int(phrase_data[1])

            course = Course(course_name, self.user, self.bot)
            await course.process_final_button(self.callback_query.message, button_index)

        if query.startswith('PURCHASE_'):
            purchase_data = query.removeprefix('PURCHASE_').split('_')
            course_name = purchase_data[0]

            course = Course(course_name, self.user, self.bot)
            await course.process_purchase(self.callback_query.message)

        if query == 'RESTART':
            msg = self.callback_query.message
            try:
                await msg.edit_reply_markup()
            except Exception:
                pass

            cmd = Start(self.bot, self.user)
            await cmd.welcome(self.callback_query.message)
            return

        if query.startswith('CHECK_'):
            purchase_data = query.removeprefix('CHECK_').split('_')
            invoice_id = purchase_data[0]

            course = Course(None, self.user, self.bot)
            await course.check_payment(self.callback_query.message, int(invoice_id))

        if query.startswith('START_'):
            course_data = query.removeprefix('START_').split('_')
            course_name = course_data[0]
            try:
                block_id = course_data[1]
            except IndexError:
                block_id = None

            course = Course(course_name, self.user, self.bot)
            await course.show_main(self.callback_query.message, block_id)

        if query.startswith('READB_'):
            block_data = query.removeprefix('READB_').split('_')
            course_name = block_data[0]
            block_id = int(block_data[1])

            course = Course(course_name, self.user, self.bot)

            mes = self.callback_query.message
            await mes.edit_text(mes.text + '\n<b>' + button_name + '</b>', reply_markup=mes.reply_markup)
            await course.read(self.callback_query.message, block_id, 1)

        if query.startswith('READ_'):
            block_data = query.removeprefix('READ_').split('_')
            course_name = block_data[0]
            block_id = int(block_data[1])
            step_id = int(block_data[2])

            course = Course(course_name, self.user, self.bot)
            await course.read(self.callback_query.message, block_id, step_id)

        await self.bot.answer_callback_query(self.callback_query.id)

