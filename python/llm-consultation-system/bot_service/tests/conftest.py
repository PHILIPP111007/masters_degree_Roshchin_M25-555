import asyncio
from unittest.mock import AsyncMock, patch

import pytest
import fakeredis.aioredis


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def fake_redis():
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture
def mock_get_redis(fake_redis):
    async def _get_redis():
        return fake_redis

    with patch("app.bot.handlers.get_redis", side_effect=_get_redis):
        yield
