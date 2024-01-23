from typing import Optional

from pydantic import BaseModel
import enums
from datetime import datetime


class Conversation(BaseModel):
    id: int
    user_id: int
    text: str
    role: enums.SpeakerRoleEnum
    created_at: datetime
    closed: Optional[bool] = False


class ConversationHistory(BaseModel):
    message: str
    role: str


class ConversationForm(BaseModel):
    user_id: int
    text: str
    role: enums.SpeakerRoleEnum
