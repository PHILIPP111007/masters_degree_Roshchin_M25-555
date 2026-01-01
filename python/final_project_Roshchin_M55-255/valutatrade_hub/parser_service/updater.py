"""
Основной модуль обновления курсов валют
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
    BaseApiClient,
)
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.config import config
from valutatrade_hub.parser_service.exceptions import RateFetchError
from valutatrade_hub.core.exceptions import ApiRequestError


logger = logging.getLogger(__name__)


class RatesUpdater:
    """
    Класс для координации процесса обновления курсов валют.
    """

    def __init__(self):
        self.clients: List[BaseApiClient] = [CoinGeckoClient(), ExchangeRateApiClient()]
        self.storage = RatesStorage()

    def run_update(self, source: str = None) -> Dict[str, Any]:
        """
        Запуск обновления курсов валют

        Args:
            source: Ограничить обновление одним источником
                   ("coingecko" или "exchangerate")

        Returns:
            Результат обновления

        Raises:
            RateFetchError: При ошибке получения курсов
        """
        logger.info("Starting rates update...")

        all_rates = {}
        errors = []
        sources_updated = []

        # Фильтруем клиентов, если указан источник
        clients_to_use = self.clients
        if source:
            if source.lower() == "coingecko":
                clients_to_use = [
                    c for c in self.clients if isinstance(c, CoinGeckoClient)
                ]
            elif source.lower() == "exchangerate":
                clients_to_use = [
                    c for c in self.clients if isinstance(c, ExchangeRateApiClient)
                ]
            else:
                raise ValueError(f"Unknown source: {source}")

        # Опрашиваем каждый клиент
        for client in clients_to_use:
            try:
                logger.info(f"Fetching from {client.name}...")
                rates = client.fetch_rates()

                if rates:
                    all_rates.update(rates)
                    sources_updated.append(client.name)
                    logger.info(f"  ✓ {client.name}: OK ({len(rates)} rates)")
                else:
                    logger.warning(f"  ⚠  {client.name}: No rates received")

            except ApiRequestError as e:
                error_msg = f"  ✗ {client.name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"  ✗ {client.name}: Unexpected error - {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Сохраняем результаты
        if all_rates:
            try:
                # Определяем источник для сохранения
                if len(sources_updated) == 1:
                    source_name = sources_updated[0]
                else:
                    source_name = "Multiple sources"

                # Сохраняем в кеш
                self.storage.save_current_rates(all_rates, source_name)

                # Сохраняем каждую пару в историю
                now = datetime.now(timezone.utc).isoformat()
                for pair_key, rate in all_rates.items():
                    from_currency, to_currency = pair_key.split("_")
                    rate_data = {
                        "from_currency": from_currency,
                        "to_currency": to_currency,
                        "rate": rate,
                        "timestamp": now,
                        "source": source_name,
                        "meta": {
                            "request_ms": 0,  # Можно добавить реальное время запроса
                            "status_code": 200,
                        },
                    }
                    self.storage.save_to_history(rate_data)

                logger.info(f"Writing {len(all_rates)} rates to {config.RATES_FILE}...")

                return {
                    "success": True,
                    "rates_count": len(all_rates),
                    "sources_updated": sources_updated,
                    "errors": errors,
                    "last_refresh": now,
                }

            except Exception as e:
                error_msg = f"Error saving rates: {str(e)}"
                logger.error(error_msg)
                raise RateFetchError(error_msg)

        else:
            error_msg = "No rates received from any source"
            logger.error(error_msg)
            raise RateFetchError(error_msg)

    def get_update_status(self) -> Dict[str, Any]:
        """
        Получение статуса последнего обновления

        Returns:
            Информация о статусе обновления
        """
        try:
            data = self.storage.load_current_rates()
            return {
                "has_data": bool(data.get("pairs")),
                "last_refresh": data.get("last_refresh"),
                "rates_count": len(data.get("pairs", {})),
                "source": data.get("source", "Unknown"),
            }
        except Exception as e:
            logger.error(f"Error getting update status: {str(e)}")
            return {
                "has_data": False,
                "last_refresh": None,
                "rates_count": 0,
                "source": "Unknown",
            }

    def force_refresh(self) -> Dict[str, Any]:
        """
        Принудительное обновление всех курсов

        Returns:
            Результат обновления
        """
        logger.info("Forcing refresh of all rates...")
        return self.run_update()
