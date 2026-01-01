"""
Модели данных для ValutaTrade Hub
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from valutatrade_hub.core.currencies import get_currency, is_currency_supported
from valutatrade_hub.core.exceptions import (
    CurrencyNotFoundError,
    InsufficientFundsError,
    ValidationError,
)
from valutatrade_hub.core.utils import (
    generate_salt,
    hash_password,
    validate_amount,
    validate_currency_code,
)


class User:
    """
    Класс пользователя системы
    """

    def __init__(
        self,
        user_id: int,
        username: str,
        password: str,
        registration_date: Optional[datetime] = None,
    ):
        """
        Конструктор класса User

        Args:
            user_id: Уникальный идентификатор пользователя
            username: Имя пользователя
            password: Пароль пользователя
            registration_date: Дата регистрации
        """
        self._user_id = user_id
        self._username = username
        self._salt = self._generate_salt()
        self._hashed_password = self._hash_password(password)
        self._registration_date = registration_date or datetime.now()

    def _generate_salt(self, length: int = 16) -> str:
        """Генерация случайной соли"""
        return generate_salt(length)

    def _hash_password(self, password: str) -> str:
        """Хеширование пароля с использованием соли"""
        return hash_password(password, self._salt)

    @property
    def user_id(self) -> int:
        """Уникальный идентификатор пользователя"""
        return self._user_id

    @user_id.setter
    def user_id(self, value: int):
        """Сеттер для user_id"""
        if not isinstance(value, int):
            raise ValidationError("user_id", "Должен быть целым числом")
        if value <= 0:
            raise ValidationError("user_id", "Должен быть положительным числом")
        self._user_id = value

    @property
    def username(self) -> str:
        """Имя пользователя"""
        return self._username

    @username.setter
    def username(self, value: str):
        """Сеттер для username"""
        if not value or not value.strip():
            raise ValidationError("username", "Не может быть пустым")
        self._username = value.strip()

    @property
    def hashed_password(self) -> str:
        """Хешированный пароль"""
        return self._hashed_password

    @hashed_password.setter
    def hashed_password(self, value: str):
        """Сеттер для hashed_password"""
        if not value or not isinstance(value, str):
            raise ValidationError("hashed_password", "Должен быть непустой строкой")
        self._hashed_password = value

    @property
    def salt(self) -> str:
        """Соль для хеширования пароля"""
        return self._salt

    @property
    def registration_date(self) -> datetime:
        """Дата регистрации"""
        return self._registration_date

    @registration_date.setter
    def registration_date(self, value: datetime):
        """Сеттер для registration_date"""
        if not isinstance(value, datetime):
            raise ValidationError("registration_date", "Должен быть объектом datetime")
        self._registration_date = value

    def get_user_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о пользователе (без пароля)

        Returns:
            Словарь с информацией о пользователе
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def change_password(self, new_password: str) -> bool:
        """
        Изменение пароля пользователя

        Args:
            new_password: Новый пароль

        Returns:
            True если пароль изменен успешно

        Raises:
            ValidationError: Если пароль некорректен
        """
        if len(new_password) < 4:
            raise ValidationError(
                "new_password", "Должен содержать не менее 4 символов"
            )

        # Генерируем новую соль и хешируем новый пароль
        self._salt = self._generate_salt()
        self._hashed_password = self._hash_password(new_password)
        return True

    def verify_password(self, password: str) -> bool:
        """
        Проверка введенного пароля

        Args:
            password: Пароль для проверки

        Returns:
            True если пароль верный, иначе False
        """
        test_hash = hash_password(password, self._salt)
        return test_hash == self._hashed_password

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование в словарь для сохранения в JSON

        Returns:
            Словарь с данными пользователя
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> User:
        """
        Создание объекта User из словаря

        Args:
            data: Словарь с данными пользователя

        Returns:
            Объект User
        """
        user = cls(
            user_id=data["user_id"],
            username=data["username"],
            password="dummy",  # Временный пароль
        )
        user._hashed_password = data["hashed_password"]
        user._salt = data["salt"]
        user._registration_date = datetime.fromisoformat(data["registration_date"])
        return user

    def __str__(self) -> str:
        """Строковое представление"""
        return f"User(id={self._user_id}, username='{self._username}')"

    def __repr__(self) -> str:
        """Представление для отладки"""
        return f"User(user_id={self._user_id}, username='{self._username}')"


class Wallet:
    """
    Класс кошелька пользователя для одной конкретной валюты
    """

    def __init__(self, currency_code: str, balance: float = 0.0):
        """
        Конструктор класса Wallet

        Args:
            currency_code: Код валюты
            balance: Начальный баланс
        """
        self.currency_code = currency_code.upper()
        self.balance = balance

    @property
    def currency_code(self) -> str:
        """Код валюты"""
        return self._currency_code

    @currency_code.setter
    def currency_code(self, value: str):
        """Сеттер для currency_code"""
        is_valid, error_message = validate_currency_code(value)
        if not is_valid:
            raise ValidationError("currency_code", error_message)

        if not is_currency_supported(value):
            raise CurrencyNotFoundError(value)

        self._currency_code = value.upper()

    @property
    def balance(self) -> float:
        """Баланс кошелька"""
        return self._balance

    @balance.setter
    def balance(self, value: float):
        """Сеттер для balance"""
        is_valid, error_message = validate_amount(value)
        if not is_valid and value != 0:
            raise ValidationError("balance", error_message)

        self._balance = float(value)

    def deposit(self, amount: float) -> bool:
        """
        Пополнение баланса

        Args:
            amount: Сумма для пополнения

        Returns:
            True если операция успешна

        Raises:
            ValidationError: Если сумма некорректна
        """
        is_valid, error_message = validate_amount(amount)
        if not is_valid:
            raise ValidationError("amount", error_message)

        self.balance += amount
        return True

    def withdraw(self, amount: float) -> bool:
        """
        Снятие средств с кошелька

        Args:
            amount: Сумма для снятия

        Returns:
            True если операция успешна

        Raises:
            ValidationError: Если сумма некорректна
            InsufficientFundsError: Если недостаточно средств
        """
        is_valid, error_message = validate_amount(amount)
        if not is_valid:
            raise ValidationError("amount", error_message)

        if amount > self.balance:
            raise InsufficientFundsError(self.currency_code, self.balance, amount)

        self.balance -= amount
        return True

    def get_balance_info(self) -> Dict[str, Any]:
        """
        Получение информации о балансе

        Returns:
            Словарь с информацией о балансе
        """
        return {
            "currency_code": self.currency_code,
            "balance": self.balance,
            "currency_info": get_currency(self.currency_code).get_display_info(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование в словарь для сохранения в JSON

        Returns:
            Словарь с данными кошелька
        """
        return {"currency_code": self.currency_code, "balance": self.balance}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Wallet:
        """
        Создание объекта Wallet из словаря

        Args:
            data: Словарь с данными кошелька

        Returns:
            Объект Wallet
        """
        return cls(currency_code=data["currency_code"], balance=data["balance"])

    def __str__(self) -> str:
        """Строковое представление"""
        return f"Wallet({self.currency_code}: {self.balance:.6f})"

    def __repr__(self) -> str:
        """Представление для отладки"""
        return f"Wallet(currency_code='{self.currency_code}', balance={self.balance})"


