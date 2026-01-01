"""
Настройка логирования для ValutaTrade Hub
"""

import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path


def setup_logging(
    log_dir: str = "logs",
    log_level: str = "INFO",
    log_format: str = "json",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> None:
    """
    Настраивает систему логирования

    Args:
        log_dir: Директория для логов
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Формат логов ('json' или 'text')
        max_bytes: Максимальный размер файла лога
        backup_count: Количество файлов для ротации
    """
    # Создаем директорию для логов
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Устанавливаем уровень логирования
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Создаем форматтер
    if log_format.lower() == "json":
        formatter = JsonFormatter()
    else:
        formatter = TextFormatter()

    # Настраиваем обработчик для файла
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / "actions.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(numeric_level)

    # Настраиваем обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)

    # Получаем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Очищаем существующие обработчики
    root_logger.handlers.clear()

    # Добавляем обработчики
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Логируем начало работы
    logger = logging.getLogger(__name__)
    logger.info(
        "Логирование инициализировано",
        extra={
            "log_dir": str(log_path),
            "log_level": log_level,
            "log_format": log_format,
        },
    )


class JsonFormatter(logging.Formatter):
    """Форматтер для JSON логов"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Добавляем дополнительные поля
        if hasattr(record, "action"):
            log_data["action"] = record.action
        if hasattr(record, "username"):
            log_data["username"] = record.username
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "currency_code"):
            log_data["currency_code"] = record.currency_code
        if hasattr(record, "amount"):
            log_data["amount"] = record.amount
        if hasattr(record, "rate"):
            log_data["rate"] = record.rate
        if hasattr(record, "base"):
            log_data["base"] = record.base
        if hasattr(record, "result"):
            log_data["result"] = record.result
        if hasattr(record, "error_type"):
            log_data["error_type"] = record.error_type
        if hasattr(record, "error_message"):
            log_data["error_message"] = record.error_message

        # Добавляем поля из extra
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Форматтер для текстовых логов"""

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def format(self, record: logging.LogRecord) -> str:
        # Добавляем дополнительные поля к сообщению
        message = record.getMessage()

        extra_fields = []
        if hasattr(record, "action"):
            extra_fields.append(f"action={record.action}")
        if hasattr(record, "username"):
            extra_fields.append(f"user='{record.username}'")
        if hasattr(record, "currency_code"):
            extra_fields.append(f"currency='{record.currency_code}'")
        if hasattr(record, "amount"):
            extra_fields.append(f"amount={record.amount}")
        if hasattr(record, "rate"):
            extra_fields.append(f"rate={record.rate}")
        if hasattr(record, "base"):
            extra_fields.append(f"base='{record.base}'")
        if hasattr(record, "result"):
            extra_fields.append(f"result={record.result}")

        if extra_fields:
            message = f"{message} ({', '.join(extra_fields)})"

        record.msg = message
        return super().format(record)


def get_logger(name: str) -> logging.Logger:
    """
    Возвращает логгер с указанным именем

    Args:
        name: Имя логгера

    Returns:
        Объект логгера
    """
    return logging.getLogger(name)
