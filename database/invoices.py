from typing import List

from database.serializer import tortoise_to_pydantic
from enums import *
from logging_engine import get_logger
from models.invoices import InvoicesModel
from pydantic_models.invoices import InvoiceForm, Invoice

logger = get_logger()


class InvoiceManagement:
    @staticmethod
    async def create(invoice: InvoiceForm) -> InvoicesModel:
        return await InvoicesModel.create(**invoice.model_dump())

    @staticmethod
    async def get_all() -> List[Invoice]:
        return [tortoise_to_pydantic(i, Invoice) for i in await InvoicesModel.all()]

    @staticmethod
    async def edit(invoice_id: int, **kwargs) -> None:
        invoice = await InvoicesModel.get_or_none(id=invoice_id)
        if not invoice:
            return

        await invoice.update_from_dict(kwargs).save()

    @staticmethod
    async def delete(invoice_id: int) -> None:
        invoice = await InvoicesModel.get_or_none(id=invoice_id)
        if not invoice:
            return

        await invoice.delete()

    @staticmethod
    async def get(id: int | str, by: GetByEnum = GetByEnum.ID) -> Invoice | None:
        invoice = None
        if by == GetByEnum.ID:
            invoice = await InvoicesModel.get_or_none(id=id)
        if by == GetByEnum.USER_ID:
            invoice = await InvoicesModel.get_or_none(user_id=id)
        if by == GetByEnum.VALUE:
            invoice = await InvoicesModel.get_or_none(invoice_id=id)
        if by == GetByEnum.TELEGRAM_ID:
            raise TypeError('Telegram id search is not supported')

        if not invoice:
            return

        return tortoise_to_pydantic(invoice, Invoice)
