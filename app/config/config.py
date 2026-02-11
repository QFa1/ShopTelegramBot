import json
from dotenv import load_dotenv, find_dotenv, set_key
import os

from aiogram import Bot
import yookassa


load_dotenv()
dotenv_path = find_dotenv()

PATH_DATABASE = 'db/shop.db'

# .env data
bot = Bot(token=os.getenv('TOKEN'))
ADMINS_ID = os.getenv('ADMINS_ID').split(';')
_HELP_ADMIN_ = os.getenv('ADMIN_USERNAME_LINK')

# JSON data
with open('data.json', 'r') as file:
    json_data = json.load(file)
_PAYMENT_METHODS_ = json_data.get('_payment_methods_')
_TG_STAR_ = json_data.get('_TG_Star_in_USDT_')["amount"]  # Стоимость одной телеграм звезды в долларах
# Сколько процентов рублей добавляется при оплате тгСтар
_TG_STAR_PERCENT_ = json_data.get('_TG_Star_in_USDT_')["percent"]
_REFERRAL_SYSTEM_ = json_data.get('_Referral_System_')

# Настройки главного канала
MAIN_CHANNEL = json_data.get('_Main_Channel_')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Payments
CRYSTALPAY_LOGIN = os.getenv('CRYSTALPAY_LOGIN')
CRYSTALPAY_SECRET = os.getenv('CRYSTALPAY_SECRET')

yookassa_account_id = os.getenv('ACCOUNT_ID')
yookassa_secret_key = os.getenv('SECRET_KEY')


def yookassa_start(id, key):
    yookassa.Configuration.account_id = id
    yookassa.Configuration.secret_key = key


if yookassa_account_id != '' or yookassa_secret_key != '':
    yookassa_start(yookassa_account_id, yookassa_secret_key)


async def reloadCrystalAPI(login, secret):
    global CRYSTALPAY_LOGIN, CRYSTALPAY_SECRET
    CRYSTALPAY_LOGIN = login
    CRYSTALPAY_SECRET = secret


async def change_help_admin(username):
    global _HELP_ADMIN_
    _HELP_ADMIN_ = f"t.me/{username.replace('@', '')}"
    await update_env('ADMIN_USERNAME_LINK', _HELP_ADMIN_)


async def change_admins(new_admin=None, delete_admin=None):
    global ADMINS_ID
    if new_admin is not None:
        ADMINS_ID += [f'{new_admin}']
        await update_env('ADMINS_ID', ";".join(map(str, ADMINS_ID)))
    elif delete_admin is not None:
        if delete_admin in ADMINS_ID:
            ADMINS_ID.remove(delete_admin)
            await update_env('ADMINS_ID', ";".join(map(str, ADMINS_ID)))


async def update_env(key, value):
    if os.path.exists(dotenv_path):
        set_key(dotenv_path, key, value)
        return True
    else:
        return False


async def is_user_subscribed(user_id):  # Проверка подписки пользователя на канал
    try:
        chat_member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False


async def conditionMainChannel(condition):
    global MAIN_CHANNEL
    MAIN_CHANNEL = condition


async def changeChannelID(new_id):
    global CHANNEL_ID
    CHANNEL_ID = new_id
