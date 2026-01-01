"""
Пользовательские исключения для ValutaTrade Hub
"""


class ValutaTradeError(Exception):
    """Базовое исключение для ValutaTrade Hub"""

    pass


class InsufficientFundsError(ValutaTradeError):
    """Недостаточно средств"""

    def __init__(self, currency_code: str, available: float, required: float):
        super().__init__(
            f"Недостаточно средств: доступно {available:.6f} {currency_code}, "
            f"требуется {required:.6f} {currency_code}"
        )
        self.currency_code = currency_code
        self.available = available
        self.required = required


class CurrencyNotFoundError(ValutaTradeError):
    """Неизвестная валюта"""

    def __init__(self, code: str):
        super().__init__(f"Неизвестная валюта '{code}'")
        self.code = code


class ApiRequestError(ValutaTradeError):
    """Ошибка при обращении к внешнему API"""

    def __init__(self, reason: str):
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
        self.reason = reason


class UserNotFoundError(ValutaTradeError):
    """Пользователь не найден"""

    def __init__(self, username: str = None, user_id: int = None):
        if username:
            message = f"Пользователь '{username}' не найден"
        elif user_id:
            message = f"Пользователь с ID={user_id} не найден"
        else:
            message = "Пользователь не найден"

        super().__init__(message)
        self.username = username
        self.user_id = user_id


class AuthenticationError(ValutaTradeError):
    """Ошибка аутентификации"""

    def __init__(self, message: str = "Неверный логин или пароль"):
        super().__init__(message)


class ValidationError(ValutaTradeError):
    """Ошибка валидации"""

    def __init__(self, field: str, message: str):
        super().__init__(f"Ошибка валидации поля '{field}': {message}")
        self.field = field
        self.message = message


class DatabaseError(ValutaTradeError):
    """Ошибка базы данных"""

    def __init__(self, message: str = "Ошибка при работе с базой данных"):
        super().__init__(message)


class PortfolioNotFoundError(ValutaTradeError):
    """Портфель не найден"""

    def __init__(self, user_id: int):
        super().__init__(f"Портфель пользователя с ID={user_id} не найден")
        self.user_id = user_id
