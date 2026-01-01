"""
Singleton для загрузки настроек
"""

import json
import tomli
from pathlib import Path
from typing import Any, Dict, Optional
import threading


class SettingsLoader:
    """
    Singleton для загрузки и управления настройками приложения
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        Реализация Singleton через __new__
        Гарантирует, что в приложении существует только один экземпляр
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Инициализация настроек (вызывается только один раз)"""
        if getattr(self, "_initialized", False):
            return

        self._config: Dict[str, Any] = {}
        self._config_file = Path("pyproject.toml")
        self._config_cache = {}

        self._load_config()
        self._initialized = True

    def _load_config(self):
        """Загрузка конфигурации из файла"""
        # Загрузка из pyproject.toml
        if self._config_file.exists():
            try:
                with open(self._config_file, "rb") as f:
                    data = tomli.load(f)
                    # Извлекаем настройки из секции [tool.valutatrade]
                    self._config = data.get("tool", {}).get("valutatrade", {})
            except Exception as e:
                print(f"Ошибка загрузки конфигурации из pyproject.toml: {e}")
                self._config = {}

        # Устанавливаем значения по умолчанию
        self._set_defaults()

    def _set_defaults(self):
        """Установка значений по умолчанию"""
        defaults = {
            "data_dir": "data",
            "log_dir": "logs",
            "log_level": "INFO",
            "log_format": "json",
            "default_base_currency": "USD",
            "rates_ttl_seconds": 300,  # 5 минут
            "session_ttl_hours": 24,
            "max_log_size_mb": 10,
            "max_log_files": 5,
            "supported_currencies": [
                "USD",
                "EUR",
                "GBP",
                "JPY",
                "CHF",
                "CAD",
                "AUD",
                "CNY",
                "RUB",
                "BTC",
                "ETH",
                "LTC",
                "XRP",
                "ADA",
                "DOT",
                "DOGE",
                "SOL",
            ],
        }

        # Объединяем с загруженными настройками (загруженные имеют приоритет)
        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получение значения настройки

        Args:
            key: Ключ настройки
            default: Значение по умолчанию

        Returns:
            Значение настройки или default
        """
        # Проверка кеша
        if key in self._config_cache:
            return self._config_cache[key]

        # Поиск значения (поддержка вложенных ключей через точку)
        keys = key.split(".")
        value = self._config

        try:
            for k in keys:
                value = value[k]

            # Кешируем результат
            self._config_cache[key] = value
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        Установка значения настройки

        Args:
            key: Ключ настройки
            value: Значение
        """
        # Очищаем кеш для этого ключа
        if key in self._config_cache:
            del self._config_cache[key]

        # Установка значения (поддержка вложенных ключей через точку)
        keys = key.split(".")
        config = self._config

        # Создаем вложенные словари при необходимости
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def reload(self) -> None:
        """
        Перезагрузка конфигурации из файла
        """
        self._config_cache.clear()
        self._load_config()

    def get_data_dir(self) -> Path:
        """Получение пути к директории данных"""
        return Path(self.get("data_dir", "data"))

    def get_log_dir(self) -> Path:
        """Получение пути к директории логов"""
        return Path(self.get("log_dir", "logs"))

    def get_log_level(self) -> str:
        """Получение уровня логирования"""
        return self.get("log_level", "INFO")

    def get_log_format(self) -> str:
        """Получение формата логов"""
        return self.get("log_format", "json")

    def get_default_base_currency(self) -> str:
        """Получение базовой валюты по умолчанию"""
        return self.get("default_base_currency", "USD")

    def get_rates_ttl_seconds(self) -> int:
        """Получение времени жизни курсов в секундах"""
        return self.get("rates_ttl_seconds", 300)

    def get_session_ttl_hours(self) -> int:
        """Получение времени жизни сессии в часах"""
        return self.get("session_ttl_hours", 24)

    def get_supported_currencies(self) -> list:
        """Получение списка поддерживаемых валют"""
        return self.get("supported_currencies", [])

    def to_dict(self) -> Dict[str, Any]:
        """Получение всех настроек в виде словаря"""
        return self._config.copy()


# Глобальный экземпляр настроек
settings = SettingsLoader()
