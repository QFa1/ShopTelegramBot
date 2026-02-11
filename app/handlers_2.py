# Aiogram
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery

from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
# My files
import app.keyboards as kb
from data import db_session
from data.users import User
from data.categories import Categories
from data.products import Products
from data.data_product import Data_Product

from app.payments.Yookassa_ import create, check
from app.payments.CrystalPay_ import create_crystalpay_invoice, check_crystalpay_payment_status
# Others
from dotenv import load_dotenv
import os
import math
import json
from datetime import datetime
from app.config import config
# Payments
from aiocpa import CryptoPay
from aiocpa.types import Invoice


load_dotenv()
router2 = Router()
bot = config.bot

cp = None
RUB_IN_USDT = 105
_CryptoBot_ApiKey_ = os.getenv('CRYPTO_BOT_API')
if _CryptoBot_ApiKey_ != '':
    try:
        cp = CryptoPay(_CryptoBot_ApiKey_)
        RUB_IN_USDT = cp.exchange(1, "RUB", "USDT")  # 1 рубль в USDT

        # CryptoBot
        @cp.polling_handler()
        async def handle_payment(invoice: Invoice, message: Message) -> None:
            await payment(message)
    except Exception:
        print('! Неправильный api ключ CryptoBot ! Перезапустите бота и добавьте новый ключ!')

_yookassa_account_id_ = config.yookassa_account_id
_yookassa_secret_key_ = config.yookassa_secret_key

CRYSTALPAY_SECRET = config.CRYSTALPAY_SECRET
CRYSTALPAY_LOGIN = config.CRYSTALPAY_LOGIN

_PAYMENT_METHODS_ = config._PAYMENT_METHODS_  # Какими банками можно оплачивать
_TG_STAR_ = config._TG_STAR_  # Стоимость одной телеграм звезды в долларах
_TG_STAR_PERCENT_ = config._TG_STAR_PERCENT_
_REFERRAL_SYSTEM_ = config._REFERRAL_SYSTEM_
json_data = config.json_data

# Флажки, чтобы добавить, изменить или удалить категорию
is_change, is_delete, is_add = False, False, False
# Флажки, чтобы добавить, изменить или удалить товар
product_add, product_delete, product_change_all, product_change_id = False, False, False, None
ProdChangeName, ProdChangePrice, ProdChangeQuantity, ProdChangeDescription, ProdChangePhoto, AddProdData = (
    False, False, False, False, False, False)
Change_Ref_Percent, Change_TGSTAR_Percent = False, False
Change_Yookassa_api, Change_CryptoBot_api, Change_CrystalPay_api = False, False, False


@router2.callback_query(F.data == 'back_to_profile')
async def profile_purchases(callback: CallbackQuery):
    db_sess = db_session.create_session()
    user_data = db_sess.query(User).filter(User.user_tg_id == callback.from_user.id).first()
    text = ''
    if _REFERRAL_SYSTEM_["works"] == 'True':
        text = (f'🔗 Количество приглашённых тобой пользователей: <b>{user_data.count_refer}</b>\n'
                f'💸 Получено <b>{user_data.received_from_ref}₽</b> с рефералов.\n\n'
                f'👉 Ваша персональная ссылка на приглашение: '
                f'\n<code>https://t.me/AutoShop_TateBot?start={callback.from_user.id}</code>\n\n'
                f'📖 Вы получите <b>{_REFERRAL_SYSTEM_["percent"]}%</b> рублей, с каждой покупки пользователя, '
                f'которого вы пригласили.')
    await callback.message.edit_text(f'🗃️ ID: <code><b>{callback.from_user.id}</b></code>\n'
                                     f'👛 Баланс: <b>{user_data.balance}₽</b>\n' + text,
                                     parse_mode="HTML", reply_markup=kb.profile)


@router2.message(F.text == 'Профиль 👤')  # Профиль
async def profile1(message: Message):
    if config.MAIN_CHANNEL or await config.is_user_subscribed(message.from_user.id):
        db_sess = db_session.create_session()
        user_data = db_sess.query(User).filter(User.user_tg_id == message.from_user.id).first()
        await message.delete()
        text = ''
        if _REFERRAL_SYSTEM_["works"] == 'True':
            text = (f'🔗 Количество приглашённых тобой пользователей: <b>{user_data.count_refer}</b>\n'
                    f'💸 Получено <b>{user_data.received_from_ref}₽</b> с рефералов.\n\n'
                    f'👉 Ваша персональная ссылка на приглашение: '
                    f'\n<code>https://t.me/AutoShop_TateBot?start={message.from_user.id}</code>\n\n'
                    f'📖 Вы получите <b>{_REFERRAL_SYSTEM_["percent"]}%</b> рублей, с каждой покупки пользователя, '
                    f'которого вы пригласили.')
        await message.answer(f'🗃️ ID: <code><b>{message.from_user.id}</b></code>\n'
                             f'👛 Баланс: <b>{user_data.balance}₽</b>\n' + text,
                             parse_mode="HTML", reply_markup=kb.profile)
    else:
        await message.answer("🙏 Пожалуйста, подпишитесь на наш канал, чтобы использовать бота",
                             reply_markup=await kb.channel())


class Form(StatesGroup):  # Форма для диалогов категорий и продуктов
    id = State()
    name = State()
    price = State()
    description = State()
    image_path = State()
    product_data = State()


@router2.message(Command('admin'))  # Панель админа при команде /admin
async def admin_panel(message: Message):
    ides = os.getenv('ADMINS_ID').split(';')
    if str(message.from_user.id) in ides:
        await message.answer(text='🕶️ Админ панель', reply_markup=kb.main_admin)


@router2.callback_query(F.data == 'admin')  # Панель админа callback
async def admin_panel2(callback: CallbackQuery):
    await callback.message.edit_text(text='🕶️ Админ панель', reply_markup=kb.main_admin)


@router2.callback_query(F.data == 'change_categories')  # Изменять удалять категории
async def change_categories(callback: CallbackQuery):
    db_sess = db_session.create_session()
    await callback.message.edit_text('↩️ - изменить | ❌ - удалить',
                                     reply_markup=await kb.admin_categories(db_sess.query(Categories).all()))


@router2.callback_query(F.data == 'backToPay')  # Настраивать методы оплаты
async def payment_methodsCallback(callback: CallbackQuery):
    if str(callback.from_user.id) in config.ADMINS_ID:
        await callback.message.edit_text('📖 Вы можете отключать и включать нужный вам способ оплаты\n(✅ - включено | '
                                         '❌ - выключено) и изменить API ключ 📝',
                                         reply_markup=await kb.payment_methods_kb(_PAYMENT_METHODS_))
        # Дальше вызывается callback - *payment_method2*


