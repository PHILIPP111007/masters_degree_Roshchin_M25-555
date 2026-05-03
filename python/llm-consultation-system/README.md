# Двухсервисная система LLM-консультаций

Проект состоит из двух независимых сервисов:

- **Auth Service** (FastAPI) — регистрация, логин, выдача JWT
- **Bot Service** (aiogram + FastAPI) — Telegram-бот с LLM-консультациями

## Архитектура

- Auth Service **создаёт** JWT
- Bot Service **проверяет** JWT (без доступа к БД Auth Service)
- Запросы к LLM выполняются **асинхронно** через Celery + RabbitMQ
- Redis используется для хранения JWT и как result backend

## Запуск

```bash
docker-compose up -d
```
