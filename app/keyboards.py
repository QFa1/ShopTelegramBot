from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import config

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Купить 🚀')],
    [KeyboardButton(text='Профиль 👤'), KeyboardButton(text='Поддержка 🆘')]
],
    resize_keyboard=True,  # Минимальный размер кнопки
    input_field_placeholder='❤️',
)


async def help_():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Связаться со мной', url=config._HELP_ADMIN_)]])


back = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад 🔙', callback_data='back')]
])
profile = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💰 Пополнить баланс', callback_data='up_balance')],
    [InlineKeyboardButton(text='🛍️ Мои покупки', callback_data='profile_purchases;None')]
])
close = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Закрыть ✖️', callback_data='back_delete')]
])
back_to_profile = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад 🔙', callback_data='back_delete')]
])


async def categories_kb(data):  # Отображение категорий
    keyboard = InlineKeyboardBuilder()
    for item in data:
        keyboard.add(InlineKeyboardButton(text=item.category, callback_data=f'category;{item.category};{item.id}'))
    return keyboard.adjust(1).as_markup()


async def products_kb(prods, category_):  # Отображение продуктов
    keyboard = InlineKeyboardBuilder()
    for prod in prods:
        if prod.count > 0:
            keyboard.add(InlineKeyboardButton(text=f'{prod.name} | {prod.price}₽',
                                              callback_data=f"product;{prod.id};{category_.id}"))
    keyboard.add(InlineKeyboardButton(text="Назад 🔙", callback_data="buy"))
    return keyboard.adjust(1).as_markup()


async def product_btn(prod_id, is_admin=False):  # Кнопка в продукте
    if is_admin:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Посмотреть данные', callback_data=f'look_data;{prod_id}')],
            [InlineKeyboardButton(text='Закрыть ✖️', callback_data=f'back_delete')]])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Купить товар', callback_data=f'buy_product;{prod_id}')],
        [InlineKeyboardButton(text='Закрыть ✖️', callback_data=f'back_delete')]
    ])


async def buy(prod_id):  # Кнопки подтверждения покупки
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Да', callback_data=f'buy_product;{prod_id};yes'),
         InlineKeyboardButton(text='Нет', callback_data=f'buy_product;{prod_id};no')]
    ])


async def channel():  # Кнопка подписаться на канал
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Подписаться 👉', url=f'https://t.me/{config.CHANNEL_ID[1:]}')]
    ])


async def payment_method1(methods, prod_data=None, up_balance=None):  # Способы оплаты
    keyboard = InlineKeyboardBuilder()
    if prod_data is not None:
        callback_text = f'{prod_data.price};{prod_data.id}'
    else:
        callback_text = f'{up_balance};up_balance'
    if methods['TelegramStars'] == 'True':
        keyboard.add(InlineKeyboardButton(text='⭐ Telegram Stars', callback_data=f'payment;TGStars;{callback_text}'))
    if methods['CryptoBot'] == 'True':
        keyboard.add(InlineKeyboardButton(text='💠 CryptoBot', callback_data=f'payment;CryptoBot;{callback_text}'))
    if methods['CrystalPay'] == 'True':
        keyboard.add(InlineKeyboardButton(text='💎 CrystalPAY', callback_data=f'payment;CrystalPay;{callback_text}'))
    if methods['YooKassa'] == 'True':
        keyboard.add(InlineKeyboardButton(text='💸 ЮKassa', callback_data=f'payment;YKassa;{callback_text}'))
    keyboard.add(InlineKeyboardButton(text='Отменить ✖️', callback_data=f'back_delete'))
    return keyboard.adjust(1).as_markup()


async def payment_methodCrypto(methods, price, prod_id):  # Способы оплаты CryptoBot (USDT, TON, BTC and etc.)
    keyboard = InlineKeyboardBuilder()
    for method in methods.split(';'):
        keyboard.add(InlineKeyboardButton(text=method, callback_data=f'paymentCrypto;{method};{price};{prod_id}'))
    keyboard.row(InlineKeyboardButton(text='Отменить ✖️', callback_data=f'back_delete'))
    return keyboard.as_markup()


async def Yookassa_KB(url, id, prod_id, price):  # Оплата Юкассой
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='💲 Оплатить', url=url),
                 InlineKeyboardButton(text='💳 Проверить оплату', callback_data=f'payYKas;{id};{prod_id};{price}'))
    return keyboard.as_markup()


