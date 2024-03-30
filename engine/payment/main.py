from dotenv import load_dotenv

from pydantic_models.system.payment import PaymentAuth
import decimal
import hashlib
import random
from urllib import parse
from urllib.parse import urlparse

# login = 'shakirafit'
# pass1 = 'mBU3D2o251TfgackvLBV'
# pass2 = 'guY5fa4EPDW2EKOy2UZ0'
# num = random.randint(1, 2147483647)


class PaymentEngine:
    def __init__(self, auth: PaymentAuth):
        self.auth = auth

    def calculate_signature(self, *args) -> str:
        """Create signature MD5.
        """
        # print(args)
        return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()

    def parse_response(self, request: str) -> dict:
        """
        :param request: Link.
        :return: Dictionary.
        """
        params = {}

        for item in urlparse(request).query.split('&'):
            key, value = item.split('=')
            params[key] = value
        return params

    def check_signature_result(
            self,
            order_number: int,
            received_sum: decimal,
            received_signature: hex,
    ) -> bool:
        signature = self.calculate_signature(received_sum, order_number, self.auth.merchant_password_2)
        if signature.lower() == received_signature.lower():
            return True
        return False

    def generate_payment_link(
            self,
            cost: decimal,
            description: str,
            is_test=0,
            robokassa_payment_url='https://auth.robokassa.ru/Merchant/Index.aspx',
    ) -> tuple[int, str]:
        """URL for redirection of the customer to the service.
        """

        number = random.randint(1, 2147483647)
        signature = self.calculate_signature(
            self.auth.merchant_login,
            cost,
            number,
            self.auth.merchant_password_1
        )

        data = {
            'MerchantLogin': self.auth.merchant_login,
            'OutSum': cost,
            'InvId': number,
            'Description': description,
            'SignatureValue': signature,
            'IsTest': is_test
        }

        return number, f'{robokassa_payment_url}?{parse.urlencode(data)}'

    def result_payment(self, request_parsed: dict) -> tuple[str, bool]:
        """Verification of notification (ResultURL).
        :param request_parsed: Parsed HTTP parameters.

        :returns Tuple of result and status in bool (Success = True)
        """
        cost = request_parsed['OutSum']
        number = request_parsed['InvId']
        signature = request_parsed['SignatureValue']

        if self.check_signature_result(number, cost, signature):
            return f'OK{request_parsed["InvId"]}', True
        return "bad sign", False


# engine = PaymentEngine(auth=PaymentAuth(
#     merchant_login='slim1',
#     merchant_password_1='mBU3D2o251TfgackvLBV',
#     merchant_password_2='guY5fa4EPDW2EKOy2UZ0',
# ))

# print(engine.generate_payment_link(15, 'Description', 1))
