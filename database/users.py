from models.users import UsersModel
from pydantic_models.users import UserForm, User
from database.serializer import tortoise_to_pydantic
from logging_engine import get_logger
from enums import *


logger = get_logger()


class UserManagement:
    @staticmethod
    async def create(user: UserForm) -> UsersModel:
        logger.debug(f'[cyan]Creating user with telegram id: {user.telegram_id}')
        return await UsersModel.create(**user.model_dump())

    @staticmethod
    async def edit(user_id: int, **kwargs) -> None:
        user = await UsersModel.get_or_none(id=user_id)
        if not user:
            return

        await user.update_from_dict(kwargs).save()

    @staticmethod
    async def get(id: int, by: GetByEnum = GetByEnum.ID, create_user: UserForm = False) -> User  | None:
        user = None
        if by in [GetByEnum.ID, GetByEnum.USER_ID]:
            user = await UsersModel.get_or_none(id=id)
        if by == GetByEnum.TELEGRAM_ID:
            user = await UsersModel.get_or_none(telegram_id=id)

        if not user:
            if create_user:
                return tortoise_to_pydantic(await UserManagement.create(create_user), User)
            return
        return tortoise_to_pydantic(user, User)