@router2.message(F.text == '🔗 Реферальная система')  # Настройки по реферальной системе | admin
async def pay_him(message: Message, state: FSMContext):
    if str(message.from_user.id) in config.ADMINS_ID:
        await message.delete()
        await state.clear()
        if _REFERRAL_SYSTEM_['works'] == 'True':
            text = 'включена ✅'
        else:
            text = 'отключена ❌'
        await message.answer(f'📖 Если пользователь был приглашён другим юзером, то юзер получает процент '
                             f'денег, задоначенных от пользователя\n\nРеферальная система: <b>{text}</b>.\n'
                             f'Процент от приглашённого пользователя: <b>{_REFERRAL_SYSTEM_["percent"]}%</b>',
                             reply_markup=await kb.ref_system_kb(_REFERRAL_SYSTEM_['works']), parse_mode='HTML')


@router2.callback_query(F.data == 'referral_percent')  # Настройки по реферальной системе | admin
async def pay_him(callback: CallbackQuery, state: FSMContext):
    global Change_Ref_Percent
    Change_Ref_Percent = True
    await state.clear()
    await state.set_state(Form.price)
    await callback.answer('')
    await callback.message.answer('❌ При отмене, отправьте /stop\n\n📝 Отправьте нужный вам процент:')


@router2.callback_query(F.data == 'changeTGStarsPercent')  # Изменить процент TGSTAR | admin
async def pay_him(callback: CallbackQuery, state: FSMContext):
    global Change_TGSTAR_Percent
    Change_TGSTAR_Percent = True
    await state.clear()
    await state.set_state(Form.price)
    await callback.answer('')
    await callback.message.answer('❌ При отмене, отправьте /stop\n\n📝 Отправьте нужный вам процент:')


