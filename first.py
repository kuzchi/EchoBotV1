import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
import asyncpg
import os

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not API_TOKEN or API_TOKEN == "ВАШ_ТОКЕН_БОТА":
    raise ValueError("Переменная окружения TELEGRAM_BOT_TOKEN не установлена или содержит неверное значение!")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
async def create_db_pool():
    return await asyncpg.create_pool(**DB_CONFIG)
db_pool = None
async def start_command(message: Message):
    await message.answer("Привет! Я эхо-бот. Напишите мне что-нибудь или используйте команду /users, чтобы увидеть список пользователей в базе данных.")
async def get_users(message: Message):
    async with db_pool.acquire() as connection:
        rows = await connection.fetch("SELECT username, first_name, last_name FROM users")
        if rows:
            users_list = "\n".join([f"{row['username']} - {row['first_name']} {row['last_name']}" for row in rows])
            await message.answer(f"Список пользователей:\n{users_list}")
        else:
            await message.answer("В базе данных нет пользователей.")
async def echo_message(message: Message):
    await message.answer(message.text)
def register_handlers(dp: Dispatcher):
    dp.message.register(start_command, Command("start"))
    dp.message.register(get_users, Command("users"))
    dp.message.register(echo_message)
async def main():
    global db_pool
    db_pool = await create_db_pool()
    print("База данных подключена.")
    try:
        register_handlers(dp)  
        await bot.delete_webhook(drop_pending_updates=True)  #
        await dp.start_polling(bot)  
    finally:
        await bot.session.close()  
        await db_pool.close()  
if __name__ == "__main__":
    asyncio.run(main())
