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


class ConversationForm(BaseModel):
    user_id: int
    text: str
    role: enums.SpeakerRoleEnum