async def CrystalPay_KB(url, id, prod_id, price):  # Оплата CrystalPay
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='💲 Оплатить', url=url),
                 InlineKeyboardButton(text='💳 Проверить оплату', callback_data=f'payCrystalPay;{id};{price};{prod_id}'))
    return keyboard.as_markup()


async def tg_stars_payment(price):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=f"Оплатить {price} ⭐️", pay=True)
    return keyboard.as_markup()


async def cryptoBot_payment(url):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='💲 Оплатить', url=url)
    return keyboard.as_markup()


# Admin -------------------------------------------------------------------------------------------------
main_admin = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Купить 🚀')],
    [KeyboardButton(text='Профиль 👤'), KeyboardButton(text='Поддержка 🆘')],
    [KeyboardButton(text='📚 Изменить категории'), KeyboardButton(text='🥖 Товары')],
    [KeyboardButton(text='👥 Пользователи'), KeyboardButton(text='💳 Способы оплаты'),
     KeyboardButton(text='⚙️ Настройки')]
],
    resize_keyboard=True,
    input_field_placeholder='❤️',
)
users_admin = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🔗 Реферальная система'), KeyboardButton(text='🪪 Данные пользователя')],
    [KeyboardButton(text='🔙 На главную'), KeyboardButton(text='✉️ Рассылка')]
],
    resize_keyboard=True,
    input_field_placeholder='👥'
)
admin_settings = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='👑 Админы'), KeyboardButton(text='💫 Главный канал'), KeyboardButton(text='📊 Статистика')],
    [KeyboardButton(text='🔙 На главную'), KeyboardButton(text='📦 Получить БД')]
],
    resize_keyboard=True,
    input_field_placeholder='⚙️')

admin_mailing_conf = InlineKeyboardMarkup(inline_keyboard=[  # Изменять баланс пользователю
    [InlineKeyboardButton(text='✅ Отправить', callback_data='mailing_true'),
     InlineKeyboardButton(text='❌ Отменить', callback_data='mailing_false')]])

bot_admins_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='➕ Добавить', callback_data='add_admin'),
     InlineKeyboardButton(text='❌ Удалить', callback_data='delete_admin')],
    [InlineKeyboardButton(text='🔄️ Изменить логин в поддержке', callback_data='change_help_login')]])


async def user_profile_data(user_id):
    kb = InlineKeyboardMarkup(inline_keyboard=[  # Изменять баланс пользователю
        [InlineKeyboardButton(text='➕ Пополнить баланс', callback_data='payhim'),
         InlineKeyboardButton(text='➖ Уменьшить баланс', callback_data='change_user_balance')],
        [InlineKeyboardButton(text='🛍️ Покупки', callback_data=f'profile_purchases;{user_id}')]
    ])
    return kb


async def admin_categories(data):  # Панель категорий у админа
    keyboard = InlineKeyboardBuilder()
    for item in data:
        keyboard.add(InlineKeyboardButton(text=item.category,
                                          callback_data=f'category;{item.category};{item.id};admin'),
                     InlineKeyboardButton(text='↩️', callback_data=f'change;{item.category};{item.id}'),
                     InlineKeyboardButton(text='❌', callback_data=f'delete;{item.category};{item.id}'))
    keyboard.row(InlineKeyboardButton(text='➕ Добавить категорию', callback_data='add'))
    return keyboard.adjust(3).as_markup()


async def products_kb_admin(products_, category_):  # Панель продуктов у админа
    keyboard = InlineKeyboardBuilder()
    for prod in products_:
        keyboard.row(InlineKeyboardButton(text=f'{prod.name} | {prod.price}₽ | {prod.count} шт.',
                                          callback_data=f"product;{prod.id};{category_.id};admin"),
                     InlineKeyboardButton(text='❌', callback_data=f'delete_prod;{prod.id};{prod.name}'))
    keyboard.row(InlineKeyboardButton(text='➕ Добавить товар в категорию', callback_data=f'add_prod;{category_.id}'),
                 InlineKeyboardButton(text="Назад 🔙", callback_data="change_categories"))
    return keyboard.as_markup()


