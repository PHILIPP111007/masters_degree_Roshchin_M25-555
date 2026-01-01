"""
Декораторы для ValutaTrade Hub
"""

import logging
from typing import Callable, Any, Optional
from functools import wraps
import inspect


def log_action(
    action_name: Optional[str] = None, verbose: bool = False, log_result: bool = True
):
    """
    Декоратор для логирования действий пользователя

    Args:
        action_name: Название действия (если None, берется из имени функции)
        verbose: Логировать подробную информацию
        log_result: Логировать результат выполнения
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger(func.__module__)

            # Определяем имя действия
            action = action_name or func.__name__.upper()

            # Получаем информацию о параметрах
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Логируем начало действия
            log_kwargs = {"action": action, "result": "STARTED"}

            # Добавляем информацию о пользователе, если доступна
            if "user_id" in bound_args.arguments:
                log_kwargs["user_id"] = bound_args.arguments["user_id"]

            if "username" in bound_args.arguments:
                log_kwargs["username"] = bound_args.arguments["username"]

            if "currency_code" in bound_args.arguments:
                log_kwargs["currency_code"] = bound_args.arguments["currency_code"]

            if "amount" in bound_args.arguments:
                log_kwargs["amount"] = bound_args.arguments["amount"]

            logger.info(f"Начало действия: {action}", extra=log_kwargs)

            try:
                # Выполняем функцию
                result = func(*args, **kwargs)

                # Логируем успешное завершение
                if log_result:
                    log_kwargs["result"] = "OK"
                    if verbose and result is not None:
                        log_kwargs["result_data"] = str(result)

                    logger.info(f"Действие завершено: {action}", extra=log_kwargs)

                return result

            except Exception as e:
                # Логируем ошибку
                log_kwargs["result"] = "ERROR"
                log_kwargs["error_type"] = type(e).__name__
                log_kwargs["error_message"] = str(e)

                logger.error(f"Ошибка при выполнении: {action}", extra=log_kwargs)

                # Пробрасываем исключение дальше
                raise

        return wrapper

    return decorator


def validate_input(validation_rules: dict):
    """
    Декоратор для валидации входных параметров

    Args:
        validation_rules: Словарь с правилами валидации
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Проверяем параметры
            for param_name, rules in validation_rules.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]

                    # Проверка типа
                    if "type" in rules:
                        expected_type = rules["type"]
                        if not isinstance(value, expected_type):
                            raise TypeError(
                                f"Параметр '{param_name}' должен быть типа {expected_type.__name__}, "
                                f"получен {type(value).__name__}"
                            )

                    # Проверка минимального значения
                    if "min" in rules and value is not None:
                        if value < rules["min"]:
                            raise ValueError(
                                f"Параметр '{param_name}' должен быть не меньше {rules['min']}"
                            )

                    # Проверка максимального значения
                    if "max" in rules and value is not None:
                        if value > rules["max"]:
                            raise ValueError(
                                f"Параметр '{param_name}' должен быть не больше {rules['max']}"
                            )

                    # Проверка на пустоту
                    if "not_empty" in rules and rules["not_empty"]:
                        if not value:
                            raise ValueError(
                                f"Параметр '{param_name}' не может быть пустым"
                            )

            return func(*args, **kwargs)

        return wrapper

    return decorator
