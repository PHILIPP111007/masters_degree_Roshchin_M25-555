FROM python:3.11-slim

WORKDIR /app

COPY bot_service/pyproject.toml .
RUN pip install uv
RUN uv pip compile pyproject.toml -o requirements.txt
RUN uv pip install --system -r requirements.txt

COPY bot_service/app ./app

CMD ["celery", "-A", "app.infra.celery_app", "worker", "--loglevel=info"]