@router2.callback_query(lambda call: True)  # Ловим все callback-и
async def Change_Delete_Category(callback: CallbackQuery, state: FSMContext):
    global is_change, is_delete, is_add, data_callback, product_add, product_delete, product_change_id, USER_ID
    global _REFERRAL_SYSTEM_, Change_CryptoBot_api, Change_Yookassa_api, Change_CrystalPay_api
    USER_ID = callback.from_user.id
    await state.clear()  # Очищаем диалог на всякий случай
    data_callback = callback.data.split(';')
    # Посмотреть товары из категории | Пользователь и Админ
    if data_callback[0] == 'category':
        db_sess = db_session.create_session()
        categ = db_sess.query(Categories).filter(Categories.category == data_callback[1]).first()
        prods = db_sess.query(Products).filter(Products.categ_id == categ.id).all()
        try:
            await callback.answer('')
            if data_callback[-1] == 'admin':
                await callback.message.edit_text(f'*➖ {categ.category} ➖*\n📦 Выберите товар:\n❌ - удалить '
                                                 f'продукт\nЕсли товар закончился, он не отображается у пользователя.',
                                                 reply_markup=await kb.products_kb_admin(prods, categ),
                                                 parse_mode="Markdown")
            else:
                await callback.message.edit_text(f'*➖ {categ.category} ➖*\n📦 Выберите товар:',
                                                 reply_markup=await kb.products_kb(prods, categ), parse_mode="Markdown")
        except Exception:  # Если тг не может отредачить сообщение, то отправляем ему новое
            if data_callback[-1] == 'admin':
                await callback.message.answer(f'*➖ {categ.category} ➖*\n📦 Выберите товар:'
                                              f'\n❌ - удалить продукт',
                                              reply_markup=await kb.products_kb_admin(prods, categ),
                                              parse_mode="Markdown")
            else:
                await callback.message.answer(f'*➖ {categ.category} ➖*\n📦 Выберите товар:',
                                              reply_markup=await kb.products_kb(prods, categ), parse_mode="Markdown")

    # Диалог добавления продуктов | Админ
    elif data_callback[0] == 'add_prod':
        product_add = True
        await state.set_state(Form.name)  # Начинаем диалог добавления продуктов
        await state.update_data(categ_id=data_callback[1])
        await callback.answer('')
        await callback.message.answer(text='При отмене, отправьте /stop\n\nНапишите название нового продукта:')
    #  Просмотр продукта | Пользователь и админ
    elif data_callback[0] == 'product':
        await callback.answer('')
        db_sess = db_session.create_session()
        prod = db_sess.query(Products).filter(Products.id == int(data_callback[1])).first()
        text = f'➖<b>Покупка➖</b>\n📦 Товар: {prod.name} \n💰 Цена: {prod.price}₽\n🛒 Доступно: {prod.count}'
        if prod.description is not None:
            text += f'\n\n<u>Описание:</u>\n{prod.description}'
        if data_callback[-1] == 'admin':
            await callback.answer('')
            product_change_id = prod.id
            text += ('\n\n<b>=====Панель админа=====</b>\nИзменить:\nВесь продукт: /change_product\nНазвание: '
                     '/change_name\nЦену: /change_price\nОписание: /change_description\nФото: /change_photo\n'
                     'Добавить данные: /add_product_data\nИзменить данные: /redact_data')
            if prod.image_path is not None:
                await callback.message.answer_photo(photo=prod.image_path, caption=text, parse_mode="HTML",
                                                    reply_markup=await kb.product_btn(prod.id, True))
            else:
                await callback.message.answer(text=text, parse_mode="HTML",
                                              reply_markup=await kb.product_btn(prod.id, True))
        else:
            if prod.image_path is not None:
                await callback.message.answer_photo(photo=prod.image_path, caption=text, parse_mode="HTML",
                                                    reply_markup=await kb.product_btn(prod.id))
            else:
                await callback.message.answer(text=text, parse_mode="HTML",
                                              reply_markup=await kb.product_btn(prod.id))
    # Покупка продукта
    elif data_callback[0] == 'buy_product':
        db_sess = db_session.create_session()
        user_data = db_sess.query(User).filter(User.user_tg_id == callback.from_user.id).first()
        prod_data = db_sess.query(Products).filter(Products.id == data_callback[1]).first()
        if data_callback[-1] == 'yes':
            await callback.answer('')
            await callback.message.delete()
            # Меняем информацию, что продукт куплен и выдаём данные пользователю
            dat_prod = db_sess.query(Data_Product).filter(Data_Product.product_id == data_callback[1],
                                                          Data_Product.purchased == False).first()
            data_1 = dat_prod.data.split(':')

            purchases_data = f'{prod_data.price}|{dat_prod.data}|{datetime.now()};'
            if user_data.purchases is not None:
                purchases_data += user_data.purchases
            db_sess.query(User).filter(User.user_tg_id == callback.from_user.id).update({
                'balance': user_data.balance - prod_data.price,
                'purchases': purchases_data
            })
            try:
                text = f'<b>💌 Спасибо за покупку!</b>\n\n<i>Ваши данные:</i>\nlogin: {data_1[0]}\npassword: {data_1[1]}'
            except IndexError:
                text = f'<b>💌 Спасибо за покупку!</b>\n\n<i>Ваши данные:</i>\n{data_1[0]}'
            await callback.message.answer(text, parse_mode="HTML")
            db_sess.query(Data_Product).filter(Data_Product.id == dat_prod.id).update({'purchased': True})
            prod_1 = db_sess.query(Products).filter(Products.id == data_callback[1])
            prod_1.update({'count': prod_1.first().count - 1})
            db_sess.commit()

        elif data_callback[-1] == 'no':
            await callback.answer('')
            await callback.message.delete()
            await callback.message.answer(f'❗Отмена покупки❗')
        elif prod_data.count < 1:
            await callback.answer('')
            await callback.message.answer('Извините, данный товар у нас закончился, но мы скоро добавим новый')
        else:
            if user_data.balance - prod_data.price >= 0:
                await callback.answer('')
                await callback.message.answer(f'💵 Вы точно хотите купить продукт {prod_data.name}?',
                                              reply_markup=await kb.buy(prod_data.id))
            else:
                await callback.answer('')
                # Возвращаем callback - payment
                await callback.message.answer('💳 Выберите способ оплаты:',
                                              reply_markup=await kb.payment_method1(methods=_PAYMENT_METHODS_,
                                                                                    prod_data=prod_data))
    # Оплата продукта или пополнение счёта
    elif data_callback[0] == 'payment':
        if data_callback[1] == 'CryptoBot':
            if cp is not None:
                await callback.message.edit_text('💱 Выберите валюту:', reply_markup=await kb.payment_methodCrypto(
                    os.getenv('PAYMENT_METHODS'), data_callback[2], data_callback[3]))
            else:
                for admin_id in config.ADMINS_ID:
                    await bot.send_message(admin_id,
                                           f'❗У пользователя <code>{callback.from_user.id}</code> не прошла '
                                           f'оплата CryptoBot.❗\nИзмените или добавьте данные.',
                                           parse_mode='HTML')
                await callback.message.answer(text='❗Извините, но оплата CryptoBot временно не работает❗')
        elif data_callback[1] == 'YKassa':
            payment_url, payment_id = create(data_callback[2], callback.message.chat.id,
                                             _yookassa_account_id_, _yookassa_secret_key_)
            if not payment_url:
                await callback.answer('')
                for admin_id in config.ADMINS_ID:
                    await bot.send_message(admin_id, f'❗У пользователя <code>{callback.from_user.id}</code> не прошла '
                                                     f'оплата ЮКассой.❗\nИзмените или добавьте данные.',
                                           parse_mode='HTML')
                await callback.message.answer(text='❗Извините, но оплата Юкассой временно не работает❗')
            else:
                await callback.message.edit_text(text=f"📦 Оплатите <b>{data_callback[2]}₽</b> по кнопке ниже:",
                                                 reply_markup=await kb.Yookassa_KB(
                                                     payment_url, payment_id, data_callback[3], data_callback[2]),
                                                 parse_mode="HTML")
        elif data_callback[1] == 'CrystalPay':
            if CRYSTALPAY_LOGIN != '' or CRYSTALPAY_SECRET != '':
                data_payment = create_crystalpay_invoice(data_callback[2], f'Оплата на {data_callback[2]}₽')
                await callback.message.edit_text(text=f"📦 Оплатите <b>{data_callback[2]}₽</b> по кнопке ниже:",
                                                 reply_markup=await kb.CrystalPay_KB(
                                                     data_payment[0], data_payment[1],
                                                     data_callback[3], data_callback[2]), parse_mode='HTML')
            else:
                await callback.answer('')
                for admin_id in config.ADMINS_ID:
                    await bot.send_message(admin_id,
                                           f'❗У пользователя <code>{callback.from_user.id}</code> не прошла '
                                           f'оплата CrystalPay.❗\nИзмените или добавьте данные.', parse_mode='HTML')
                await callback.message.answer(text='❗Извините, но оплата CrystalPay временно не работает❗')

        elif data_callback[1] == 'TGStars':
            # Из рублей в telegram stars
            amount = math.ceil((int(data_callback[2]) * (_TG_STAR_PERCENT_ / 100 + 1)) * RUB_IN_USDT / _TG_STAR_)
            prices = [LabeledPrice(label="XTR", amount=amount)]
            await callback.message.delete()
            await callback.message.answer_invoice(
                title=f"Оплата на {data_callback[2]}₽",
                description="💘 Оплатите по кнопке ниже:",
                prices=prices,
                provider_token="",
                payload="channel_support",
                currency="XTR",
                reply_markup=await kb.tg_stars_payment(amount),
            )
    elif data_callback[0] == 'paymentCrypto':
        summm = await cp.exchange(int(data_callback[2]), "RUB", data_callback[1])  # Из рублей в нужную валюту
        invoice = await cp.create_invoice(round(summm, 3), data_callback[1])
        await callback.message.edit_text(f"📦 Оплатите <b>{round(summm, 3)} {data_callback[1]}</b> по кнопке ниже:\n",
                                         parse_mode="HTML",
                                         reply_markup=await kb.cryptoBot_payment(invoice.mini_app_invoice_url))
        invoice.await_payment(message=callback.message)
    elif data_callback[0] == 'payYKas':  # Проверяем, оплатил ли пользователь
        await callback.answer('')
        if not check(data_callback[1]):
            await callback.message.answer('❕ Оплата ещё не прошла ❕')
        else:
            await callback.message.delete()
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.user_tg_id == USER_ID)
            user_data = user.first()
            # Если реф. система включена и пользователь был кем то приглашён, то добавляем денег реферу
            if user_data.refer_id is not None and _REFERRAL_SYSTEM_["works"] == 'True':
                ref_user = db_sess.query(User).filter(User.user_tg_id == user_data.refer_id)
                percent_money = int(_REFERRAL_SYSTEM_["percent"] / 100 * int(data_callback[3]))
                ref_user.update({
                    'balance': ref_user.first().balance + percent_money,
                    'received_from_ref': ref_user.first().received_from_ref + percent_money,
                })
            if data_callback[2] == 'up_balance':
                # Добавляем данные в покупки юзера
                purchases_data = f'{int(data_callback[3])}|None|{datetime.now()};'
                if user_data.purchases is not None:
                    purchases_data += user_data.purchases
                user.update({'balance': user_data.balance + int(data_callback[3]),
                             'all_money': user_data.all_money + int(data_callback[3]),
                             'purchases': purchases_data})
                db_sess.commit()
                return await callback.message.answer(f'<b>💌 Спасибо за пополнение на {data_callback[3]}₽!</b>',
                                                     parse_mode="HTML")
            else:
                dat_prod = db_sess.query(Data_Product).filter(Data_Product.product_id == data_callback[2],
                                                              Data_Product.purchased == False).first()
                # Добавляем данные в покупки юзера
                purchases_data = f'{int(data_callback[3])}|{dat_prod.data}|{datetime.now()};'
                if user_data.purchases is not None:
                    purchases_data += user_data.purchases
                user.update({'all_money': user_data.all_money + int(data_callback[3]),
                             'purchases': purchases_data})
                # Меняем информацию, что продукт куплен и выдаём данные пользователю
                data_1 = dat_prod.data.split(':')
                try:
                    text = (f'<b>💌 Спасибо за покупку!</b>\n\n<i>Ваши данные:</i>\nlogin: {data_1[0]}\npassword: '
                            f'{data_1[1]}')
                except IndexError:
                    text = f'<b>💌 Спасибо за покупку!</b>\n\n<i>Ваши данные:</i>\n{data_1[0]}'
                await callback.message.answer(text, parse_mode="HTML")
                prod_1 = db_sess.query(Products).filter(Products.id == data_callback[2])
                prod_1.update({'count': prod_1.first().count - 1})  # Количество оставшихся данных
                db_sess.query(Data_Product).filter(Data_Product.id == dat_prod.id).update({'purchased': True})
                db_sess.commit()
    elif data_callback[0] == 'payCrystalPay':  # Оплатил ли
        await callback.answer('')
        check_payment = check_crystalpay_payment_status(data_callback[1])
        if check_payment[0] == 'error':
            await callback.answer('')
            for admin_id in config.ADMINS_ID:
                await bot.send_message(admin_id,
                                       f'❗У пользователя <code>{callback.from_user.id}</code> не прошла '
                                       f'оплата CrystalPay.❗\n Ошибка:\n{check_payment[1]}', parse_mode='HTML')
            await callback.message.answer(text='❗Извините, но оплата CrystalPay временно не работает❗')
        elif check_payment == 'payed':
            await payment(callback.message)
        else:
            await callback.message.answer('❕ Оплата ещё не прошла ❕')

    # Изменять категории | админ
    elif data_callback[0] == 'change':
        is_change = True
        await state.set_state(Form.name)  # Устанавливаем состояние диалога
        await callback.answer('')
        await callback.message.answer(text=f'✏️ Изменить категорию: <b>{data_callback[1]}</b>\n'
                                           f'Напиши новое название', parse_mode='HTML')
    elif data_callback[0] == 'add':  # Добавить категорию
        is_add = True
        await state.set_state(Form.name)
        await callback.answer('')
        await callback.message.answer(text=f'Напишите название для категории.')
    elif data_callback[0] == 'delete':  # Удалить категорию
        is_delete = True
        await state.set_state(Form.name)
        await callback.answer('')
        await callback.message.answer(text=f'Вы точно хотите удалить категорию {data_callback[1]}?\n'
                                           f'Все продукты из этой категории тоже удалятся. (подтвердить | отменить)\n'
                                           f'/confirm ✔️ | /cancel 🔙 ')
    # Удалить продукт | Админ
    elif data_callback[0] == 'delete_prod':
        product_delete = True
        await state.set_state(Form.name)
        await callback.answer('')
        await callback.message.answer(text=f'Вы точно хотите удалить продукт {data_callback[2]}?\n'
                                           f'(подтвердить | отменить)\n'
                                           f'/confirm ✔️ | /cancel 🔙 ')
    # Посмотреть данные в продукте | Админ
    elif data_callback[0] == 'look_data':
        await callback.answer('')
        db_sess = db_session.create_session()
        items = db_sess.query(Data_Product).filter(Data_Product.product_id == data_callback[1]).all()
        text = '(🟥 - не куплено | 🟩 - куплено)\n\n<b>==========Данные==========</b>'
        for item in items:
            if item.purchased:
                text += f'\n🟩 {item.data}'
            else:
                text += f'\n🟥 {item.data}'
        await callback.message.answer(text=text, parse_mode="HTML", reply_markup=kb.close)
    # Удалить данные в продукте | Админ
    elif data_callback[0] == 'deleteData':
        await callback.answer('')
        db_sess = db_session.create_session()
        data_prod_1 = db_sess.query(Data_Product).filter(Data_Product.id == int(data_callback[1]))
        data_prod_2 = data_prod_1.first()
        await callback.message.answer(f'Данные {data_prod_2.data} удалены.', reply_markup=kb.close)
        data_prod_1.delete()
        prod_1 = db_sess.query(Products).filter(Products.id == int(data_callback[2]))
        if data_prod_2.purchased is False:
            prod_1.update({'count': prod_1.first().count - 1})  # Количество оставшихся данных
        db_sess.commit()
    elif data_callback[0] == 'profile_purchases':  # Посмотреть покупки
        db_sess = db_session.create_session()
        if data_callback[1] == 'None':
            _userID_ = callback.from_user.id
        else:
            _userID_ = int(data_callback[1])
        data = db_sess.query(User).filter(User.user_tg_id == _userID_).first().purchases
        text = ''
        await callback.answer('')
        if data is None:
            text = 'У вас ещё не было пополнений 😔'
            if data_callback[1] != 'None':
                text = 'Пользователь не совершал покупок.'
        else:
            for index, purchase in enumerate(data.split(';'), start=1):
                data_purchase = purchase.split('|')
                try:
                    if data_purchase[1] == 'None':
                        tt = datetime.strptime(data_purchase[2], "%Y-%m-%d %H:%M:%S.%f").strftime("%d-%m-%Y %H:%M")
                        text += f'{index}. Пополнение на: {data_purchase[0]}₽<b>│</b>{tt}\n'
                    else:
                        if data_purchase[0][0] == '!':
                            tt = datetime.strptime(data_purchase[2], "%Y-%m-%d %H:%M:%S.%f").strftime("%d-%m-%Y %H:%M")
                            text += (f"{index}. Покупка с баланса: {data_purchase[0].replace('!', '')}₽<b>│</b>{tt}<b>"
                                     f"│</b><code>{data_purchase[1]}</code>\n")
                        else:
                            tt = datetime.strptime(data_purchase[2], "%Y-%m-%d %H:%M:%S.%f").strftime("%d-%m-%Y %H:%M")
                            text += (f'{index}. Покупка на: {data_purchase[0]}₽<b>│</b>{tt}<b>│</b>'
                                     f'<code>{data_purchase[1]}</code>\n')
                except IndexError:
                    pass
        await callback.message.answer(text, reply_markup=kb.close, parse_mode='HTML')
    elif data_callback[0] == 'payment_method2':  # Настраивать способы оплаты. Вкл/выкл способ оплаты
        with open('data.json', 'w') as file_1:
            if data_callback[2] == 'True':  # Отключаем способ оплаты
                json_data['_payment_methods_'][data_callback[1]] = 'False'
            elif data_callback[2] == 'False':  # Включаем способ оплаты
                json_data['_payment_methods_'][data_callback[1]] = 'True'
            json.dump(json_data, file_1, indent=4)
            await callback.message.edit_text('Нажмите, чтобы поменять состояние (✅ - включено | ❌ - выключено)',
                                             reply_markup=await kb.payment_methods_kb(
                                                 json_data.get('_payment_methods_')))
    elif data_callback[0] == 'ref_system2':  # Отключать и включать реферальную систему в админ панели
        with open('data.json', 'w') as file_2:
            if data_callback[1] == 'True':
                json_data['_Referral_System_']['works'] = 'False'
                text = 'отключена ❌'
            elif data_callback[1] == 'False':
                json_data['_Referral_System_']['works'] = 'True'
                text = 'включена ✅'
            json.dump(json_data, file_2, indent=4)
            _REFERRAL_SYSTEM_ = json_data['_Referral_System_']
            await callback.message.edit_text(f'📖 Если пользователь был приглашён другим юзером, то юзер получает '
                                             f'процент денег, задоначенных от пользователя\n\nРеферальная система: '
                                             f'<b>{text}</b>.\nПроцент от приглашённого пользователя: <b>'
                                             f'{_REFERRAL_SYSTEM_["percent"]}%</b>',
                                             reply_markup=await kb.ref_system_kb(_REFERRAL_SYSTEM_['works']),
                                             parse_mode='HTML')
    elif data_callback[0] == 'api_pay':  # Добавлять и изменять api ключи
        if data_callback[1] == 'TelegramStars':
            await callback.message.edit_text(f'К оплате добавляется <b>{_TG_STAR_PERCENT_}%</b> рублей. \n'
                                             f'Для оплатой Звёздами Телеграмм не нужен API. Подробнее: ',
                                             reply_markup=kb.tgStars_Instruction, parse_mode='HTML')
        elif data_callback[1] == 'CryptoBot':
            text = '<b>➖Оплата CryptoBot➖</b>\n\n'
            if cp is None:
                text += ('❗Оплата не работает, API ключа нет.❗\n📖 Нажмите на инструкцию ниже, чтобы узнать, как его'
                         ' получить.\n\n❕При добавлении api ключа, необходимо перезагрузить бота❕')
            else:
                text += (f'<b>API ключ</b>:\n<span class="tg-spoiler">{_CryptoBot_ApiKey_}</span>\n\n'
                         f'❕Вам придётся перезагрузить бота, если изменить api ключ❕')
            await callback.message.edit_text(text=text, reply_markup=kb.CryptoBot_Instruction, parse_mode='HTML')
        elif data_callback[1] == 'YooKassa':
            text = '<b>➖Оплата ЮКасса➖</b>\n\n'
            if _yookassa_secret_key_ == '' or _yookassa_account_id_ == '':
                text += '❗Оплата не работает, добавьте секретный ключ и id аккаунта❗'
            else:
                text += (f'<b>ACCOUNT ID</b>: <span class="tg-spoiler">{_yookassa_account_id_}</span>\n'
                         f'<b>SECRET KEY</b>: <span class="tg-spoiler">{_yookassa_secret_key_}</span>')
            await callback.message.edit_text(text=text, reply_markup=kb.Yookassa_Instruction, parse_mode='HTML')
        elif data_callback[1] == 'CrystalPay':
            text = '<b>➖Оплата CrystalPay➖</b>\n\n'
            if CRYSTALPAY_SECRET == '' or CRYSTALPAY_LOGIN == '':
                text += '❗Оплата не работает, добавьте секретный ключ и логин аккаунта❗'
            else:
                text += (f'<b>Логин кассы</b>: <span class="tg-spoiler">{CRYSTALPAY_LOGIN}</span>\n'
                         f'<b>Секретный ключ</b>: <span class="tg-spoiler">{CRYSTALPAY_SECRET}</span>')
            await callback.message.edit_text(text=text, reply_markup=kb.CrystalPay_Instruction, parse_mode='HTML')

    elif data_callback[0] == 'change_api_key':  # Изменять апи ключи
        await state.clear()
        await callback.answer('')
        if data_callback[1] == 'Yookassa':
            Change_Yookassa_api = True
            await state.set_state(Form.price)
            await callback.message.answer(text='❌ При отмене нажмите /stop\nОтправьте ID аккаунта:')
        elif data_callback[1] == 'CryptoBot':
            Change_CryptoBot_api = True
            await state.set_state(Form.price)
            await callback.message.answer(text='❌ При отмене нажмите /stop\nОтправьте API ключ:')
        elif data_callback[1] == 'CrystalPay':
            Change_CrystalPay_api = True
            await state.set_state(Form.price)
            await callback.message.answer(text='❌ При отмене нажмите /stop\nОтправьте Логин Кассы:')
    elif data_callback[0] == 'delete_admin2':  # Удалять админов
        await config.change_admins(delete_admin=data_callback[1])
        await callback.answer('')
        await callback.message.answer(f'🕯️ Админ <code>{data_callback[1]}</code> удалён.', parse_mode='HTML')
    elif data_callback[0] == 'ChangeMainChannel':  # Отключать и включать функцию обязательной подписки на канал
        text = ('<i>📖 Вы можете отключить и включить функцию, которая проверяет, чтобы пользователь был подписан на '
                'канал. Так же не забудьте добавить бота в канал.</i>\n\n')
        if config.CHANNEL_ID.replace('@', '') == '':
            text += 'Канал ещё не добавлен ❌'
        else:
            text += f'🏹 Канал: <b>{config.CHANNEL_ID}</b>'
        with open('data.json', 'w') as file_3:
            if data_callback[1] == 'True':  # Отключаем способ оплаты
                json_data['_Main_Channel_'] = 'False'
                await config.conditionMainChannel('False')
            else:  # Включаем способ оплаты
                json_data['_Main_Channel_'] = 'True'
                await config.conditionMainChannel('True')
            json.dump(json_data, file_3, indent=4)
            await callback.message.edit_text(text=text, reply_markup=await kb.changeMainChannel(config.MAIN_CHANNEL),
                                             parse_mode='HTML')
    else:
        print(f'Неизвестный callback: {callback.data}')


