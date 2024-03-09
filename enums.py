from enum import Enum


class AccessEnum(Enum):
    USER = 'Normal User'
    ADMIN = 'Administrator'


class GetByEnum(Enum):
    ID = 'ID'
    TELEGRAM_ID = 'TELEGRAM_ID'
    USER_ID = 'USER_ID'


class InvoiceInternalStatusEnum(Enum):
    CREATED = 'Created'
    SUCCESS = 'Success'
    EXPIRED = 'Expired'
