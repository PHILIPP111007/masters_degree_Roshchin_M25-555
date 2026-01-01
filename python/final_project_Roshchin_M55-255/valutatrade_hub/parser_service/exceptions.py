"""
Исключения для Parser Service
"""



class ParserServiceError(Exception):
    """Базовое исключение для Parser Service"""

    pass


class ConfigError(ParserServiceError):
    """Ошибка конфигурации"""

    pass


class RateFetchError(ParserServiceError):
    """Ошибка при получении курсов"""

    pass


class StorageError(ParserServiceError):
    """Ошибка при работе с хранилищем"""

    pass
