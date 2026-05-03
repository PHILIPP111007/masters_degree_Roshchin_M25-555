from app.infra.celery_app import celery_app
from app.services.openrouter_client import OpenRouterClient


@celery_app.task(name="llm_request", bind=True, max_retries=3)
def llm_request(self, tg_chat_id: int, prompt: str, bot_token: str):
    import asyncio

    from aiogram import Bot

    async def _process():
        client = OpenRouterClient()
        try:
            answer = await client.chat_completion(prompt)
            bot = Bot(token=bot_token)
            await bot.send_message(
                chat_id=tg_chat_id,
                text=f"Ответ LLM:\n\n{answer}",
            )
            await bot.session.close()
        except Exception as e:
            raise self.retry(exc=e, countdown=10)

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_process())
    finally:
        loop.close()

    return {"status": "ok", "chat_id": tg_chat_id}
