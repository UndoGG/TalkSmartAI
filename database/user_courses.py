from typing import List
from database.serializer import tortoise_to_pydantic
from enums import *
from logging_engine import get_logger
from models.user_courses import UserCoursesModel
from pydantic_models.user_courses import UserCourseForm, UserCourse

logger = get_logger()


class UserCoursesManagement:
    @staticmethod
    async def create(user_course: UserCourseForm) -> UserCoursesModel:
        return await UserCoursesModel.create(**user_course.model_dump())

    @staticmethod
    async def get(id: int, by: GetByEnum = GetByEnum.ID) -> List[UserCourse] | UserCourse | None:
        courses = []
        match by:
            case GetByEnum.ID:
                course = await UserCoursesModel.get_or_none(id=id)
                if course:
                    return tortoise_to_pydantic(course, UserCourse)
                else:
                    return None
            case GetByEnum.USER_ID:
                courses = await UserCoursesModel.filter(user_id=id)
                return [tortoise_to_pydantic(i, UserCourse) for i in courses]
            case GetByEnum.TELEGRAM_ID:
                raise TypeError('Telegram id search is not supported')