@router2.message(Form.name)  # Продолжаем диалог, чтобы редактировать категории или продукты
async def dialog1(message: Message, state: FSMContext):
    global is_change, is_add, is_delete, product_add, product_delete, ProdChangeName
    # Заносим категорию в бд
    db_sess = db_session.create_session()
    if is_change:  # ИЗМЕНИТЬ
        is_change = False
        (db_sess.query(Categories).filter(Categories.category == data_callback[1]).
         update({'category': message.text}))
        await state.clear()
        await message.answer('Название категории успешно изменено.')
    if is_add:  # ДОБАВИТЬ
        is_add = False
        cat = Categories(
            category=message.text
        )
        db_sess.add(cat)
        await state.clear()
        await message.answer(f'Категория успешно добавлена.')
    if is_delete:  # УДАЛИТЬ
        is_delete = False
        if message.text == '/confirm':
            db_sess.delete(db_sess.query(Categories).filter(Categories.category == data_callback[1]).first())
            prods_ = db_sess.query(Products).filter(Products.categ_id == int(data_callback[2])).all()
            for prod_ in prods_:
                db_sess.query(Data_Product).filter(Data_Product.product_id == prod_.id).delete()
            db_sess.query(Products).filter(Products.categ_id == int(data_callback[2])).delete()
            await state.clear()
            await message.answer(f'Категория {data_callback[1]} удалена.')
        elif message.text == '/cancel':
            await state.clear()
            await message.answer(f'❗Удаление категории {data_callback[1]} отменено❗')
        else:
            await message.answer(f'Неизвестная команда. Сделайте всё сначала.')
    # Диалог добавления продуктов в категорию
    if product_add:
        product_add = False
        if not message.text == '/stop':
            if not ProdChangeName:
                await state.update_data(name=message.text)
                await state.set_state(Form.price)
                await message.answer('❌ - /stop\n💵 Напишите цену для продукта:')
            else:
                ProdChangeName = False
                db_sess.query(Products).filter(Products.id == product_change_id).update({'name': message.text})
                await message.answer('✔️ Название продукта успешно изменено.')
                await state.clear()
        elif message.text == '/stop':
            ProdChangeName = False
            await message.delete()
            await state.clear()  # Очищаем диалог, если отправлено /stop
            await message.answer('❗Отменено❗')
    # Диалог удаления продукта в категории
    if product_delete:
        product_delete = False
        if message.text == '/confirm':
            db_sess.query(Data_Product).filter(Data_Product.product_id == int(data_callback[1])).delete()
            db_sess.delete(db_sess.query(Products).filter(Products.id == int(data_callback[1])).first())
            await state.clear()
            await message.answer(f'Продукт {data_callback[2]} успешно удалён.')
        elif message.text == '/cancel':
            await state.clear()
            await message.answer(f'❗Удаление продукта {data_callback[2]} отменено❗')
        else:
            await message.answer(f'Неизвестная команда. Сделайте всё сначала.')
    db_sess.commit()
    db_sess.close()


