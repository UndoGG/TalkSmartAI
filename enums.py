from enum import Enum


class AccessEnum(Enum):
    USER = 'Normal User'
    ADMIN = 'Administrator'


class ConfigTypeEnum(Enum):
    TELEGRAM = 'Telegram'


class PromiseTypeEnum(Enum):
    PROVIDE_TOPIC = 'Provide topic'


class SpeakerRoleEnum(Enum):
    USER = 'User'
    ASSISTANT = 'Assistant'


class GetByEnum(Enum):
    ID = 'ID'
    TELEGRAM_ID = 'TELEGRAM_ID'
    USER_ID = 'USER_ID'
