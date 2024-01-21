from typing import Optional

from pydantic import BaseModel
import enums
from datetime import datetime


class Promise(BaseModel):
    id: int
    user_id: int
    type: enums.PromiseTypeEnum
    scenario_name: str


class PromiseForm(BaseModel):
    user_id: int
    type: enums.PromiseTypeEnum
    scenario_name: str