@router2.message(Form.price)  # Продолжаем диалог, чтобы редактировать продукты
async def dialog2(message: Message, state: FSMContext):
    global ProdChangePrice, Change_Ref_Percent, _REFERRAL_SYSTEM_, Change_TGSTAR_Percent, _TG_STAR_PERCENT_
    global Change_CryptoBot_api, Change_Yookassa_api, Change_CrystalPay_api
    if not message.text == '/stop':
        if Change_CryptoBot_api:
            Change_CryptoBot_api = False
            await state.clear()
            await config.update_env('CRYPTO_BOT_API', message.text)
            text = (f'🎉 Ключ изменён! Перезагрузите бота, чтобы оплата начала работать\n\n'
                    f'<b>API ключ</b>:\n<span class="tg-spoiler">{message.text}</span>\n\n')
            await message.answer(text=text, reply_markup=kb.CryptoBot_Instruction, parse_mode='HTML')
        elif Change_CrystalPay_api:
            await state.update_data(price=message.text)
            await state.set_state(Form.description)
            await message.answer('❌ - /stop\nОтправьте секретный ключ:')
        elif not message.text.isdigit():
            return await message.answer("❌ - /stop\n❗Пожалуйста, введите число❗")
        else:
            if Change_Ref_Percent:  # Изменять проценты по реферальной системе
                Change_Ref_Percent = False
                with open('data.json', 'w') as file_3:
                    json_data['_Referral_System_']['percent'] = int(message.text)
                    json.dump(json_data, file_3, indent=4)
                    _REFERRAL_SYSTEM_ = json_data['_Referral_System_']
                await state.clear()
                await message.answer('Проценты изменены ✅')
            elif Change_TGSTAR_Percent:  # Изменять проценты в оплате TGSTAR
                Change_TGSTAR_Percent = False
                with open('data.json', 'w') as file_4:
                    json_data['_TG_Star_in_USDT_']['percent'] = int(message.text)
                    json.dump(json_data, file_4, indent=4)
                    _TG_STAR_PERCENT_ = json_data['_TG_Star_in_USDT_']['percent']
                await state.clear()
                await message.answer('Проценты изменены ✅')
            elif Change_Yookassa_api:
                await state.update_data(price=int(message.text))
                await state.set_state(Form.description)
                await message.answer('❌ - /stop\nОтправьте секретный ключ:')
            elif not ProdChangePrice:
                await state.update_data(price=int(message.text))
                await state.set_state(Form.description)
                await message.answer('️ Отправьте описание.\n⏩ Чтобы пропустить, отправьте /pass')
            else:
                ProdChangePrice = False
                db_sess = db_session.create_session()
                db_sess.query(Products).filter(Products.id == product_change_id).update({'price': message.text})
                db_sess.commit()
                await message.answer('✔️ Цена продукта успешно изменена.')
                await state.clear()
    elif message.text == '/stop':
        ProdChangePrice, Change_Ref_Percent, Change_TGSTAR_Percent = False, False, False
        Change_CryptoBot_api, Change_Yookassa_api, Change_CrystalPay_api = False, False, False
        await state.clear()  # Очищаем диалог, если отправлено /stop
        await message.answer('❗Отменено❗')


