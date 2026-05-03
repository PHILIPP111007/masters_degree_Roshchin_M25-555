FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install uv
RUN uv pip compile pyproject.toml -o requirements.txt
RUN uv pip install --system -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]