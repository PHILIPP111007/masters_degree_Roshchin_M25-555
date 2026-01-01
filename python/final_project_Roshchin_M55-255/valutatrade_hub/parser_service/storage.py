"""
Управление хранилищем данных Parser Service
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import shutil

from valutatrade_hub.parser_service.config import config
from valutatrade_hub.parser_service.exceptions import StorageError


class RatesStorage:
    """
    Класс для управления хранилищем курсов валют.
    Отвечает за работу с rates.json (кеш) и exchange_rates.json (журнал).
    """

    def __init__(self):
        self.rates_file = config.RATES_FILE
        self.history_file = config.HISTORY_FILE

    def save_current_rates(self, rates: Dict[str, float], source: str) -> None:
        """
        Сохранение текущих курсов в кеш (rates.json)

        Args:
            rates: Словарь с курсами в формате {валютная_пара: курс}
            source: Источник данных (CoinGecko, ExchangeRate-API)

        Raises:
            StorageError: При ошибке сохранения
        """
        try:
            # Подготавливаем данные для сохранения
            now = datetime.now(timezone.utc).isoformat()
            pairs_data = {}

            for pair_key, rate in rates.items():
                pairs_data[pair_key] = {
                    "rate": rate,
                    "updated_at": now,
                    "source": source,
                }

            data = {"pairs": pairs_data, "last_refresh": now, "source": source}

            # Атомарное сохранение через временный файл
            with tempfile.NamedTemporaryFile(
                mode="w", dir=self.rates_file.parent, delete=False, encoding="utf-8"
            ) as tmp_file:
                json.dump(data, tmp_file, indent=2, ensure_ascii=False)
                tmp_path = Path(tmp_file.name)

            # Перемещаем временный файл на место целевого
            shutil.move(str(tmp_path), str(self.rates_file))

        except (IOError, json.JSONDecodeError) as e:
            raise StorageError(f"Ошибка сохранения текущих курсов: {str(e)}")

    def save_to_history(self, rate_data: Dict[str, Any]) -> None:
        """
        Сохранение записи в историю (exchange_rates.json)

        Args:
            rate_data: Данные о курсе для сохранения

        Raises:
            StorageError: При ошибке сохранения
        """
        try:
            # Создаем уникальный ID для записи
            from_currency = rate_data["from_currency"]
            to_currency = rate_data["to_currency"]
            timestamp = rate_data["timestamp"]

            record_id = f"{from_currency}_{to_currency}_{timestamp}"
            rate_data["id"] = record_id

            # Загружаем существующую историю
            history = self._load_history()

            # Добавляем новую запись
            history.append(rate_data)

            # Атомарное сохранение
            with tempfile.NamedTemporaryFile(
                mode="w", dir=self.history_file.parent, delete=False, encoding="utf-8"
            ) as tmp_file:
                json.dump(history, tmp_file, indent=2, ensure_ascii=False)
                tmp_path = Path(tmp_file.name)

            shutil.move(str(tmp_path), str(self.history_file))

        except (IOError, json.JSONDecodeError, KeyError) as e:
            raise StorageError(f"Ошибка сохранения в историю: {str(e)}")

    def load_current_rates(self) -> Dict[str, Any]:
        """
        Загрузка текущих курсов из кеша

        Returns:
            Данные из rates.json

        Raises:
            StorageError: При ошибке загрузки
        """
        try:
            if not self.rates_file.exists():
                return {"pairs": {}, "last_refresh": None}

            with open(self.rates_file, "r", encoding="utf-8") as f:
                return json.load(f)

        except (IOError, json.JSONDecodeError) as e:
            raise StorageError(f"Ошибка загрузки текущих курсов: {str(e)}")

    def _load_history(self) -> List[Dict[str, Any]]:
        """
        Загрузка истории курсов

        Returns:
            Список исторических записей

        Raises:
            StorageError: При ошибке загрузки
        """
        try:
            if not self.history_file.exists():
                return []

            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)

        except (IOError, json.JSONDecodeError) as e:
            raise StorageError(f"Ошибка загрузки истории: {str(e)}")

    def get_latest_rates(self) -> Dict[str, Dict[str, Any]]:
        """
        Получение последних курсов из кеша в удобном формате

        Returns:
            Словарь с последними курсами
        """
        data = self.load_current_rates()
        return data.get("pairs", {})

    def clear_history(self) -> None:
        """
        Очистка истории курсов

        Raises:
            StorageError: При ошибке очистки
        """
        try:
            if self.history_file.exists():
                self.history_file.unlink()
        except IOError as e:
            raise StorageError(f"Ошибка очистки истории: {str(e)}")

    def cleanup_old_records(self, max_days: int = 30) -> None:
        """
        Удаление старых записей из истории

        Args:
            max_days: Максимальный возраст записей в днях

        Raises:
            StorageError: При ошибке очистки
        """
        try:
            history = self._load_history()
            if not history:
                return

            cutoff_date = datetime.now(timezone.utc).timestamp() - (max_days * 86400)

            filtered_history = []
            for record in history:
                try:
                    record_date = datetime.fromisoformat(
                        record["timestamp"].replace("Z", "+00:00")
                    ).timestamp()

                    if record_date >= cutoff_date:
                        filtered_history.append(record)
                except (KeyError, ValueError):
                    # Пропускаем некорректные записи
                    continue

            # Сохраняем отфильтрованную историю
            with tempfile.NamedTemporaryFile(
                mode="w", dir=self.history_file.parent, delete=False, encoding="utf-8"
            ) as tmp_file:
                json.dump(filtered_history, tmp_file, indent=2, ensure_ascii=False)
                tmp_path = Path(tmp_file.name)

            shutil.move(str(tmp_path), str(self.history_file))

        except (IOError, json.JSONDecodeError) as e:
            raise StorageError(f"Ошибка очистки старых записей: {str(e)}")
