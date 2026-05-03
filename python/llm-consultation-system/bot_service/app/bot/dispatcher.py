from aiogram import Bot, Dispatcher

from app.bot.handlers import router
from app.core.config import settings

bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher()
dp.include_router(router)
