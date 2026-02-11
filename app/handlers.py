# Хэндлеры пользователя #
# Aiogram
import datetime

from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import Message, CallbackQuery, FSInputFile

from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
# My files
import app.keyboards as kb
from data import db_session
from data.users import User
from data.categories import Categories
from data.products import Products
from app.config import config
# Others
from dotenv import load_dotenv
import os

load_dotenv()

router = Router()
bot = config.bot

_PAYMENT_METHODS_ = config._PAYMENT_METHODS_


class Main_Form(StatesGroup):  # Форма для диалога
    first = State()
    second = State()
    third = State()


# Флажки для диалогов
UP_BALANCE, LOOK_USER_DATA, PAY_HIM, CHANGE_HIM = False, False, False, False
ADMIN_MAILING, mailing_text, CHANGE_HELP_LOGIN, ADD_ADMIN = False, '', False, False


@router.message(CommandStart())  # /start
async def cmd_start(message: Message, command: CommandObject):
    args = command.args  # Если пользователь перешёл по реф-ой ссылке
    if config.MAIN_CHANNEL == 'False' or await config.is_user_subscribed(message.from_user.id):
        await message.answer(text=f'👋 Привет @{message.from_user.username}! Добро пожаловать в наш магазин!',
                             reply_markup=kb.main)
    else:
        await message.answer("🙏 Пожалуйста, подпишитесь на наш канал, чтобы использовать бота",
                             reply_markup=await kb.channel())
    # Если пользователь впервые зашёл в бота, то добавляем его в бд
    db_sess = db_session.create_session()
    _user_ = db_sess.query(User).filter(User.user_tg_id == message.from_user.id).first()
    if not _user_:
        user = User(
            user_tg_id=message.from_user.id,
            user_login=message.from_user.username,
            refer_id=args
        )
        db_sess.add(user)
        if args is not None:
            refer_user = db_sess.query(User).filter(User.user_tg_id == args)
            refer_user.update({'count_refer': refer_user.first().count_refer + 1})
            await bot.send_message(args, '+1 пользователь по реферальной ссылке! 🎉')
    else:
        if _user_.user_login != message.from_user.username:
            db_sess.query(User).filter(User.user_tg_id == message.from_user.id).update({
                'user_login': message.from_user.username})
    db_sess.commit()
    if str(message.from_user.id) in config.ADMINS_ID:
        await message.answer(text='🕶️ Админ панель', reply_markup=kb.main_admin)
        if os.getenv('ADMIN_USERNAME_LINK') == 't.me/':
            await config.update_env('ADMIN_USERNAME_LINK', f't.me/{message.from_user.username}')


@router.message(F.text == '🔙 На главную')  # Главная | admin
async def back_admin(message: Message):
    if str(message.from_user.id) in config.ADMINS_ID:
        await message.delete()
        await message.answer(text='🕶️ Главная', reply_markup=kb.main_admin)


@router.message(F.text == '👥 Пользователи')  # Панель пользователей | admin
async def user_admin(message: Message):
    if str(message.from_user.id) in config.ADMINS_ID:
        await message.delete()
        await message.answer(text='💥 Выберите нужную функцию', reply_markup=kb.users_admin)


@router.message(F.text == '📦 Получить БД')  # admin
async def get_database(message: Message):
    if str(message.from_user.id) in config.ADMINS_ID:
        await message.delete()
        await message.answer_document(
            FSInputFile(config.PATH_DATABASE), parse_mode='HTML',
            caption=f'Изменить бд: /changeDB \n\n'
                    f'📦 База данных \n<b>#DB | <i>{datetime.datetime.now().strftime("%d.%m.%Y")}</i></b>')


@router.message(Command('changeDB'))  # admin
async def change_database(message: Message, state: FSMContext):
    if str(message.from_user.id) in config.ADMINS_ID:
        await message.delete()
        await state.clear()
        await state.set_state(Main_Form.third)
        await message.answer(text='❌ - /stop\n📦 Отправьте новый файл с расширением db:')


