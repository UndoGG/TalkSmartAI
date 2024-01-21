from datetime import datetime
from tortoise.models import Model
from tortoise import fields
import enums


class UsersModel(Model):
    id: int = fields.BigIntField(pk=True)
    telegram_id: int = fields.BigIntField()
    access: enums.AccessEnum = fields.CharEnumField(enums.AccessEnum)
    created_at: datetime = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = 'users'

