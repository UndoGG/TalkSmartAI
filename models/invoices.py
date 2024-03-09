from datetime import datetime
from tortoise.models import Model
from tortoise import fields
import enums


class InvoicesModel(Model):
    id: int = fields.BigIntField(pk=True)
    user = fields.ForeignKeyField('models.UsersModel')
    invoice_id = fields.TextField()
    course_name = fields.TextField()
    status = fields.CharEnumField(enums.InvoiceInternalStatusEnum)
    created_at: datetime = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = 'invoices'