@router.callback_query(F.data == 'back_delete')  # Кнопка 'Закрыть'
async def back(callback: CallbackQuery, state: FSMContext):
    global PAY_HIM, UP_BALANCE, CHANGE_HIM, LOOK_USER_DATA
    await state.clear()
    PAY_HIM, UP_BALANCE, CHANGE_HIM, LOOK_USER_DATA = False, False, False, False
    await callback.message.delete()


@router.message(F.text == 'Купить 🚀')  # Купить товары
async def buy(message: Message):
    if config.MAIN_CHANNEL == 'False' or await config.is_user_subscribed(message.from_user.id):
        db_sess = db_session.create_session()
        data = db_sess.query(Categories).all()
        await message.delete()
        if data:
            await message.answer('🧨 Каталог', reply_markup=await kb.categories_kb(data))
        else:
            await message.answer('🧨 Каталогов не существует')
    else:
        await message.answer("🙏 Пожалуйста, подпишитесь на наш канал, чтобы использовать бота",
                             reply_markup=await kb.channel())


@router.callback_query(F.data == 'buy')  # Купить товары | callback
async def buy2(callback: CallbackQuery):
    db_sess = db_session.create_session()
    data = db_sess.query(Categories).all()
    await callback.message.edit_text('🧨 Каталог', reply_markup=await kb.categories_kb(data))


@router.message(F.text == 'Поддержка 🆘')  # Поддержка
async def help1(message: Message):
    if config.MAIN_CHANNEL == 'False' or await config.is_user_subscribed(message.from_user.id):
        await message.delete()
        await message.answer('🆘 Для получение поддержки, нажмите кнопку ниже', reply_markup=await kb.help_())
    else:
        await message.answer("🙏 Пожалуйста, подпишитесь на наш канал, чтобы использовать бота",
                             reply_markup=await kb.channel())


@router.callback_query(F.data == 'up_balance')
async def up_balance(callback: CallbackQuery, state: FSMContext):
    global UP_BALANCE
    UP_BALANCE = True
    await state.clear()
    await callback.answer('')
    await state.set_state(Main_Form.first)
    await callback.message.answer('💌 Напишите сумму, на которую вы хотите пополнить баланс:', reply_markup=kb.close)


@router.message(F.text == '🪪 Данные пользователя')  # Посмотреть данные о пользователе | admin
async def user_data_(message: Message, state: FSMContext):
    global LOOK_USER_DATA
    if str(message.from_user.id) in config.ADMINS_ID:
        await message.delete()
        LOOK_USER_DATA = True
        await state.clear()
        await state.set_state(Main_Form.first)
        await message.answer(f'===При отмене, нажмите /stop===\n🪪 Отправьте ID или Логин пользователя:')


@router.message(F.text == '📊 Статистика')  # Посмотреть данные о пользователе | admin
async def user_data_(message: Message, state: FSMContext):
    if str(message.from_user.id) in config.ADMINS_ID:
        await message.delete()
        await state.clear()
        msg = await message.answer(text='⏱️ Идёт подсчёт...')
        users_by_day, users_by_week = 0, 0
        users_balance, users_all_money = 0, 0
        sales_by_day, sales_by_week, sales_all_time, day_count1, week_count1, all_time_count1 = 0, 0, 0, 0, 0, 0
        donate_by_day, donate_by_week, donate_all_time, day_count2, week_count2, all_time_count2 = 0, 0, 0, 0, 0, 0

        _date_ = datetime.datetime.now()
        db_sess = db_session.create_session()
        all_users = db_sess.query(User)
        for user in all_users.all():
            time_difference1 = _date_ - user.modified_date
            if time_difference1.days < 1:
                users_by_day += 1
            if time_difference1.days < 7:
                users_by_week += 1
            users_balance += user.balance
            users_all_money += user.all_money

            if user.purchases is not None:
                try:
                    for user_purchase in user.purchases.split(';'):
                        purchase = user_purchase.split('|')
                        time_difference2 = _date_ - datetime.datetime.strptime(purchase[2], '%Y-%m-%d %H:%M:%S.%f')
                        if purchase[1] == 'None':  # Если пополнение баланса
                            donate_all_time += 1
                            all_time_count2 += int(purchase[0])
                            if time_difference2.days < 1:
                                donate_by_day += 1
                                day_count2 += int(purchase[0])
                            if time_difference2.days < 7:
                                donate_by_week += 1
                                week_count2 += int(purchase[0])
                        else:  # Если покупка товара
                            sales_all_time += 1
                            all_time_count1 += int(purchase[0])
                            if time_difference2.days < 1:
                                sales_by_day += 1
                                day_count1 += int(purchase[0])
                            if time_difference2.days < 7:
                                sales_by_week += 1
                                week_count1 += int(purchase[0])
                except Exception:
                    pass

        text = (f'📊 Статистика\n\n👥 <b>Пользователи:</b>\n👥За день: {users_by_day}\n👥За неделю: '
                f'{users_by_week}\n👥За всё время: {all_users.count()}\n\n👥Сумма всех балансов: {users_balance}₽\n'
                f'👥Баланс за всё время: {users_all_money}₽\n\n💸 <b>Продажи:</b>\n\n💸За день: {sales_by_day} '
                f'({day_count1}₽)\n💸За неделю: {sales_by_week} ({week_count1}₽)\n💸За всё время: {sales_all_time} '
                f'({all_time_count1}₽)\n\n💰 <b>Пополнения:</b>\n\n💰За день: {donate_by_day} ({day_count2}₽)\n'
                f'💰За неделю: {donate_by_week}({week_count2}₽)\n💰За всё время: {donate_all_time} '
                f'({all_time_count2}₽)')
        await bot.edit_message_text(text=text, parse_mode='HTML', chat_id=message.chat.id, message_id=msg.message_id)


