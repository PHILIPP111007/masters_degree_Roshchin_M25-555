import pytest
import respx
from httpx import Response

from app.services.openrouter_client import OpenRouterClient


@pytest.mark.asyncio
async def test_chat_completion_success():
    mock_response = {"choices": [{"message": {"content": "Привет! Чем могу помочь?"}}]}

    with respx.mock as mock:
        mock.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=Response(200, json=mock_response)
        )

        client = OpenRouterClient()
        result = await client.chat_completion("Привет")

        assert result == "Привет! Чем могу помочь?"
        assert mock.calls.call_count == 1


@pytest.mark.asyncio
async def test_chat_completion_error():
    with respx.mock as mock:
        mock.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=Response(500, text="Internal Server Error")
        )

        client = OpenRouterClient()
        with pytest.raises(RuntimeError, match="OpenRouter returned status 500"):
            await client.chat_completion("Привет")
