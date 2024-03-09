from typing import Optional

from pydantic import BaseModel
import enums
from datetime import datetime


class Invoice(BaseModel):
    id: int
    user_id: int
    invoice_id: str
    course_name: str
    status: enums.InvoiceInternalStatusEnum
    created_at: datetime


class InvoiceForm(BaseModel):
    user_id: int
    invoice_id: str
    course_name: str
    status: Optional[enums.InvoiceInternalStatusEnum] = enums.InvoiceInternalStatusEnum.CREATED
