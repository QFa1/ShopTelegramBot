import yookassa
from yookassa import Payment
import uuid


def create(amount, chat_id, id, key):
    if id == '' or key == '':
        return False, False
    try:
        id_key = str(uuid.uuid4())
        payment = Payment.create({
            "amount": {
                'value': amount,
                'currency': "RUB"
            },
            'payment_method_data': {
                'type': 'bank_card'
            },
            'confirmation': {
                'type': 'redirect',
                'return_url': 'https://t.me/AutoShop_TateBot'
            },
            'capture': True,
            'metadata': {
                'chat_id': chat_id
            }
        }, id_key)
        return payment.confirmation.confirmation_url, payment.id
    except Exception:
        return False, False


def check(payment_id):
    payment = yookassa.Payment.find_one(payment_id)
    if payment.status == 'succeeded':
        return payment.metadata
    else:
        return False
