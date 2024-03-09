from tortoise import fields
from tortoise.models import Model


class UserCoursesModel(Model):
    id: int = fields.BigIntField(pk=True)
    user = fields.ForeignKeyField('models.UsersModel')
    course_name = fields.TextField()

    class Meta:
        table = 'user_courses'