@router2.message(Form.description)  # Продолжаем диалог, чтобы редактировать продукты
async def dialog4(message: Message, state: FSMContext):
    global ProdChangeDescription, Change_Yookassa_api, _yookassa_account_id_, _yookassa_secret_key_, \
        Change_CrystalPay_api, CRYSTALPAY_LOGIN, CRYSTALPAY_SECRET
    if not message.text == '/stop':
        if Change_Yookassa_api:  # Изменить данные Юкассы
            Change_Yookassa_api = False
            x = (await state.get_data())['price']
            await config.update_env('ACCOUNT_ID', str(x))
            await config.update_env('SECRET_KEY', message.text)
            _yookassa_account_id_ = x
            _yookassa_secret_key_ = message.text
            config.yookassa_start(x, message.text)
            await state.clear()
            text = (f'🎉 Данные изменены, бот готов к оплате ЮКассой!\n\n<b>ACCOUNT ID</b>: '
                    f'<span class="tg-spoiler">{x}</span>\n'
                    f'<b>SECRET KEY</b>: <span class="tg-spoiler">{message.text}</span>')
            await message.answer(text=text, reply_markup=kb.Yookassa_Instruction, parse_mode='HTML')
        elif Change_CrystalPay_api:
            Change_CrystalPay_api = False
            x = (await state.get_data())['price']
            await config.update_env('CRYSTALPAY_LOGIN', x)
            await config.update_env('CRYSTALPAY_SECRET', message.text)
            await config.reloadCrystalAPI(x, message.text)
            CRYSTALPAY_LOGIN = x
            CRYSTALPAY_SECRET = message.text
            await state.clear()
            text = (f'🎉 Данные изменены, бот готов к оплате CrystalPay!\n\n<b>Логин кассы</b>: '
                    f'<span class="tg-spoiler">{x}</span>\n'
                    f'<b>Секретный ключ</b>: <span class="tg-spoiler">{message.text}</span>')
            await message.answer(text=text, reply_markup=kb.CrystalPay_Instruction, parse_mode='HTML')
        elif not ProdChangeDescription:
            if not message.text == '/pass':
                await state.update_data(description=message.text)
            else:
                await state.update_data(description=None)
            await state.set_state(Form.image_path)
            await message.answer('🖼️ Отправьте картинку.\n⏩ Чтобы пропустить, отправьте /pass')
        else:
            ProdChangeDescription = False
            if message.text == '/pass':
                descri = None
                text = '✔️ Описание продукта удалено'
            else:
                descri = message.text
                text = '✔️ Описание продукта успешно изменено.'
            db_sess = db_session.create_session()
            db_sess.query(Products).filter(Products.id == product_change_id).update({'description': descri})
            db_sess.commit()
            await message.answer(text)
            await state.clear()
    elif message.text == '/stop':
        ProdChangeDescription, Change_Yookassa_api, Change_CrystalPay_api = False, False, False
        await state.clear()  # Очищаем диалог, если отправлено /stop
        await message.answer('❗Отменено❗')


