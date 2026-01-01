"""
Иерархия валют для ValutaTrade Hub
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import re


class CurrencyNotFoundError(Exception):
    """Исключение для неизвестной валюты"""

    def __init__(self, code: str):
        super().__init__(f"Неизвестная валюта '{code}'")
        self.code = code


class Currency(ABC):
    """
    Абстрактный базовый класс для валют
    """

    def __init__(self, name: str, code: str):
        """
        Инициализация валюты

        Args:
            name: Человекочитаемое имя валюты
            code: Код валюты (ISO код или тикер)
        """
        self._validate_code(code)
        self._validate_name(name)

        self._name = name
        self._code = code.upper()

    @property
    def name(self) -> str:
        """Возвращает имя валюты"""
        return self._name

    @property
    def code(self) -> str:
        """Возвращает код валюты"""
        return self._code

    @abstractmethod
    def get_display_info(self) -> str:
        """
        Возвращает строковое представление валюты

        Returns:
            Строка с информацией о валюте
        """
        pass

    def _validate_code(self, code: str):
        """Валидация кода валюты"""
        if not isinstance(code, str):
            raise TypeError("Код валюты должен быть строкой")

        if not 2 <= len(code) <= 5:
            raise ValueError("Код валюты должен содержать от 2 до 5 символов")

        if not re.match(r"^[A-Z0-9]+$", code.upper()):
            raise ValueError("Код валюты должен содержать только буквы и цифры")

    def _validate_name(self, name: str):
        """Валидация имени валюты"""
        if not isinstance(name, str):
            raise TypeError("Имя валюты должно быть строкой")

        if not name.strip():
            raise ValueError("Имя валюты не может быть пустым")

    def __str__(self) -> str:
        """Строковое представление"""
        return self.get_display_info()

    def __repr__(self) -> str:
        """Представление для отладки"""
        return f"{self.__class__.__name__}(name='{self.name}', code='{self.code}')"


class FiatCurrency(Currency):
    """
    Класс для фиатных валют
    """

    def __init__(self, name: str, code: str, issuing_country: str):
        """
        Инициализация фиатной валюты

        Args:
            name: Имя валюты
            code: Код валюты
            issuing_country: Страна/зона эмиссии
        """
        super().__init__(name, code)

        if not issuing_country.strip():
            raise ValueError("Страна эмиссии не может быть пустой")

        self._issuing_country = issuing_country

    @property
    def issuing_country(self) -> str:
        """Возвращает страну эмиссии"""
        return self._issuing_country

    @property
    def currency_type(self) -> str:
        """Возвращает тип валюты"""
        return "FIAT"

    def get_display_info(self) -> str:
        """Возвращает строковое представление фиатной валюты"""
        return f"[{self.currency_type}] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """
    Класс для криптовалют
    """

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float = 0.0):
        """
        Инициализация криптовалюты

        Args:
            name: Имя валюты
            code: Код валюты
            algorithm: Алгоритм консенсуса/хэширования
            market_cap: Рыночная капитализация
        """
        super().__init__(name, code)

        if not algorithm.strip():
            raise ValueError("Алгоритм не может быть пустым")

        if market_cap < 0:
            raise ValueError("Рыночная капитализация не может быть отрицательной")

        self._algorithm = algorithm
        self._market_cap = market_cap

    @property
    def algorithm(self) -> str:
        """Возвращает алгоритм"""
        return self._algorithm

    @property
    def market_cap(self) -> float:
        """Возвращает рыночную капитализацию"""
        return self._market_cap

    @property
    def currency_type(self) -> str:
        """Возвращает тип валюты"""
        return "CRYPTO"

    def get_display_info(self) -> str:
        """Возвращает строковое представление криптовалюты"""
        mcap_str = (
            f"{self.market_cap:.2e}"
            if self.market_cap > 1e6
            else f"{self.market_cap:,.2f}"
        )
        return f"[{self.currency_type}] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {mcap_str})"


# Реестр валют
_CURRENCY_REGISTRY: Dict[str, Currency] = {}


def _initialize_currency_registry():
    """Инициализация реестра валют"""
    global _CURRENCY_REGISTRY

    # Фиатные валюты
    fiat_currencies = [
        FiatCurrency("US Dollar", "USD", "United States"),
        FiatCurrency("Euro", "EUR", "Eurozone"),
        FiatCurrency("British Pound", "GBP", "United Kingdom"),
        FiatCurrency("Japanese Yen", "JPY", "Japan"),
        FiatCurrency("Swiss Franc", "CHF", "Switzerland"),
        FiatCurrency("Canadian Dollar", "CAD", "Canada"),
        FiatCurrency("Australian Dollar", "AUD", "Australia"),
        FiatCurrency("Chinese Yuan", "CNY", "China"),
        FiatCurrency("Russian Ruble", "RUB", "Russia"),
    ]

    # Криптовалюты
    crypto_currencies = [
        CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
        CryptoCurrency("Ethereum", "ETH", "Ethash", 370e9),
        CryptoCurrency("Litecoin", "LTC", "Scrypt", 5.8e9),
        CryptoCurrency("Ripple", "XRP", "Ripple Protocol Consensus", 30e9),
        CryptoCurrency("Cardano", "ADA", "Ouroboros", 10e9),
        CryptoCurrency("Polkadot", "DOT", "Nominated Proof-of-Stake", 8e9),
        CryptoCurrency("Dogecoin", "DOGE", "Scrypt", 9e9),
        CryptoCurrency("Solana", "SOL", "Proof of History", 12e9),
    ]

    # Регистрация всех валют
    for currency in fiat_currencies + crypto_currencies:
        _CURRENCY_REGISTRY[currency.code] = currency


def get_currency(code: str) -> Currency:
    """
    Возвращает объект валюты по коду

    Args:
        code: Код валюты

    Returns:
        Объект Currency

    Raises:
        CurrencyNotFoundError: Если валюта не найдена
    """
    if not _CURRENCY_REGISTRY:
        _initialize_currency_registry()

    code_upper = code.upper()

    if code_upper not in _CURRENCY_REGISTRY:
        raise CurrencyNotFoundError(code)

    return _CURRENCY_REGISTRY[code_upper]


def get_all_currencies() -> Dict[str, Currency]:
    """
    Возвращает все доступные валюты

    Returns:
        Словарь с валютами (код -> объект Currency)
    """
    if not _CURRENCY_REGISTRY:
        _initialize_currency_registry()

    return _CURRENCY_REGISTRY.copy()


def get_supported_currency_codes() -> list:
    """
    Возвращает список поддерживаемых кодов валют

    Returns:
        Список кодов валют
    """
    if not _CURRENCY_REGISTRY:
        _initialize_currency_registry()

    return sorted(_CURRENCY_REGISTRY.keys())


def is_currency_supported(code: str) -> bool:
    """
    Проверяет, поддерживается ли валюта

    Args:
        code: Код валюты

    Returns:
        True если валюта поддерживается, иначе False
    """
    if not _CURRENCY_REGISTRY:
        _initialize_currency_registry()

    return code.upper() in _CURRENCY_REGISTRY
