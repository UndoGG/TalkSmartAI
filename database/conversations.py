import enums
from database.serializer import tortoise_to_pydantic
from logging_engine import get_logger
from models.conversations import ConversationsModel
from pydantic_models.conversations import ConversationForm, Conversation

logger = get_logger()


class ConversationManagement:
    @staticmethod
    async def create(conversation: ConversationForm):
        return await ConversationsModel.create(**conversation.model_dump())

    @staticmethod
    async def get(id: int, by: enums.GetByEnum = enums.GetByEnum.ID, create_conversation: ConversationForm = False) -> Conversation | None:
        conversation = None
        if by == enums.GetByEnum.TELEGRAM_ID:
            raise TypeError('Telegram id conversation search is not supported')
        if by == enums.GetByEnum.ID:
            conversation = await ConversationsModel.get_or_none(id=id)
        if by == enums.GetByEnum.USER_ID:
            conversation = await ConversationsModel.get_or_none(user_id=id)
        if not conversation:
            if create_conversation:
                return tortoise_to_pydantic(await ConversationManagement.create(create_conversation), Conversation)
            return
        return tortoise_to_pydantic(conversation, Conversation)