@router2.message(Form.image_path)  # Продолжаем диалог, чтобы редактировать продукты
async def dialog5(message: Message, state: FSMContext):
    global ProdChangePhoto
    if not message.text == '/stop':
        if not ProdChangePhoto:
            if product_change_all:
                text = ('Добавьте ещё больше данных, каждый с новой строчки, в виде:'
                        '\n\nlogin:password\nlogin:password\nlogin:password\n\nили\n\ndata1\ndata2\ndata3\n\n'
                        'Чтобы пропустить, отправьте /pass')
            else:
                text = ('Отправьте данные, каждый с новой строчки, в виде:'
                        '\n\nlogin:password\nlogin:password\nlogin:password\n\nили\n\ndata1\ndata2\ndata3')
            if message.text == '/pass':
                await state.update_data(image_path=None)
                await state.set_state(Form.product_data)
                await message.answer(text)
            else:
                try:
                    await state.update_data(image_path=message.photo[-1].file_id)
                    await state.set_state(Form.product_data)
                    await message.answer(text)
                except TypeError:
                    await message.answer('Отправьте картинку или пропустите - /pass')
        else:
            try:
                if message.text == '/pass':
                    phot = None
                    text = '✔️ Фото продукта удалено.'
                else:
                    phot = message.photo[-1].file_id
                    text = '✔️ Фото продукта успешно изменено.'
                db_sess = db_session.create_session()
                db_sess.query(Products).filter(Products.id == product_change_id).update(
                    {'image_path': phot})
                db_sess.commit()
                await message.answer(text)
                await state.clear()
                ProdChangePhoto = False
            except TypeError:
                await message.answer('Отправьте картинку или выйдите - /stop')
    elif message.text == '/stop':
        ProdChangePhoto = False
        await state.clear()  # Очищаем диалог, если отправлено /stop
        await message.answer('❗Отменено❗')


@router2.message(Form.product_data)  # Продолжаем диалог, чтобы редактировать продукты
async def dialog6(message: Message, state: FSMContext):
    global product_change_all, AddProdData
    if not message.text == '/stop':
        db_sess = db_session.create_session()
        if product_change_all:  # Если пользователь изменяет всё в продукте
            product_change_all = False
            all_data = await state.get_data()  # Получаем данные из состояния
            product_database = db_sess.query(Products).filter(Products.id == all_data['id'])
            count = product_database.first().count
            if message.text != '/pass':
                count += len(message.text.split('\n'))
                for dat in message.text.split('\n'):
                    prod_data = Data_Product(
                        product_id=all_data['id'],
                        data=dat
                    )
                    db_sess.add(prod_data)
            product_database.update({
                'name': all_data['name'],
                'price': all_data['price'],
                'count': count,
                'description': all_data['description'],
                'image_path': all_data['image_path']
            })
            db_sess.commit()
            await message.answer('Товар обновлён ✔️')
            await state.clear()
        else:
            if not AddProdData:
                all_data = await state.get_data()  # Получаем данные из состояния
                prod = Products(
                    categ_id=all_data['categ_id'],
                    name=all_data['name'],
                    price=all_data['price'],
                    count=len(message.text.split('\n')),
                    description=all_data['description'],
                    image_path=all_data['image_path']
                )
                db_sess.add(prod)
                db_sess.commit()
                for dat in message.text.split('\n'):
                    prod_data = Data_Product(
                        product_id=prod.id,
                        data=dat
                    )
                    db_sess.add(prod_data)
                db_sess.commit()
                await message.answer('Товар добавлен ✔️')
                await state.clear()
            else:
                AddProdData = False
                product_database = db_sess.query(Products).filter(Products.id == product_change_id)
                count = len(message.text.split('\n')) + product_database.first().count
                for dat in message.text.split('\n'):
                    prod_data = Data_Product(
                        product_id=product_change_id,
                        data=dat
                    )
                    db_sess.add(prod_data)
                product_database.update({'count': count})
                db_sess.commit()
                await message.answer('✔️ Новые данные успешно добавлены.')
                await state.clear()
    elif message.text == '/stop':
        product_change_all, AddProdData = False, False
        await state.clear()  # Очищаем диалог, если отправлено /stop
        await message.answer('❗Отменено❗')


