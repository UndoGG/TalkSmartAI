from enum import Enum


class AccessEnum(Enum):
    USER = 'Normal User'
    ADMIN = 'Administrator'


<<<<<<< Updated upstream
=======
class ConfigTypeEnum(Enum):
    TELEGRAM = 'Telegram'


class PromiseTypeEnum(Enum):
    PROVIDE_TOPIC = 'Provide topic'
    PROVIDE_OPINION = 'Provide opinion'
    UPLOAD_FILE = 'Upload file'


class SpeakerRoleEnum(Enum):
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'
    RATE = 'rate'


>>>>>>> Stashed changes
class GetByEnum(Enum):
    ID = 'ID'
    TELEGRAM_ID = 'TELEGRAM_ID'
    USER_ID = 'USER_ID'
    VALUE = 'VALUE'


class InvoiceInternalStatusEnum(Enum):
    CREATED = 'Created'
    FAILED = 'Failed'
    SUCCESS = 'Success'
    EXPIRED = 'Expired'
