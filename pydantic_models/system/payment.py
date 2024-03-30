from pydantic import BaseModel


class PaymentAuth(BaseModel):
    merchant_login: str
    merchant_password_1: str
    merchant_password_2: str
