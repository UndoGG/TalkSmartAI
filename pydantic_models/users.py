from typing import Optional

from pydantic import BaseModel
import enums
from datetime import datetime


class User(BaseModel):
    id: int
    telegram_id: int
    access: enums.AccessEnum
    created_at: datetime


class UserForm(BaseModel):
    telegram_id: int
    access: Optional[enums.AccessEnum] = enums.AccessEnum.USER
