from unittest.mock import AsyncMock, patch

import pytest
from aiogram.types import Message, User, Chat

from app.bot.handlers import text_handler, token_handler


def make_message(text: str, user_id: int = 123, chat_id: int = 456) -> Message:
    return Message(
        message_id=1,
        date=None,
        chat=Chat(id=chat_id, type="private"),
        from_user=User(id=user_id, is_bot=False, first_name="Test"),
        text=text,
    )


@pytest.mark.asyncio
async def test_token_handler_saves_token(mock_get_redis, fake_redis):
    from app.core.config import settings
    from jose import jwt
    import time

    token = jwt.encode(
        {"sub": "42", "role": "user", "exp": int(time.time()) + 3600},
        settings.jwt_secret,
        algorithm=settings.jwt_alg,
    )

    msg = make_message(f"/token {token}")
    msg.answer = AsyncMock()

    await token_handler(msg)

    msg.answer.assert_called_once()
    call_text = msg.answer.call_args[0][0]
    assert "✅" in call_text

    saved_token = await fake_redis.get(f"token:{msg.from_user.id}")
    assert saved_token == token


@pytest.mark.asyncio
async def test_token_handler_invalid_token(mock_get_redis):
    msg = make_message("/token garbage_token")
    msg.answer = AsyncMock()

    await token_handler(msg)

    msg.answer.assert_called_once()
    call_text = msg.answer.call_args[0][0]
    assert "❌" in call_text


@pytest.mark.asyncio
async def test_text_handler_no_token(mock_get_redis):
    msg = make_message("Как дела?")
    msg.answer = AsyncMock()

    await text_handler(msg)

    msg.answer.assert_called_once()
    call_text = msg.answer.call_args[0][0]
    assert "⛔" in call_text


@pytest.mark.asyncio
async def test_text_handler_with_token(mock_get_redis, fake_redis):
    import time
    from jose import jwt
    from app.core.config import settings

    token = jwt.encode(
        {"sub": "42", "role": "user", "exp": int(time.time()) + 3600},
        settings.jwt_secret,
        algorithm=settings.jwt_alg,
    )
    await fake_redis.set("token:123", token)

    msg = make_message("Привет, LLM!")
    msg.answer = AsyncMock()

    with patch("app.bot.handlers.llm_request") as mock_llm_request:
        mock_llm_request.delay = AsyncMock()
        await text_handler(msg)

        msg.answer.assert_called_once()
        call_text = msg.answer.call_args[0][0]
        assert "⏳" in call_text

        mock_llm_request.delay.assert_called_once_with(
            tg_chat_id=msg.chat.id,
            prompt="Привет, LLM!",
            bot_token=settings.telegram_bot_token,
        )