async def redactProductData(product_data):  # Удалять данные в продукте
    keyboard = InlineKeyboardBuilder()
    for item in product_data:
        if item.purchased:
            keyboard.row(InlineKeyboardButton(text=f'\n🟩 {item.data}',
                                              callback_data=f'deleteData;{item.id};{item.product_id}'))
        else:
            keyboard.row(InlineKeyboardButton(text=f'\n🟥 {item.data}',
                                              callback_data=f'deleteData;{item.id};{item.product_id}'))
    keyboard.row(InlineKeyboardButton(text='Закрыть ✖️', callback_data=f'back_delete'))
    return keyboard.as_markup()


async def delete_admin(admins):  # Удалять админов
    keyboard = InlineKeyboardBuilder()
    for admin in admins:
        keyboard.add(InlineKeyboardButton(text=f'➖ {admin}', callback_data=f'delete_admin2;{admin}'))
    keyboard.add(InlineKeyboardButton(text='Закрыть ✖️', callback_data='back_delete'))
    return keyboard.adjust(1).as_markup()


async def changeMainChannel(main_channel):
    keyboard = InlineKeyboardBuilder()
    if main_channel == 'True':
        keyboard.add(InlineKeyboardButton(text='✅ Включено', callback_data='ChangeMainChannel;True'))
    else:
        keyboard.add(InlineKeyboardButton(text='❌ Выключено', callback_data='ChangeMainChannel;False'))
    keyboard.add(InlineKeyboardButton(text='➕ Добавить/Изменить канал', callback_data='RedactMainChannel'))
    return keyboard.adjust(1).as_markup()


async def payment_methods_kb(data):  # Изменять методы оплаты (Включить или отключить оплату, например, Юкассой)
    keyboard = InlineKeyboardBuilder()
    for method, available in data.items():
        if available == 'True':
            keyboard.add(InlineKeyboardButton(text=f'✅ {method}', callback_data=f'payment_method2;{method};True'),
                         InlineKeyboardButton(text='📝 API', callback_data=f'api_pay;{method}'))
        elif available == 'False':
            keyboard.add(InlineKeyboardButton(text=f'❌ {method}', callback_data=f'payment_method2;{method};False'),
                         InlineKeyboardButton(text='📝 API ', callback_data=f'api_pay;{method}'))
    return keyboard.adjust(2).as_markup()


async def ref_system_kb(data):  # Изменять методы оплаты (Включить или отключить оплату, например, Юкассой)
    keyboard = InlineKeyboardBuilder()
    if data == 'False':
        keyboard.add(InlineKeyboardButton(text='✅ Включить', callback_data=f'ref_system2;False'))
    elif data == 'True':
        keyboard.add(InlineKeyboardButton(text=f'❌ Отключить', callback_data=f'ref_system2;True'))
    keyboard.add(InlineKeyboardButton(text='✏️ Изменить процент', callback_data=f'referral_percent'))
    return keyboard.adjust(1).as_markup()


tgStars_Instruction = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📕 Инструкция', url='https://telegra.ph/Oplata-Telegram-Stars-12-10-4')],
    [InlineKeyboardButton(text='♾️ Изменить процент', callback_data='changeTGStarsPercent')],
    [InlineKeyboardButton(text='🔙 Назад', callback_data='backToPay')]
])
CryptoBot_Instruction = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📕 Инструкция', url='https://telegra.ph/Oplata-Crypto-Bot-12-13')],
    [InlineKeyboardButton(text='Добавить/Изменить ключ', callback_data='change_api_key;CryptoBot')],
    [InlineKeyboardButton(text='🔙 Назад', callback_data='backToPay')]
])
Yookassa_Instruction = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📕 Инструкция', url='https://telegra.ph/Oplata-YUkassoj-12-13')],
    [InlineKeyboardButton(text='Добавить/Изменить данные', callback_data='change_api_key;Yookassa')],
    [InlineKeyboardButton(text='🔙 Назад', callback_data='backToPay')]
])
CrystalPay_Instruction = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📕 Инструкция', url='https://telegra.ph/Oplata-CrystalPay-12-21')],
    [InlineKeyboardButton(text='Добавить/Изменить данные', callback_data='change_api_key;CrystalPay')],
    [InlineKeyboardButton(text='🔙 Назад', callback_data='backToPay')]
])