# Команды изменения продукта -----------------------------------------------------------------------------
@router2.message(Command('change_product'))
async def change_product(message: Message, state: FSMContext):
    global product_add, product_change_all
    product_add, product_change_all = True, True
    await state.clear()
    await message.delete()
    await state.update_data(id=product_change_id)
    await state.set_state(Form.name)  # Начинаем диалог добавления продуктов, но мы просто изменим его
    await message.answer(text='При отмене, отправьте /stop\n\nНапишите новое название продукта:')


@router2.message(Command('change_name'))
async def change_name(message: Message, state: FSMContext):
    global ProdChangeName, product_add
    ProdChangeName, product_add = True, True
    await state.clear()
    await state.set_state(Form.name)
    await message.delete()
    await message.answer(text='При отмене, отправьте /stop\n\nНапишите новое название продукта:')


@router2.message(Command('change_price'))
async def change_name(message: Message, state: FSMContext):
    global ProdChangePrice
    ProdChangePrice = True
    await state.clear()
    await message.delete()
    await state.set_state(Form.price)
    await message.answer(text='При отмене, отправьте /stop\n\nНапишите новую цену продукта:')


@router2.message(Command('change_description'))
async def change_name(message: Message, state: FSMContext):
    global ProdChangeDescription
    ProdChangeDescription = True
    await state.clear()
    await message.delete()
    await state.set_state(Form.description)
    await message.answer(text='При отмене, отправьте /stop\nЧтобы удалить описание, отправьте /pass\n\n'
                              'Напишите новое описание продукта:')


@router2.message(Command('change_photo'))
async def change_name(message: Message, state: FSMContext):
    global ProdChangePhoto
    ProdChangePhoto = True
    await state.clear()
    await message.delete()
    await state.set_state(Form.image_path)
    await message.answer(text='При отмене, отправьте /stop\nЧтобы удалить фото, отправьте /pass\n\n'
                              'Скиньте новое фото продукта:')


@router2.message(Command('add_product_data'))
async def change_name(message: Message, state: FSMContext):
    global AddProdData
    AddProdData = True
    await state.clear()
    await message.delete()
    await state.set_state(Form.product_data)
    await message.answer(text='При отмене, отправьте /stop\n\nДобавьте ещё больше данных, '
                              'каждый с новой строчки, в виде:\n\nlogin:password\nlogin:password'
                              '\nlogin:password')


@router2.message(Command('redact_data'))
async def redact_data(message: Message):
    await message.delete()
    db_sess = db_session.create_session()
    items = db_sess.query(Data_Product).filter(Data_Product.product_id == data_callback[1]).all()
    await message.answer(text='❗Нажмите на данные, чтобы их сразу удалить❗\n (🟥 - не куплено | 🟩 - куплено)',
                         reply_markup=await kb.redactProductData(items))


# При оплате -------------------------------------------------------------------------------------------
async def payment(message):
    try:
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.user_tg_id == USER_ID)
        user_data = user.first()
        # Если реф. система включена и пользователь был кем то приглашён, то добавляем денег реферу
        if user_data.refer_id is not None and _REFERRAL_SYSTEM_["works"] == 'True':
            ref_user = db_sess.query(User).filter(User.user_tg_id == user_data.refer_id)
            _price_ = data_callback[3]
            if data_callback[3] == 'up_balance':
                _price_ = data_callback[2]
            percent_money = int(_REFERRAL_SYSTEM_["percent"] / 100 * int(_price_))
            ref_user.update({
                'balance': ref_user.first().balance + percent_money,
                'received_from_ref': ref_user.first().received_from_ref + percent_money
            })
        if data_callback[3] == 'up_balance':
            purchases_data = f'{int(data_callback[2])}|None|{datetime.now()};'
            if user_data.purchases is not None:
                purchases_data += user_data.purchases
            user.update({'balance': user_data.balance + int(data_callback[2]),
                         'all_money': user_data.all_money + int(data_callback[2]),
                         'purchases': purchases_data})
            db_sess.commit()
            return await message.answer(f'<b>💌 Спасибо за пополнение на {data_callback[2]}₽!</b>', parse_mode="HTML")
        else:
            # Меняем информацию, что продукт куплен и выдаём данные пользователю
            dat_prod = db_sess.query(Data_Product).filter(Data_Product.product_id == data_callback[3],
                                                          Data_Product.purchased == False).first()
            data_1 = dat_prod.data.split(':')
            try:
                text = f'<b>💌 Спасибо за покупку!</b>\n\n<i>Ваши данные:</i>\nlogin: {data_1[0]}\npassword: {data_1[1]}'
            except IndexError:
                text = f'<b>💌 Спасибо за покупку!</b>\n\n<i>Ваши данные:</i>\n{data_1[0]}'
            prod_1 = db_sess.query(Products).filter(Products.id == data_callback[3])
            prod_1.update({'count': prod_1.first().count - 1})  # Количество оставшихся данных
            db_sess.query(Data_Product).filter(Data_Product.id == dat_prod.id).update({'purchased': True})

            # Добавляем данные в покупки юзера
            purchases_data = f'{int(data_callback[2])}|{dat_prod.data}|{datetime.now()};'
            if user_data.purchases is not None:
                purchases_data += user_data.purchases
            user.update({'all_money': user_data.all_money + int(data_callback[2]),
                         'purchases': purchases_data})
            db_sess.commit()
            return await message.answer(text, parse_mode="HTML")
    except Exception as e:
        print(e)
        return await message.answer('❗Ошибка оплаты❗\nПожалуйста, напишите в поддержку 🥲')


# Telegram Stars
@router2.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router2.message(F.successful_payment)
async def success_payment_handler(message: Message):
    await payment(message)
