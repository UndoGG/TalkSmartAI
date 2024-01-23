from enum import Enum


class AccessEnum(Enum):
    USER = 'Normal User'
    ADMIN = 'Administrator'


class ConfigTypeEnum(Enum):
    TELEGRAM = 'Telegram'


class PromiseTypeEnum(Enum):
    PROVIDE_TOPIC = 'Provide topic'
    PROVIDE_OPINION = 'Provide opinion'


class SpeakerRoleEnum(Enum):
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'


class GetByEnum(Enum):
    ID = 'ID'
    TELEGRAM_ID = 'TELEGRAM_ID'
    USER_ID = 'USER_ID'