@router.callback_query(F.data == 'payhim')  # Пополнить баланс другому пользователю | admin
async def pay_him(callback: CallbackQuery, state: FSMContext):
    global PAY_HIM
    PAY_HIM = True
    await state.clear()
    await callback.answer('')
    await state.set_state(Main_Form.first)
    await callback.message.answer(f'===При отмене, нажмите /stop===\n'
                                  f'🫰 На какую сумму вы хотите пополнить баланс пользователя?')
    await state.update_data(USER_ID=USER_ID_PROFILE)


@router.callback_query(F.data == 'change_user_balance')  # Изменить баланс другому пользователю | admin
async def pay_him(callback: CallbackQuery, state: FSMContext):
    global CHANGE_HIM
    CHANGE_HIM = True
    await state.clear()
    await callback.answer('')
    await state.set_state(Main_Form.first)
    await callback.message.answer(f'===При отмене, нажмите /stop===\n🫰 На какую сумму вы хотите уменьшить баланс '
                                  f'пользователя? (Нельзя сделать баланс в минус)')
    await state.update_data(USER_ID=USER_ID_PROFILE)


@router.message(F.text == '⚙️ Настройки')
async def setting_admin(message: Message, state: FSMContext):
    if str(message.from_user.id) in config.ADMINS_ID:
        await message.delete()
        await state.clear()
        await message.answer('⚙️ Настройки бота.', reply_markup=kb.admin_settings)


@router.message(F.text == '👑 Админы')  # admins
async def bot_admins1(message: Message, state: FSMContext):
    if str(message.from_user.id) in config.ADMINS_ID:
        await message.delete()
        await state.clear()
        db_sess = db_session.create_session()
        text = '<b>🟰🟰🟰Админы🟰🟰🟰</b>\n\n'
        for admin_id in config.ADMINS_ID:
            try:
                text += (f'◾ <code>{admin_id}</code> '
                         f'@{db_sess.query(User).filter(User.user_tg_id == admin_id).first().user_login}\n')
            except AttributeError:
                text += f'◾ <code>{admin_id}</code> '
        text += f'\n🆘 Ссылка на админа в поддержке: {config._HELP_ADMIN_}'
        await message.answer(text, reply_markup=kb.bot_admins_kb, parse_mode='HTML')


@router.message(F.text == '💫 Главный канал')  # Главная | admin
async def main_channel(message: Message, state: FSMContext):
    if str(message.from_user.id) in config.ADMINS_ID:
        await message.delete()
        await state.clear()
        text = ('<i>📖 Вы можете отключить и включить функцию, которая проверяет, чтобы пользователь был подписан на '
                'канал. Так же не забудьте добавить бота в канал.</i>\n\n')
        if config.CHANNEL_ID.replace('@', '') == '':
            text += 'Канал ещё не добавлен ❌'
        else:
            text += f'🏹 Канал: <b>{config.CHANNEL_ID}</b>'
        await message.answer(text=text, reply_markup=await kb.changeMainChannel(config.MAIN_CHANNEL), parse_mode='HTML')


