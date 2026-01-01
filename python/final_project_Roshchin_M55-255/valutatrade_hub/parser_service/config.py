"""
Конфигурация Parser Service
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Tuple, List
from pathlib import Path


def default_crypto_id_map() -> Dict[str, str]:
    """Фабрика для CRYPTO_ID_MAP"""
    return {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "LTC": "litecoin",
        "XRP": "ripple",
        "ADA": "cardano",
        "DOT": "polkadot",
        "DOGE": "dogecoin",
        "SOL": "solana",
    }


def default_fiat_currencies() -> Tuple[str, ...]:
    """Фабрика для FIAT_CURRENCIES"""
    return ("EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY", "RUB")


def default_crypto_currencies() -> Tuple[str, ...]:
    """Фабрика для CRYPTO_CURRENCIES"""
    return ("BTC", "ETH", "LTC", "XRP", "ADA", "DOT", "DOGE", "SOL")


@dataclass
class ParserConfig:
    """
    Конфигурация для сервиса парсинга курсов валют.
    Ключи API загружаются из переменных окружения.
    """

    # API-ключи (загружаются из переменных окружения)
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")

    # Эндпоинты API
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # Базовая валюта
    BASE_CURRENCY: str = "USD"

    # Списки отслеживаемых валют с default_factory
    FIAT_CURRENCIES: Tuple[str, ...] = field(default_factory=default_fiat_currencies)
    CRYPTO_CURRENCIES: Tuple[str, ...] = field(
        default_factory=default_crypto_currencies
    )
    CRYPTO_ID_MAP: Dict[str, str] = field(default_factory=default_crypto_id_map)

    # Пути к файлам данных
    DATA_DIR: Path = field(default_factory=lambda: Path("data"))
    RATES_FILE: Path = field(init=False)  # Инициализируется в __post_init__
    HISTORY_FILE: Path = field(init=False)  # Инициализируется в __post_init__

    # Сетевые параметры
    REQUEST_TIMEOUT: int = 10  # секунд
    MAX_RETRIES: int = 3  # количество попыток при ошибках сети

    # Интервал обновления (в секундах)
    UPDATE_INTERVAL: int = 3600  # 1 час

    def __post_init__(self):
        """Инициализация полей после создания объекта"""
        # Инициализируем пути к файлам
        self.DATA_DIR.mkdir(exist_ok=True)
        self.RATES_FILE = self.DATA_DIR / "rates.json"
        self.HISTORY_FILE = self.DATA_DIR / "exchange_rates.json"

        # Проверяем наличие API-ключа для ExchangeRate-API
        if not self.EXCHANGERATE_API_KEY:
            print(
                "⚠️  Внимание: EXCHANGERATE_API_KEY не установлен в переменных окружения"
            )
            print(
                "   Для фиатных валют будет использоваться публичный доступ (с ограничениями)"
            )

    def validate(self) -> bool:
        """Проверка валидности конфигурации"""
        # Проверяем, что все криптовалюты имеют соответствие в CRYPTO_ID_MAP
        missing_mappings = []
        for crypto in self.CRYPTO_CURRENCIES:
            if crypto not in self.CRYPTO_ID_MAP:
                missing_mappings.append(crypto)

        if missing_mappings:
            print(
                f"⚠️  Внимание: отсутствуют маппинги для криптовалют: {missing_mappings}"
            )
            print("   Добавьте их в CRYPTO_ID_MAP в config.py")
            return False

        return True


# Глобальный экземпляр конфигурации
config = ParserConfig()
