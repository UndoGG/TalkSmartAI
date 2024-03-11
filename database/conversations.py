from typing import List
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
    async def edit(conversation_id: int, **kwargs) -> None:
        conversation = await ConversationsModel.get_or_none(id=conversation_id)
        if not conversation:
            return
        return await conversation.update_from_dict(kwargs).save()

    @staticmethod
    async def get(id: int, by: enums.GetByEnum = enums.GetByEnum.ID, create_conversation: ConversationForm = False, include_closed=False) -> List[Conversation]:
        conversations = []
        if by == enums.GetByEnum.TELEGRAM_ID:
            raise TypeError('Telegram id conversation search is not supported')
        if by == enums.GetByEnum.ID:
            conversations = await ConversationsModel.filter(id=id)
        if by == enums.GetByEnum.USER_ID:
            conversations = await ConversationsModel.filter(user_id=id)

        if not include_closed:
            conversations = [conv for conv in conversations if conv.closed is False]

        if not conversations and create_conversation:
            return tortoise_to_pydantic(await ConversationManagement.create(create_conversation), Conversation)

        return [tortoise_to_pydantic(conv, Conversation) for conv in conversations]

    @staticmethod
    async def delete(conv_id: int):
        conv = await ConversationsModel.get_or_none(id=conv_id)
        if not conv:
            return

        await conv.delete()
