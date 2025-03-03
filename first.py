import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiohttp import web
import asyncpg
import json


with open("dbconfig.json", "r") as config_file:
    config = json.load(config_file)

API_TOKEN = config.get("telegram_bot_token")
if not API_TOKEN:
    raise ValueError("Токен бота не указан в конфигурации")

DB_CONFIG = config.get("db_config")
if not DB_CONFIG:
    raise ValueError("Нет конфигурации базы данных")

# Настройки вебхука
WEBHOOK_HOST = "https://webhook.site/c845b68e-93cb-4b72-aefe-add803390659"  
WEBHOOK_PATH = ""  
WEBHOOK_URL = WEBHOOK_HOST  

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


async def create_db_pool():
    return await asyncpg.create_pool(**DB_CONFIG)

db_pool = None

# Обработчики команд
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

async def handle_webhook(request):
    update = await request.json()
    await dp.feed_update(bot, update)
    return web.Response()

async def main():
    global db_pool
    db_pool = await create_db_pool()
    print("База данных подключена.")

    await bot.set_webhook(WEBHOOK_URL)
    print(f"Вебхук установлен на {WEBHOOK_URL}")

    register_handlers(dp)

    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=8080)  
    await site.start()

    print(f"Сервер запущен и слушает порт 8080")

    try:
        while True:
            await asyncio.sleep(3600)  
    finally:
        await bot.session.close()
        await db_pool.close()

if __name__ == "__main__":
    asyncio.run(main())
