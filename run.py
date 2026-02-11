# Aiogram
from aiogram import Dispatcher
# Others
from dotenv import load_dotenv
import os
import asyncio
from app.config.config import bot, update_env
# My files
from app.handlers import router
from app.handlers_2 import router2, cp
from data import db_session


dp = Dispatcher()  # Обрабатывает входящие обновления
load_dotenv()


async def main():
    # Подключаемся к бд
    try:
        db_session.global_init("db/shop.db")
        db_sess = db_session.create_session()
        db_sess.commit()
        dp.include_router(router)  # Диспетчер роутер в handlers
        dp.include_router(router2)  # Диспетчер роутер в handlers_2
        if os.getenv('CRYPTO_BOT_API') != '':
            try:
                await asyncio.gather(dp.start_polling(bot), cp.start_polling())
            except Exception:
                print('! Неправильный api ключ CryptoBot ! Запустите бота заново и добавьте верный api')
                await update_env('CRYPTO_BOT_API', '')
                print('RUN | Повторный запуск бота')
                await asyncio.gather(dp.start_polling(bot))
        else:
            await asyncio.gather(dp.start_polling(bot))
    except Exception as e:
        print(f'Ошибка!!!\n{e}')


if __name__ == '__main__':
    print('RUN | Бот работает')
    # logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('EXIT')


# pyinstaller --onefile run.py
