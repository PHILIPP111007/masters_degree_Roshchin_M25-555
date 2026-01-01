"""
Клиенты для работы с внешними API
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import config


class BaseApiClient(ABC):
    """Абстрактный базовый класс для API клиентов"""

    def __init__(self, name: str):
        self.name = name
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "ValutaTradeHub/1.0", "Accept": "application/json"}
        )

    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """
        Получение курсов валют от API

        Returns:
            Словарь с курсами в формате {валютная_пара: курс}

        Raises:
            ApiRequestError: При ошибке запроса к API
        """
        pass

    def _make_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Выполнение HTTP запроса с обработкой ошибок

        Args:
            url: URL для запроса
            params: Параметры запроса

        Returns:
            Ответ API в виде словаря

        Raises:
            ApiRequestError: При ошибке запроса
        """
        try:
            response = self.session.get(
                url, params=params, timeout=config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            raise ApiRequestError(f"Таймаут при запросе к {self.name}")
        except requests.exceptions.ConnectionError:
            raise ApiRequestError(f"Ошибка соединения с {self.name}")
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "unknown"
            raise ApiRequestError(
                f"HTTP ошибка {status_code} при запросе к {self.name}: {str(e)}"
            )
        except json.JSONDecodeError as e:
            raise ApiRequestError(f"Ошибка парсинга JSON от {self.name}: {str(e)}")
        except Exception as e:
            raise ApiRequestError(
                f"Неизвестная ошибка при запросе к {self.name}: {str(e)}"
            )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"


class CoinGeckoClient(BaseApiClient):
    """Клиент для работы с CoinGecko API"""

    def __init__(self):
        super().__init__("CoinGecko")

    def fetch_rates(self) -> Dict[str, float]:
        """
        Получение курсов криптовалют от CoinGecko

        Returns:
            Словарь с курсами криптовалют к USD

        Raises:
            ApiRequestError: При ошибке запроса
        """
        # Подготавливаем список ID криптовалют
        crypto_ids = [
            config.CRYPTO_ID_MAP[crypto]
            for crypto in config.CRYPTO_CURRENCIES
            if crypto in config.CRYPTO_ID_MAP
        ]

        if not crypto_ids:
            return {}

        # Формируем параметры запроса
        params = {"ids": ",".join(crypto_ids), "vs_currencies": "usd"}

        # Выполняем запрос
        data = self._make_request(config.COINGECKO_URL, params)

        # Преобразуем ответ в стандартный формат
        rates = {}
        for crypto_code in config.CRYPTO_CURRENCIES:
            if crypto_code in config.CRYPTO_ID_MAP:
                gecko_id = config.CRYPTO_ID_MAP[crypto_code]
                if gecko_id in data and "usd" in data[gecko_id]:
                    pair_key = f"{crypto_code}_{config.BASE_CURRENCY}"
                    rates[pair_key] = float(data[gecko_id]["usd"])

        return rates


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для работы с ExchangeRate-API"""

    def __init__(self):
        super().__init__("ExchangeRate-API")

    def fetch_rates(self) -> Dict[str, float]:
        """
        Получение курсов фиатных валют от ExchangeRate-API

        Returns:
            Словарь с курсами фиатных валют к USD

        Raises:
            ApiRequestError: При ошибке запроса
        """
        # Формируем URL с API ключом
        if not config.EXCHANGERATE_API_KEY:
            print("⚠️  ExchangeRate-API ключ не установлен, пропускаем фиатные валюты")
            return {}

        url = (
            f"{config.EXCHANGERATE_API_URL}/{config.EXCHANGERATE_API_KEY}/"
            f"latest/{config.BASE_CURRENCY}"
        )

        # Выполняем запрос
        data = self._make_request(url)

        # Проверяем статус ответа
        if data.get("result") != "success":
            error_type = data.get("error-type", "unknown")
            raise ApiRequestError(f"ExchangeRate-API вернул ошибку: {error_type}")

        # Извлекаем курсы
        rates_data = data.get("rates", {})

        # Преобразуем в стандартный формат
        rates = {}
        for fiat_code in config.FIAT_CURRENCIES:
            if fiat_code in rates_data:
                pair_key = f"{fiat_code}_{config.BASE_CURRENCY}"
                rates[pair_key] = float(rates_data[fiat_code])

        return rates
