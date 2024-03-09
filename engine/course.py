import os
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import enums
from database.invoices import InvoiceManagement
from engine.video import VideoHelper
from logging_engine import get_logger
from pydantic_models.invoices import InvoiceForm
from pydantic_models.user_courses import UserCourseForm
from pydantic_models.users import User
from tools.yaml_parser import read_yaml_file
from database.user_courses import UserCoursesManagement

logger = get_logger()


class Course:
    def __init__(self, course_name, user: User, bot: Bot):
        self.bot = bot
        self.user = user
        self.messages_config: dict = read_yaml_file(os.path.join('config', 'messages.yml'))
        self.courses_config: dict = read_yaml_file(os.path.join('config', 'courses.yml'))
        if course_name:
            self.course_data = self.courses_config['courses'][course_name]
        self.course_name = course_name

    async def welcome(self, msg: Message):
        # Get first phrase
        data = list(self.course_data['welcome'][0].values())[0]

        user_courses = await UserCoursesManagement.get(id=self.user.id, by=enums.GetByEnum.USER_ID)
        if self.course_name in [i.course_name for i in user_courses]:
            return await self.show_main(msg)

        if data['last']:
            buttons = []
            for name, data in self.course_data['final_buttons'].items():
                if data['type'] == 'text':
                    buttons.append([InlineKeyboardButton(
                        text=data['name'],
                        callback_data=f"FINB_{self.course_name}_{name}")])
                if data['type'] == 'payment':
                    buttons.append([InlineKeyboardButton(
                        text=self.messages_config['buy_course_button'],
                        callback_data=f"FINB_{self.course_name}_{name}")])
        else:
            buttons = [[InlineKeyboardButton(
                text=data['continue_button_text'],
                callback_data=f"CONT_{self.course_name}_1")]]

        inline = InlineKeyboardMarkup(inline_keyboard=buttons)

        if data.get('video') is not None:
            await VideoHelper.send_video(msg.chat.id, video_name=data['video']['filename'],
                                         caption=data['video']['caption'], bot=self.bot, reply_to=msg.message_id)
        await self.bot.send_message(msg.chat.id, data['text'], reply_markup=inline)

    async def continue_welcome(self, msg: Message, phrase_index: int):
        data = self.course_data['welcome'][phrase_index]
        data = list(data.values())[0]
        if data['last']:
            buttons = []
            for button_index, button in enumerate(self.course_data['final_buttons']):
                button_name = list(button.keys())[0]
                button_data = button[button_name]
                if button_data['type'] == 'text':
                    buttons.append([InlineKeyboardButton(
                        text=button_data['name'],
                        callback_data=f"FINB_{self.course_name}_{button_index}")])
                if button_data['type'] == 'payment':
                    user_courses = await UserCoursesManagement.get(id=self.user.id, by=enums.GetByEnum.USER_ID)
                    if self.course_name not in [i.course_name for i in user_courses]:
                        buttons.append([InlineKeyboardButton(
                            text=button_data['name'],
                            callback_data=f"FINB_{self.course_name}_{button_index}")])
                    else:
                        buttons.append([InlineKeyboardButton(
                            text=button_data['payed_alt'],
                            callback_data=f"FINB_{self.course_name}_{button_index}")])

        else:
            buttons = [[InlineKeyboardButton(
                text=data['continue_button_text'],
                callback_data=f"CONT_{self.course_name}_{phrase_index + 1}")]]

        inline = InlineKeyboardMarkup(inline_keyboard=buttons)

        if data.get('video') is not None:
            await VideoHelper.send_video(msg.chat.id, video_name=data['video']['filename'],
                                         caption=data['video'].get('caption'), bot=self.bot, reply_to=msg.message_id)

        if data.get('photo') is not None:
            await VideoHelper.send_photo(msg.chat.id, photo_name=data['photo']['filename'],
                                         caption=data['video'].get('caption'), bot=self.bot, reply_to=msg.message_id)

        if data.get('document') is not None:
            await VideoHelper.send_document(msg.chat.id, data['photo']['filename'],
                                            caption=data['video'].get('caption'), bot=self.bot, reply_to=msg.message_id)
        await self.bot.send_message(msg.chat.id, data['text'], reply_markup=inline)

    async def process_final_button(self, msg: Message, button_index: int):
        button = self.course_data['final_buttons'][button_index]
        button = list(button.values())[0]

        if button['type'] == 'text':
            return await msg.reply(button['text'], parse_mode='HTML')
        if button['type'] == 'payment':
            user_courses = await UserCoursesManagement.get(id=self.user.id, by=enums.GetByEnum.USER_ID)
            if self.course_name in [i.course_name for i in user_courses]:
                return await self.show_main(msg)  # Start course if user owns it

            buttons = [
                [InlineKeyboardButton(
                    text=self.messages_config['buy_course_button'],
                    callback_data=f"PURCHASE_{self.course_name}_NORMAL")],
                [InlineKeyboardButton(
                    text=self.messages_config['buy_course_russia_button'],
                    callback_data=f"PURCHASE_{self.course_name}_RUSSIA")]
            ]
            inline = InlineKeyboardMarkup(inline_keyboard=buttons)
            return await msg.reply(self.messages_config['buy_course_text'], reply_markup=inline, parse_mode='HTML')

    async def process_purchase(self, msg: Message):
        internal_invoice_id = 'Dummy'  # TODO: Create invoice via Robokassa
        invoice = await InvoiceManagement.create(InvoiceForm(user_id=self.user.id,
                                                             invoice_id=internal_invoice_id,
                                                             course_name=self.course_name))
        await msg.edit_reply_markup()
        buttons = [
            [InlineKeyboardButton(
                text=self.messages_config['check_invoice_button'],
                callback_data=f"CHECK_{invoice.id}")]
        ]

        inline = InlineKeyboardMarkup(inline_keyboard=buttons)

        return await msg.reply(self.messages_config['invoice_created_text'], parse_mode='HTML', reply_markup=inline)

    async def check_payment(self, msg: Message, invoice_internal_id: int):
        invoice = await InvoiceManagement.get(id=invoice_internal_id)
        if not invoice:
            return await msg.reply(self.messages_config['unknown_invoice'])

        status = enums.InvoiceInternalStatusEnum.SUCCESS  # TODO: Check invoice status
        if status == enums.InvoiceInternalStatusEnum.EXPIRED:
            return await msg.reply(self.messages_config['expired_invoice'])
        if status == enums.InvoiceInternalStatusEnum.CREATED:
            return await msg.reply(self.messages_config['created_invoice'])
        if status == enums.InvoiceInternalStatusEnum.SUCCESS:
            await UserCoursesManagement.create(UserCourseForm(user_id=self.user.id,
                                                              course_name=invoice.course_name))
            await InvoiceManagement.delete(invoice.id)
            await msg.edit_reply_markup()

            buttons = [
                [InlineKeyboardButton(
                    text=self.messages_config['start_course_button'],
                    callback_data=f"START_{invoice.course_name}")]
            ]

            inline = InlineKeyboardMarkup(inline_keyboard=buttons)
            return await msg.reply(self.messages_config['success_invoice'], reply_markup=inline)
        else:
            return await msg.reply(f'Неизвестный статус оплаты. Свяжитесь с администратором\n{status}')

    async def show_main(self, msg: Message, last_block_id: int = None):
        logic_file_path = self.courses_config['courses'][self.course_name]['logic_file_name']
        logic: dict = read_yaml_file(os.path.join('config', 'courses', logic_file_path))

        buttons = []

        for item in logic['blocks']:
            data = logic['blocks'][item]

            text = data['display_name']
            if str(last_block_id) == str(item):
                text += ' ✅'
                try:
                    await msg.edit_reply_markup()
                except Exception:
                    pass

            buttons.append([
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"READB_{self.course_name}_{item}")
            ])

        inline = InlineKeyboardMarkup(inline_keyboard=buttons)
        await msg.reply(self.messages_config['select_block'], reply_markup=inline)

    async def read(self, msg: Message, block_number: int, step_number: int, remove_buttons: bool = True):
        logic_file_path = self.courses_config['courses'][self.course_name]['logic_file_name']

        logic: dict = read_yaml_file(os.path.join('config', 'courses', logic_file_path))['blocks']
        data = logic[block_number]['steps'][step_number]

        callback_data = f"READ_{self.course_name}_{block_number}_{step_number + 1}"
        back_callback_data = f"READ_{self.course_name}_{block_number}_{step_number - 1}"
        if data.get('block_last') is True:
            callback_data = f"START_{self.course_name}_{block_number}"
        if data.get('last') is True:
            callback_data = "RESTART"

        buttons = [[
            InlineKeyboardButton(
                text=data['continue_text'],
                callback_data=callback_data)
        ],
            [InlineKeyboardButton(
                text=self.messages_config['back_button'],
                callback_data=back_callback_data)
            ]]

        if step_number <= 1 or self.courses_config['courses'][self.course_name]['enable_back_button'] is False:
            del buttons[-1]

        inline = InlineKeyboardMarkup(inline_keyboard=buttons)

        reply_to = None
        media_inline = inline

        if data.get('text'):
            if not data.get('video') and not data.get('document') and not data.get('photo'):
                rep = inline
            else:
                rep = None
                media_inline = inline
            reply_to = await msg.reply(data['text'], reply_markup=rep, protect_content=data['protect'])
            reply_to = reply_to.message_id

        video_inline = None
        photo_inline = None
        document_inline = None
        if media_inline:
            if data.get('document'):
                document_inline = inline
            elif data.get('photo'):
                photo_inline = inline
            elif data.get('video'):
                video_inline = inline

        if data.get('video'):
            await VideoHelper.send_video(msg.chat.id, data['video']['filename'], data['video'].get('caption'),
                                         self.bot, reply_to=reply_to, reply_markup=video_inline,
                                         protect_content=data['protect'])

        if data.get('photo'):
            await VideoHelper.send_photo(msg.chat.id, data['photo']['filename'], data['photo'].get('caption'),
                                         self.bot, reply_to=reply_to, reply_markup=photo_inline,
                                         protect_content=data['protect'])

        if data.get('document'):
            await VideoHelper.send_document(msg.chat.id, data['document']['filename'], data['document'].get('caption'),
                                            self.bot, reply_to=reply_to, reply_markup=document_inline,
                                            protect_content=data['protect'])

        if remove_buttons:
            try:
                await msg.edit_reply_markup()
            except Exception:
                pass
