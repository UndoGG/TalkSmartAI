from datetime import datetime
from tortoise.models import Model
from tortoise import fields
import enums


class ConversationsModel(Model):
    id: int = fields.BigIntField(pk=True)
    user = fields.ForeignKeyField('models.UsersModel')
    text: str = fields.TextField()
    role: enums.SpeakerRoleEnum = fields.CharEnumField(enums.SpeakerRoleEnum)
    created_at: datetime = fields.DatetimeField(auto_now_add=True)
    closed: bool = fields.BooleanField(default=False)

    class Meta:
        table = 'conversations'

