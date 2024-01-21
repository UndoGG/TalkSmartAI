import enums
from database.serializer import tortoise_to_pydantic
from logging_engine import get_logger
from enums import *
from models.promises import PromisesModel
from pydantic_models.promises import PromiseForm, Promise

logger = get_logger()


class PromiseManagement:
    @staticmethod
    async def create(promise: PromiseForm):
        promises = await PromisesModel.filter()
        for _promise in promises:
            await _promise.delete()
        return await PromisesModel.create(**promise.model_dump())

    @staticmethod
    async def get(id: int, by: enums.GetByEnum = enums.GetByEnum.ID, create_promise: PromiseForm = False) -> Promise | None:
        if by == enums.GetByEnum.TELEGRAM_ID:
            raise TypeError('Promises telegram id search is not supported')

        promise = []
        if by == enums.GetByEnum.USER_ID:
            promise = await PromisesModel.filter(user_id=id)
        if by == enums.GetByEnum.ID:
            promise = await PromisesModel.filter(id=id)

        if len(promise) == 0:
            if create_promise:
                return tortoise_to_pydantic(await PromiseManagement.create(create_promise), Promise)
            return
        if len(promise) > 0:
            return tortoise_to_pydantic(promise[0], Promise)

    @staticmethod
    async def delete(promise_id: int):
        promise = await PromisesModel.get_or_none(id=promise_id)
        if not promise:
            return
        await promise.delete()
