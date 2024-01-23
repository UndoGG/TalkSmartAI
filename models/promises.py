from datetime import datetime
from tortoise.models import Model
from tortoise import fields
import enums


class PromisesModel(Model):
    id: int = fields.BigIntField(pk=True)
    user = fields.ForeignKeyField('models.UsersModel')
    type = fields.CharEnumField(enums.PromiseTypeEnum)
    scenario_name = fields.TextField()
    topic = fields.TextField(null=True)

    class Meta:
        table = 'promises'