@router.callback_query(F.data == 'RedactMainChannel')  # Редактировать главный канал
async def redact_main_channel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Main_Form.second)
    await callback.answer('')
    await callback.message.answer(text='❌ - /stop\n✏️ Отправьте логин группы:')


@router.callback_query(F.data == 'change_help_login')  # Поменять логин в поддержке
async def change_help_login(callback: CallbackQuery, state: FSMContext):
    global CHANGE_HELP_LOGIN
    CHANGE_HELP_LOGIN = True
    await state.clear()
    await state.set_state(Main_Form.first)
    await callback.answer('')
    await callback.message.answer(f'❌ При отмене, отправьте /stop\n\n📧 Отправьте новый логин, на который '
                                  f'пользователи будут писать в поддержку. Формат: @adminlogin')


@router.callback_query(F.data == 'add_admin')  # Добавить нового админа
async def add_admin_1(callback: CallbackQuery, state: FSMContext):
    global ADD_ADMIN
    ADD_ADMIN = True
    await state.clear()
    await state.set_state(Main_Form.first)
    await callback.answer('')
    await callback.message.answer('❌ При отмене, отправьте /stop\n\n📧 Отправьте id нового админа.')


@router.callback_query(F.data == 'delete_admin')  # Удалить админа
async def add_admin_1(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.answer('📛 Какого админа удалить?', reply_markup=await kb.delete_admin(config.ADMINS_ID))


@router.message(F.text == '✉️ Рассылка')  # Рассылка сообщений | admin
async def emailing1(message: Message, state: FSMContext):
    global ADMIN_MAILING
    if str(message.from_user.id) in config.ADMINS_ID:
        ADMIN_MAILING = True
        await message.delete()
        await state.clear()
        await state.set_state(Main_Form.first)
        await message.answer(f'===При отмене, нажмите /stop===\n📨 Напишите сообщение, которое будет отправлено '
                             f'всем пользователям. Можно использовать HTML разметку.')


@router.callback_query(F.data == 'mailing_true')  # Рассылка | admin
async def emailing2(callback: CallbackQuery):
    await callback.message.edit_text('📨 Рассылка началась...')
    db_sess = db_session.create_session()
    users_block, users_receive = 0, 0
    for _user_ in db_sess.query(User).all():
        try:
            await bot.send_message(_user_.user_tg_id, mailing_text, parse_mode='HTML')
            users_receive += 1
        except:
            users_block += 1
    await callback.message.edit_text(f'📨 Рассылка закончена.\n\n✅Пользователей получило сообщение: {users_receive}\n'
                                     f'❌Пользователей не получило сообщение: {users_block}')


@router.callback_query(F.data == 'mailing_false')  # Рассылка | admin
async def pay_him(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.answer('📨 Рассылка отменена.')


@router.message(F.text == '📚 Изменить категории')  # Изменять удалять категории
async def change_categories(message: Message, state: FSMContext):
    if str(message.from_user.id) in config.ADMINS_ID:
        await state.clear()
        await message.delete()
        db_sess = db_session.create_session()
        await message.answer('↩️ - изменить | ❌ - удалить',
                             reply_markup=await kb.admin_categories(db_sess.query(Categories).all()))


@router.message(F.text == '💳 Способы оплаты')  # Настраивать методы оплаты
async def payment_methods(message: Message, state: FSMContext):
    if str(message.from_user.id) in config.ADMINS_ID:
        await state.clear()
        await message.delete()
        await message.answer('📖 Вы можете отключать и включать нужный вам способ оплаты\n(✅ - включено | ❌ - '
                             'выключено) и изменить API ключ 📝',
                             reply_markup=await kb.payment_methods_kb(_PAYMENT_METHODS_))
        # Дальше вызывается callback - *payment_method2*


@router.message(F.text == '🥖 Товары')
async def show_all_products(message: Message, state: FSMContext):
    if str(message.from_user.id) in config.ADMINS_ID:
        await message.delete()
        await state.clear()
        db_sess = db_session.create_session()
        categories_ = db_sess.query(Categories).all()
        text = ''
        for category_ in categories_:
            text += f'<b>➖➖➖{category_.category}➖➖➖</b>'
            prods = db_sess.query(Products).filter(Products.categ_id == category_.id).all()
            for prod in prods:
                text += f'\n   (<b>{prod.count}шт</b>) {prod.name} - {prod.price}₽'
            text += '\n\n'
        if text == '':
            text += '🥖 Товаров нет'
        await message.answer(text=text, parse_mode='HTML', reply_markup=kb.close)


@router.message(Main_Form.first)
async def amount(message: Message, state: FSMContext):
    global UP_BALANCE, PAY_HIM, LOOK_USER_DATA, USER_ID_PROFILE, CHANGE_HIM, ADMIN_MAILING, mailing_text, \
        CHANGE_HELP_LOGIN, ADD_ADMIN
    if message.text == '/stop':
        UP_BALANCE, LOOK_USER_DATA, PAY_HIM, CHANGE_HIM, ADMIN_MAILING = False, False, False, False, False
        CHANGE_HELP_LOGIN, ADD_ADMIN = False, False
        await message.answer('❗Отменено❗')
        await state.clear()
    elif ADMIN_MAILING:
        ADMIN_MAILING = False
        await state.clear()
        mailing_text = message.text
        db_sess = db_session.create_session()
        await message.answer(f'📨 Отправить сообщение {db_sess.query(User).count()} пользователям?',
                             reply_markup=kb.admin_mailing_conf)
        # Дальше callback-и mailing_true, mailing_false
    elif LOOK_USER_DATA:  # Посмотреть данные о пользователе
        db_sess = db_session.create_session()
        if message.text.isdigit():
            user_ = db_sess.query(User).filter(User.user_tg_id == int(message.text)).first()
        else:
            user_ = db_sess.query(User).filter(User.user_login == message.text.replace('@', '')).first()
        if not user_:
            await message.answer('❌ Пользователь не найден - /stop\n🔍 Отправьте id/login повторно')
        else:
            USER_ID_PROFILE = user_.user_tg_id
            text = (
                f'🪪 Пользователь <code><b>{user_.user_tg_id}</b></code>.\n◾Логин: @{user_.user_login}\n◾Баланс: '
                f'<b>{user_.balance}₽</b> \n◾Всего вложено: <b>{user_.all_money}₽</b>\n◾Первый запуск бота: '
                f'{str(user_.modified_date).split()[0]}\n◾Приглашено по реферальной ссылке: {user_.count_refer}\n\n')

            await message.answer(text, parse_mode='HTML', reply_markup=await kb.user_profile_data(
                user_.user_tg_id))
            await state.clear()
            LOOK_USER_DATA = False
    elif PAY_HIM:  # Пополнить баланс другому пользователю
        PAY_HIM = False
        db_sess = db_session.create_session()
        all_data = await state.get_data()  # Получаем данные из состояния
        user_ = db_sess.query(User).filter(User.user_tg_id == all_data['USER_ID'])
        user_.update({'balance': user_.first().balance + int(message.text),
                      'all_money': user_.first().all_money + int(message.text)})
        db_sess.commit()
        user_ = user_.first()
        await bot.send_message(user_.user_tg_id, f'💸 Ваш баланс пополнен на {message.text}₽!')
        await message.answer(
            f'🪪 Пользователь <b>{user_.user_tg_id}</b>.\n◾Логин: @{user_.user_login}\n◾Баланс: <b>{user_.balance}'
            f'₽</b>\n◾Всего вложено: <b>{user_.all_money}₽</b>\n◾Первый запуск бота: '
            f'{str(user_.modified_date).split()[0]}\n◾Приглашено по реферальной ссылке: {user_.count_refer}',
            parse_mode='HTML',
            reply_markup=await kb.user_profile_data(user_.user_tg_id))
        await state.clear()
    elif CHANGE_HIM:  # Уменьшить баланс другому пользователю
        db_sess = db_session.create_session()
        all_data = await state.get_data()  # Получаем данные из состояния
        user_ = db_sess.query(User).filter(User.user_tg_id == all_data['USER_ID'])
        if user_.first().balance - int(message.text) < 0:
            await message.answer(f'❌ - /stop\nБаланс будет меньше нуля, введите другую сумму.')
        else:
            CHANGE_HIM = False
            user_.update({'balance': user_.first().balance - int(message.text),
                          'all_money': user_.first().all_money - int(message.text)})
            db_sess.commit()
            user_ = user_.first()
            await bot.send_message(user_.user_tg_id, f'Ваш баланс уменьшен на {message.text}₽')
            await message.answer(
                f'◾🪪 Пользователь <b>{user_.user_tg_id}</b>.\n◾Логин: @{user_.user_login}\n◾Баланс: '
                f'<b>{user_.balance}₽</b>\n◾Всего вложено: <b>{user_.all_money}₽</b>\n◾Первый запуск бота: '
                f'{str(user_.modified_date).split()[0]}\n◾Приглашено по реферальной ссылке: {user_.count_refer}',
                parse_mode='HTML', reply_markup=await kb.user_profile_data(user_.user_tg_id))
        await state.clear()
    elif CHANGE_HELP_LOGIN:
        CHANGE_HELP_LOGIN = False
        await config.change_help_admin(message.text)
        await message.answer(f'✅ Ссылка изменена на: {config._HELP_ADMIN_}')
        await state.clear()
    elif not message.text.isdigit():
        await message.answer('❌ - /stop\n❕Введите число❕')
    else:
        if UP_BALANCE:
            if int(message.text) < 30:
                await message.answer('Укажите сумму больше 30₽')
            else:
                UP_BALANCE = False
                await state.clear()
                await message.answer('Выберите способ пополнения:',
                                     reply_markup=await kb.payment_method1(methods=_PAYMENT_METHODS_,
                                                                           up_balance=message.text))
        elif ADD_ADMIN:
            ADD_ADMIN = False
            await config.change_admins(new_admin=int(message.text))
            await message.answer(f'🎉 Новый админ <code>{message.text}</code> добавлен!', parse_mode='HTML')
            await state.clear()


@router.message(Main_Form.second)
async def amount(message: Message, state: FSMContext):
    if message.text == '/stop':
        await state.clear()
        await message.answer('❗Отменено❗')
    else:
        await state.clear()
        channel = message.text.replace("@", "")
        await config.changeChannelID(f'@{channel}')
        await config.update_env('CHANNEL_ID', f'@{channel}')
        await message.answer(f'🏹 Новый канал: <b>@{channel}</b>\nСсылка: https://t.me/{channel}', parse_mode='HTML')


@router.message(Main_Form.third)
async def amount(message: Message, state: FSMContext):
    if message.text == '/stop':
        await message.answer('❗Отменено❗')
        await state.clear()
    else:
        document = message.document
        new_file = await bot.get_file(document.file_id)
        if document.file_name != 'shop.db':
            try:
                newdb_oslist = os.listdir('db/newdb/')
                if newdb_oslist != []:
                    await bot.send_document(message.chat.id, FSInputFile(f'db/newdb/{newdb_oslist[0]}'),
                                            caption="Отправьте данную вашу базу данных с названием "
                                                    "<code>shop.db</code> 😊", parse_mode='HTML')
                    os.remove('db/newdb/shop.db')
                else:
                    newdbpath = f'db/newdb/{document.file_name}'
                    await bot.download_file(new_file.file_path, newdbpath)
                    os.rename(newdbpath, 'db/newdb/shop.db')
                    await bot.send_document(message.chat.id, FSInputFile(f'db/newdb/shop.db'),
                                            caption="Отправьте данную вашу базу данных с названием "
                                                    "<code>shop.db</code> 😊", parse_mode='HTML')
                    # Удаление файла после отправки (если это нужно)
                    os.remove('db/newdb/shop.db')
            except Exception:
                await message.answer('😔 Ошибка.\nПопробуйте подождать и отправить файл заново или измените '
                                     'название файла на: <code>shop.db</code>', parse_mode='HTML')
        else:
            await bot.download_file(new_file.file_path, 'db/shop.db')
            await message.answer('🔥 База данных успешно обновлена!')
            await state.clear()
