# вспомогательные функции
"""
Вспомогательные функции для ValutaTrade Hub
"""

import re
import string
import secrets
import hashlib
from typing import Optional, Tuple
from datetime import datetime, timedelta


def validate_currency_code(code: str) -> Tuple[bool, Optional[str]]:
    """
    Валидация кода валюты

    Args:
        code: Код валюты для проверки

    Returns:
        Кортеж (валиден_ли, сообщение_об_ошибке)
    """
    if not isinstance(code, str):
        return False, "Код валюты должен быть строкой"

    code = code.strip().upper()

    if not code:
        return False, "Код валюты не может быть пустым"

    if len(code) < 2 or len(code) > 5:
        return False, "Код валюты должен содержать от 2 до 5 символов"

    if not re.match(r"^[A-Z0-9]+$", code):
        return False, "Код валюты должен содержать только буквы и цифры"

    return True, None


def validate_amount(amount: float) -> Tuple[bool, Optional[str]]:
    """
    Валидация суммы

    Args:
        amount: Сумма для проверки

    Returns:
        Кортеж (валиден_ли, сообщение_об_ошибке)
    """
    if not isinstance(amount, (int, float)):
        return False, "Сумма должна быть числом"

    if amount <= 0:
        return False, "Сумма должна быть положительным числом"

    if amount > 1_000_000_000:  # 1 миллиард
        return False, "Сумма слишком большая"

    return True, None


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Валидация имени пользователя

    Args:
        username: Имя пользователя для проверки

    Returns:
        Кортеж (валиден_ли, сообщение_об_ошибке)
    """
    if not isinstance(username, str):
        return False, "Имя пользователя должно быть строкой"

    username = username.strip()

    if not username:
        return False, "Имя пользователя не может быть пустым"

    if len(username) < 3:
        return False, "Имя пользователя должно содержать минимум 3 символа"

    if len(username) > 50:
        return False, "Имя пользователя слишком длинное"

    if not re.match(r"^[a-zA-Z0-9_\-\.]+$", username):
        return (
            False,
            "Имя пользователя может содержать только буквы, цифры, точку, дефис и подчеркивание",
        )

    return True, None


def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """
    Валидация пароля

    Args:
        password: Пароль для проверки

    Returns:
        Кортеж (валиден_ли, сообщение_об_ошибке)
    """
    if not isinstance(password, str):
        return False, "Пароль должен быть строкой"

    if len(password) < 4:
        return False, "Пароль должен содержать минимум 4 символа"

    if len(password) > 100:
        return False, "Пароль слишком длинный"

    return True, None


def generate_salt(length: int = 16) -> str:
    """
    Генерация соли для хеширования пароля

    Args:
        length: Длина соли

    Returns:
        Соль
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def hash_password(password: str, salt: str) -> str:
    """
    Хеширование пароля с солью

    Args:
        password: Пароль
        salt: Соль

    Returns:
        Хешированный пароль
    """
    return hashlib.sha256((password + salt).encode()).hexdigest()


def format_currency_amount(amount: float, currency_code: str) -> str:
    """
    Форматирование суммы валюты

    Args:
        amount: Сумма
        currency_code: Код валюты

    Returns:
        Отформатированная строка
    """
    # Определяем количество знаков после запятой в зависимости от валюты
    if currency_code in ["JPY", "KRW", "VND"]:
        # Валюты без копеек
        return f"{amount:,.0f} {currency_code}"
    elif currency_code in ["BTC", "ETH", "XRP"]:
        # Криптовалюты - больше знаков после запятой
        return f"{amount:,.8f} {currency_code}"
    else:
        # Обычные валюты - 2 знака после запятой
        return f"{amount:,.2f} {currency_code}"


def calculate_converted_amount(
    amount: float, from_currency: str, to_currency: str, exchange_rate: float
) -> float:
    """
    Расчет конвертированной суммы

    Args:
        amount: Исходная сумма
        from_currency: Исходная валюта
        to_currency: Целевая валюта
        exchange_rate: Курс обмена

    Returns:
        Конвертированная сумма
    """
    return amount * exchange_rate


def is_data_fresh(updated_at: datetime, ttl_seconds: int) -> bool:
    """
    Проверка свежести данных

    Args:
        updated_at: Время последнего обновления
        ttl_seconds: Время жизни данных в секундах

    Returns:
        True если данные свежие, иначе False
    """
    if not updated_at:
        return False

    return datetime.now() - updated_at < timedelta(seconds=ttl_seconds)
