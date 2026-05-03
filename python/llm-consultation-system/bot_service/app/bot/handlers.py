from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.dispatcher import bot
from app.core.config import settings
from app.core.jwt import decode_and_validate
from app.infra.redis import get_redis

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "Привет! Я бот-консультант с LLM.\n\n"
        "Сначала зарегистрируйся в Auth Service и получи JWT-токен.\n"
        "Затем отправь мне токен командой:\n"
        "/token <ваш_jwt_токен>\n\n"
        "После этого можешь задавать мне любые вопросы!"
    )


@router.message(Command("token"))
async def token_handler(message: Message):
    tg_user_id = message.from_user.id
    parts = message.text.strip().split(maxsplit=1)

    if len(parts) < 2:
        await message.answer("❌ Укажи токен: /token <jwt>")
        return

    token = parts[1].strip()

    try:
        payload = decode_and_validate(token)
        redis = await get_redis()
        await redis.set(f"token:{tg_user_id}", token)
        await message.answer(
            f"✅ Токен принят и сохранён!\n"
            f"Пользователь ID: {payload['sub']}\n"
            f"Роль: {payload.get('role', 'unknown')}\n\n"
            f"Теперь можешь задавать вопросы."
        )
    except ValueError:
        await message.answer(
            "❌ Неверный или истёкший токен. Получи новый в Auth Service."
        )


@router.message(F.text)
async def text_handler(message: Message):
    tg_user_id = message.from_user.id
    tg_chat_id = message.chat.id

    redis = await get_redis()
    token = await redis.get(f"token:{tg_user_id}")

    if not token:
        await message.answer(
            "⛔ У тебя нет токена. Сначала зарегистрируйся в Auth Service "
            "и отправь токен командой /token <jwt>"
        )
        return

    try:
        decode_and_validate(token)
    except ValueError:
        await message.answer(
            "⛔ Твой токен недействителен или истёк. "
            "Получи новый в Auth Service и отправь командой /token <jwt>"
        )
        return

    from app.tasks.llm_tasks import llm_request

    llm_request.delay(
        tg_chat_id=tg_chat_id,
        prompt=message.text,
        bot_token=settings.telegram_bot_token,
    )

    await message.answer("⏳ Запрос принят, обрабатываю... Ожидай ответа.")
