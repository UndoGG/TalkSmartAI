from typing import List

from pydantic import BaseModel


class MessagesConfig(BaseModel):
    welcome: List[str]


class TelegramConfig(BaseModel):
    messages: MessagesConfig
