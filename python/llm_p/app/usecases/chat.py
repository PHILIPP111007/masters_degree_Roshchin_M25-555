from app.repositories.chat_messages import ChatMessageRepository
from app.services.openrouter_client import OpenRouterClient


class ChatUseCase:
    def __init__(self, chat_repo: ChatMessageRepository, llm_client: OpenRouterClient):
        self._chat_repo = chat_repo
        self._llm_client = llm_client

    async def ask(
        self,
        user_id: int,
        prompt: str,
        system: str | None = None,
        max_history: int = 10,
        temperature: float = 0.7,
    ) -> str:
        # Build messages for LLM
        messages: list[dict] = []

        if system:
            messages.append({"role": "system", "content": system})

        # Get history
        history = await self._chat_repo.get_recent_messages(user_id, limit=max_history)
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})

        # Add current prompt
        messages.append({"role": "user", "content": prompt})

        # Save user message
        await self._chat_repo.add_message(user_id=user_id, role="user", content=prompt)

        # Get response from LLM
        answer = await self._llm_client.chat_completion(
            messages, temperature=temperature
        )

        # Save assistant message
        await self._chat_repo.add_message(
            user_id=user_id, role="assistant", content=answer
        )

        return answer

    async def get_history(self, user_id: int, limit: int = 50) -> list:
        messages = await self._chat_repo.get_recent_messages(user_id, limit=limit)
        return messages

    async def clear_history(self, user_id: int) -> None:
        await self._chat_repo.delete_all_for_user(user_id)