class Portfolio:
    """
    Класс для управления всеми кошельками одного пользователя
    """

    def __init__(self, user_id: int, wallets: Optional[Dict[str, Wallet]] = None):
        """
        Конструктор класса Portfolio

        Args:
            user_id: ID пользователя
            wallets: Словарь кошельков
        """
        self._user_id = user_id
        self._wallets = wallets or {}

    @property
    def user_id(self) -> int:
        """ID пользователя"""
        return self._user_id

    @user_id.setter
    def user_id(self, value: int):
        """Сеттер для user_id"""
        if not isinstance(value, int):
            raise ValidationError("user_id", "Должен быть целым числом")
        if value <= 0:
            raise ValidationError("user_id", "Должен быть положительным числом")
        self._user_id = value

    @property
    def wallets(self) -> Dict[str, Wallet]:
        """Словарь кошельков (копия)"""
        return self._wallets.copy()

    def add_currency(self, currency_code: str, initial_balance: float = 0.0) -> Wallet:
        """
        Добавление новой валюты в портфель

        Args:
            currency_code: Код валюты
            initial_balance: Начальный баланс

        Returns:
            Созданный кошелек

        Raises:
            ValidationError: Если валюта уже существует
        """
        currency_code = currency_code.upper()

        if currency_code in self._wallets:
            raise ValidationError(
                "currency_code", f"Валюта {currency_code} уже существует в портфеле"
            )

        wallet = Wallet(currency_code, initial_balance)
        self._wallets[currency_code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Optional[Wallet]:
        """
        Получение кошелька по коду валюты

        Args:
            currency_code: Код валюты

        Returns:
            Кошелек или None, если не найден
        """
        return self._wallets.get(currency_code.upper())

    def ensure_wallet_exists(self, currency_code: str) -> Wallet:
        """
        Гарантирует наличие кошелька для валюты

        Args:
            currency_code: Код валюты

        Returns:
            Существующий или созданный кошелек
        """
        wallet = self.get_wallet(currency_code)
        if not wallet:
            wallet = self.add_currency(currency_code, 0.0)
        return wallet

    def get_total_value(
        self, exchange_rates: Dict[str, float], base_currency: str = "USD"
    ) -> float:
        """
        Расчет общей стоимости портфеля

        Args:
            exchange_rates: Словарь курсов валют
            base_currency: Базовая валюта

        Returns:
            Общая стоимость в базовой валюте
        """
        total_value = 0.0

        for currency_code, wallet in self._wallets.items():
            if currency_code == base_currency:
                total_value += wallet.balance
            else:
                rate_key = f"{currency_code}_{base_currency}"
                if rate_key in exchange_rates:
                    rate = exchange_rates[rate_key]
                    total_value += wallet.balance * rate

        return total_value

    def get_portfolio_info(
        self, exchange_rates: Dict[str, float], base_currency: str = "USD"
    ) -> Dict[str, Any]:
        """
        Получение полной информации о портфеле

        Args:
            exchange_rates: Словарь курсов валют
            base_currency: Базовая валюта

        Returns:
            Словарь с информацией о портфеле
        """
        wallets_info = {}
        total_value = 0.0

        for currency_code, wallet in self._wallets.items():
            wallet_info = wallet.get_balance_info()

            if currency_code == base_currency:
                value_in_base = wallet.balance
            else:
                rate_key = f"{currency_code}_{base_currency}"
                value_in_base = wallet.balance * exchange_rates.get(rate_key, 0)

            wallet_info["value_in_base"] = value_in_base
            total_value += value_in_base

            wallets_info[currency_code] = wallet_info

        return {
            "user_id": self._user_id,
            "wallets": wallets_info,
            "total_value": total_value,
            "base_currency": base_currency,
            "wallets_count": len(self._wallets),
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование в словарь для сохранения в JSON

        Returns:
            Словарь с данными портфеля
        """
        wallets_dict = {}
        for currency_code, wallet in self._wallets.items():
            wallets_dict[currency_code] = wallet.to_dict()

        return {"user_id": self._user_id, "wallets": wallets_dict}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Portfolio:
        """
        Создание объекта Portfolio из словаря

        Args:
            data: Словарь с данными портфеля

        Returns:
            Объект Portfolio
        """
        wallets = {}
        for currency_code, wallet_data in data["wallets"].items():
            wallets[currency_code] = Wallet.from_dict(wallet_data)

        return cls(user_id=data["user_id"], wallets=wallets)

    def __str__(self) -> str:
        """Строковое представление"""
        return f"Portfolio(user_id={self._user_id}, wallets={len(self._wallets)})"

    def __repr__(self) -> str:
        """Представление для отладки"""
        return f"Portfolio(user_id={self._user_id}, wallets={self._wallets})"
