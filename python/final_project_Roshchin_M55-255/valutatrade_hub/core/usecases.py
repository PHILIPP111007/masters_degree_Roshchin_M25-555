"""
Сценарии использования (бизнес-логика) для ValutaTrade Hub
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from valutatrade_hub.core.currencies import get_currency, is_currency_supported
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    AuthenticationError,
    CurrencyNotFoundError,
    InsufficientFundsError,
    PortfolioNotFoundError,
    UserNotFoundError,
    ValidationError,
)
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import is_data_fresh
from valutatrade_hub.decorators import log_action, validate_input
from valutatrade_hub.infra.database import db_manager
from valutatrade_hub.infra.settings import settings

logger = logging.getLogger(__name__)


class UserUseCases:
    """Сценарии использования для работы с пользователями"""

    @staticmethod
    @log_action(action_name="REGISTER", verbose=True)
    @validate_input(
        {
            "username": {"type": str, "not_empty": True},
            "password": {"type": str, "not_empty": True},
        }
    )
    def register_user(username: str, password: str) -> Dict[str, Any]:
        """
        Регистрация нового пользователя

        Args:
            username: Имя пользователя
            password: Пароль

        Returns:
            Информация о зарегистрированном пользователе

        Raises:
            ValidationError: Если данные некорректны
        """
        # Проверка уникальности имени пользователя
        existing_user = db_manager.find_one(
            "users", lambda u: u["username"].lower() == username.lower()
        )

        if existing_user:
            raise ValidationError(
                "username", f"Имя пользователя '{username}' уже занято"
            )

        # Проверка пароля
        if len(password) < 4:
            raise ValidationError(
                "password", "Пароль должен содержать не менее 4 символов"
            )

        # Генерация user_id
        users = db_manager.load_data("users", default=[])
        next_id = max([u["user_id"] for u in users], default=0) + 1

        # Создание пользователя
        user = User(user_id=next_id, username=username, password=password)

        # Сохранение пользователя
        db_manager.insert("users", user.to_dict())

        # Создание портфеля для пользователя
        portfolio = Portfolio(user_id=next_id)
        portfolio.add_currency("USD", 1000.0)  # Начальный баланс

        # Сохранение портфеля
        db_manager.insert("portfolios", portfolio.to_dict())

        return {
            "user_id": user.user_id,
            "username": user.username,
            "message": f"Пользователь '{username}' успешно зарегистрирован",
        }

    @staticmethod
    @log_action(action_name="LOGIN", verbose=True)
    @validate_input(
        {
            "username": {"type": str, "not_empty": True},
            "password": {"type": str, "not_empty": True},
        }
    )
    def authenticate_user(username: str, password: str) -> Dict[str, Any]:
        """
        Аутентификация пользователя

        Args:
            username: Имя пользователя
            password: Пароль

        Returns:
            Информация об аутентифицированном пользователе

        Raises:
            UserNotFoundError: Если пользователь не найден
            AuthenticationError: Если пароль неверный
        """
        # Поиск пользователя
        user_data = db_manager.find_one(
            "users", lambda u: u["username"].lower() == username.lower()
        )

        if not user_data:
            raise UserNotFoundError(username=username)

        # Проверка пароля
        user = User.from_dict(user_data)

        if not user.verify_password(password):
            raise AuthenticationError()

        # Сохранение сессии
        session_data = {
            "user_id": user.user_id,
            "username": user.username,
            "login_time": datetime.now().isoformat(),
        }

        db_manager.save_data("session", session_data)

        return {
            "user_id": user.user_id,
            "username": user.username,
            "message": f"Вы вошли как '{user.username}'",
        }

    @staticmethod
    @log_action(action_name="LOGOUT")
    def logout_user(user_id: int) -> Dict[str, Any]:
        """
        Выход пользователя из системы

        Args:
            user_id: ID пользователя

        Returns:
            Сообщение об успешном выходе
        """
        # Очистка сессии
        db_manager.save_data("session", {})

        return {"message": "Вы вышли из системы"}

    @staticmethod
    def get_current_session() -> Optional[Dict[str, Any]]:
        """
        Получение текущей сессии

        Returns:
            Данные сессии или None
        """
        try:
            session_data = db_manager.load_data("session", default={})

            if not session_data or "user_id" not in session_data:
                return None

            # Проверка срока действия сессии
            login_time = datetime.fromisoformat(session_data["login_time"])
            session_ttl = timedelta(hours=settings.get_session_ttl_hours())

            if datetime.now() - login_time > session_ttl:
                # Сессия истекла
                db_manager.save_data("session", {})
                return None

            return session_data
        except Exception:
            return None


class PortfolioUseCases:
    """Сценарии использования для работы с портфелями"""

    @staticmethod
    @log_action(action_name="SHOW_PORTFOLIO", verbose=True)
    def get_user_portfolio(user_id: int, base_currency: str = "USD") -> Dict[str, Any]:
        """
        Получение портфеля пользователя

        Args:
            user_id: ID пользователя
            base_currency: Базовая валюта для расчета

        Returns:
            Информация о портфеле

        Raises:
            PortfolioNotFoundError: Если портфель не найден
            CurrencyNotFoundError: Если базовая валюта не поддерживается
        """
        # Проверка поддержки базовой валюты
        if not is_currency_supported(base_currency):
            raise CurrencyNotFoundError(base_currency)

        # Поиск портфеля пользователя
        portfolio_data = db_manager.find_one(
            "portfolios", lambda p: p["user_id"] == user_id
        )

        if not portfolio_data:
            # Создание портфеля по умолчанию
            portfolio = Portfolio(user_id=user_id)
            portfolio.add_currency("USD", 1000.0)
            db_manager.insert("portfolios", portfolio.to_dict())
            portfolio_data = portfolio.to_dict()

        # Загрузка курсов валют
        exchange_rates = ExchangeRateUseCases.get_all_rates()

        # Создание объекта Portfolio
        portfolio = Portfolio.from_dict(portfolio_data)

        # Получение информации о портфеле
        portfolio_info = portfolio.get_portfolio_info(exchange_rates, base_currency)

        # Добавление информации о пользователе
        user_data = db_manager.find_one("users", lambda u: u["user_id"] == user_id)
        if user_data:
            portfolio_info["username"] = user_data["username"]

        return portfolio_info

    @staticmethod
    @log_action(action_name="BUY", verbose=True)
    @validate_input(
        {
            "user_id": {"type": int, "min": 1},
            "currency_code": {"type": str, "not_empty": True},
            "amount": {"type": (int, float), "min": 0.000001},
        }
    )
    def buy_currency(user_id: int, currency_code: str, amount: float) -> Dict[str, Any]:
        """
        Покупка валюты

        Args:
            user_id: ID пользователя
            currency_code: Код покупаемой валюты
            amount: Количество покупаемой валюты

        Returns:
            Результат покупки

        Raises:
            CurrencyNotFoundError: Если валюта не поддерживается
            InsufficientFundsError: Если недостаточно средств
            ApiRequestError: Если не удалось получить курс
        """
        # Проверка поддержки валюты
        if not is_currency_supported(currency_code):
            raise CurrencyNotFoundError(currency_code)

        # Получение курса
        rate = ExchangeRateUseCases.get_exchange_rate(currency_code, "USD")

        if not rate:
            raise ApiRequestError("Не удалось получить курс для покупки")

        # Расчет стоимости в USD
        cost_usd = amount * rate

        # Получение портфеля пользователя
        portfolio_data = db_manager.find_one(
            "portfolios", lambda p: p["user_id"] == user_id
        )

        if not portfolio_data:
            raise PortfolioNotFoundError(user_id)

        portfolio = Portfolio.from_dict(portfolio_data)

        # Проверка наличия USD кошелька и достаточности средств
        usd_wallet = portfolio.get_wallet("USD")
        if not usd_wallet:
            usd_wallet = portfolio.add_currency("USD", 0.0)

        if usd_wallet.balance < cost_usd:
            raise InsufficientFundsError("USD", usd_wallet.balance, cost_usd)

        # Получение или создание кошелька для целевой валюты
        target_wallet = portfolio.get_wallet(currency_code)
        if not target_wallet:
            target_wallet = portfolio.add_currency(currency_code, 0.0)

        # Сохранение старых балансов для логов
        old_usd_balance = usd_wallet.balance
        old_target_balance = target_wallet.balance

        try:
            # Выполнение операции
            usd_wallet.withdraw(cost_usd)
            target_wallet.deposit(amount)

            # Сохранение изменений
            db_manager.update(
                "portfolios",
                lambda p: p["user_id"] == user_id,
                lambda _: portfolio.to_dict(),
            )

            # Получение информации о пользователе для логов
            user_data = db_manager.find_one("users", lambda u: u["user_id"] == user_id)
            username = user_data["username"] if user_data else str(user_id)

            return {
                "username": username,
                "currency_code": currency_code,
                "amount": amount,
                "rate": rate,
                "cost_usd": cost_usd,
                "old_usd_balance": old_usd_balance,
                "new_usd_balance": usd_wallet.balance,
                "old_target_balance": old_target_balance,
                "new_target_balance": target_wallet.balance,
                "message": f"Покупка {amount:.6f} {currency_code} выполнена успешно",
            }

        except Exception as e:
            # В случае ошибки логируем и пробрасываем дальше
            logger.error(
                f"Ошибка при покупке валюты: {e}",
                extra={
                    "user_id": user_id,
                    "currency_code": currency_code,
                    "amount": amount,
                },
            )
            raise

    @staticmethod
    @log_action(action_name="SELL", verbose=True)
    @validate_input(
        {
            "user_id": {"type": int, "min": 1},
            "currency_code": {"type": str, "not_empty": True},
            "amount": {"type": (int, float), "min": 0.000001},
        }
    )
    def sell_currency(
        user_id: int, currency_code: str, amount: float
    ) -> Dict[str, Any]:
        """
        Продажа валюты

        Args:
            user_id: ID пользователя
            currency_code: Код продаваемой валюты
            amount: Количество продаваемой валюты

        Returns:
            Результат продажи

        Raises:
            CurrencyNotFoundError: Если валюта не поддерживается
            InsufficientFundsError: Если недостаточно валюты для продажи
            ApiRequestError: Если не удалось получить курс
        """
        # Проверка поддержки валюты
        if not is_currency_supported(currency_code):
            raise CurrencyNotFoundError(currency_code)

        # Получение курса
        rate = ExchangeRateUseCases.get_exchange_rate(currency_code, "USD")

        if not rate:
            raise ApiRequestError("Не удалось получить курс для продажи")

        # Расчет выручки в USD
        revenue_usd = amount * rate

        # Получение портфеля пользователя
        portfolio_data = db_manager.find_one(
            "portfolios", lambda p: p["user_id"] == user_id
        )

        if not portfolio_data:
            raise PortfolioNotFoundError(user_id)

        portfolio = Portfolio.from_dict(portfolio_data)

        # Проверка наличия кошелька с валютой
        source_wallet = portfolio.get_wallet(currency_code)
        if not source_wallet:
            raise InsufficientFundsError(currency_code, 0, amount)

        # Проверка достаточности средств
        if source_wallet.balance < amount:
            raise InsufficientFundsError(currency_code, source_wallet.balance, amount)

        # Получение или создание USD кошелька
        usd_wallet = portfolio.get_wallet("USD")
        if not usd_wallet:
            usd_wallet = portfolio.add_currency("USD", 0.0)

        # Сохранение старых балансов для логов
        old_source_balance = source_wallet.balance
        old_usd_balance = usd_wallet.balance

        try:
            # Выполнение операции
            source_wallet.withdraw(amount)
            usd_wallet.deposit(revenue_usd)

            # Сохранение изменений
            db_manager.update(
                "portfolios",
                lambda p: p["user_id"] == user_id,
                lambda _: portfolio.to_dict(),
            )

            # Получение информации о пользователе для логов
            user_data = db_manager.find_one("users", lambda u: u["user_id"] == user_id)
            username = user_data["username"] if user_data else str(user_id)

            return {
                "username": username,
                "currency_code": currency_code,
                "amount": amount,
                "rate": rate,
                "revenue_usd": revenue_usd,
                "old_source_balance": old_source_balance,
                "new_source_balance": source_wallet.balance,
                "old_usd_balance": old_usd_balance,
                "new_usd_balance": usd_wallet.balance,
                "message": f"Продажа {amount:.6f} {currency_code} выполнена успешно",
            }

        except Exception as e:
            # В случае ошибки логируем и пробрасываем дальше
            logger.error(
                f"Ошибка при продаже валюты: {e}",
                extra={
                    "user_id": user_id,
                    "currency_code": currency_code,
                    "amount": amount,
                },
            )
            raise


class ExchangeRateUseCases:
    """Сценарии использования для работы с курсами валют"""

    @staticmethod
    @log_action(action_name="GET_RATE")
    @validate_input(
        {
            "from_currency": {"type": str, "not_empty": True},
            "to_currency": {"type": str, "not_empty": True},
        }
    )
    def get_exchange_rate(from_currency: str, to_currency: str) -> Optional[float]:
        """
        Получение курса обмена между валютами

        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта

        Returns:
            Курс обмена или None
        """
        # Если валюты одинаковые
        if from_currency.upper() == to_currency.upper():
            return 1.0

        # Загрузка курсов
        rates_data = db_manager.load_data("rates", default={})

        print(f"DEBUG: Ищем курс {from_currency} → {to_currency}")
        print(
            f"DEBUG: Структура rates_data: {list(rates_data.keys()) if rates_data else 'пусто'}"
        )

        # Пытаемся найти курс в разных форматах
        pair = f"{from_currency.upper()}_{to_currency.upper()}"

        # Вариант 1: Прямо в корне (старый формат)
        if pair in rates_data and isinstance(rates_data[pair], dict):
            rate = rates_data[pair].get("rate")
            if rate:
                print(f"DEBUG: Найден курс в корне: {rate}")
                return rate

        # Вариант 2: В секции "pairs" (новый формат)
        if "pairs" in rates_data and pair in rates_data["pairs"]:
            rate = rates_data["pairs"][pair].get("rate")
            if rate:
                print(f"DEBUG: Найден курс в pairs: {rate}")
                return rate

        # Вариант 3: Обратный курс
        reverse_pair = f"{to_currency.upper()}_{from_currency.upper()}"

        # В корне
        if reverse_pair in rates_data and isinstance(rates_data[reverse_pair], dict):
            reverse_rate = rates_data[reverse_pair].get("rate")
            if reverse_rate and reverse_rate != 0:
                rate = 1.0 / reverse_rate
                print(f"DEBUG: Найден обратный курс в корне: {reverse_rate} → {rate}")
                return rate

        # В секции "pairs"
        if "pairs" in rates_data and reverse_pair in rates_data["pairs"]:
            reverse_rate = rates_data["pairs"][reverse_pair].get("rate")
            if reverse_rate and reverse_rate != 0:
                rate = 1.0 / reverse_rate
                print(f"DEBUG: Найден обратный курс в pairs: {reverse_rate} → {rate}")
                return rate

        print(f"DEBUG: Курс {pair} не найден")
        return None

    @staticmethod
    def get_all_rates() -> Dict[str, float]:
        """
        Получение всех курсов валют

        Returns:
            Словарь с курсами валют
        """
        rates_data = db_manager.load_data("rates", default={})

        # Извлекаем только курсы
        exchange_rates = {}

        for key, value in rates_data.items():
            if key not in ["source", "last_refresh"] and isinstance(value, dict):
                exchange_rates[key] = value.get("rate", 0)

        return exchange_rates

    @staticmethod
    def _refresh_rates() -> bool:
        """
        Обновление курсов валют

        Returns:
            True если обновление успешно, иначе False
        """
        try:
            # В реальном приложении здесь должен быть запрос к API
            # Для демонстрации используем фиктивные данные

            mock_rates = {
                "EUR_USD": {"rate": 1.0786, "updated_at": datetime.now().isoformat()},
                "BTC_USD": {"rate": 59337.21, "updated_at": datetime.now().isoformat()},
                "USD_EUR": {"rate": 0.9271, "updated_at": datetime.now().isoformat()},
                "USD_BTC": {
                    "rate": 0.00001685,
                    "updated_at": datetime.now().isoformat(),
                },
                "EUR_BTC": {
                    "rate": 0.0000156,
                    "updated_at": datetime.now().isoformat(),
                },
                "BTC_EUR": {"rate": 64038.46, "updated_at": datetime.now().isoformat()},
                "USD_GBP": {"rate": 0.79, "updated_at": datetime.now().isoformat()},
                "GBP_USD": {"rate": 1.27, "updated_at": datetime.now().isoformat()},
                "USD_JPY": {"rate": 148.5, "updated_at": datetime.now().isoformat()},
                "JPY_USD": {"rate": 0.0067, "updated_at": datetime.now().isoformat()},
                "USD_CHF": {"rate": 0.88, "updated_at": datetime.now().isoformat()},
                "CHF_USD": {"rate": 1.14, "updated_at": datetime.now().isoformat()},
            }

            rates_data = {
                **mock_rates,
                "source": "MockService",
                "last_refresh": datetime.now().isoformat(),
            }

            db_manager.save_data("rates", rates_data)

            logger.info(
                "Курсы валют обновлены",
                extra={"source": "MockService", "rates_count": len(mock_rates)},
            )

            return True

        except Exception as e:
            logger.error(f"Ошибка при обновлении курсов: {e}")
            raise ApiRequestError(f"Не удалось обновить курсы: {e}")

    @staticmethod
    def get_rate_info(from_currency: str, to_currency: str) -> Dict[str, Any]:
        """
        Получение полной информации о курсе

        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта

        Returns:
            Информация о курсе

        Raises:
            CurrencyNotFoundError: Если валюта не поддерживается
            ApiRequestError: Если не удалось получить курс
        """
        rate = ExchangeRateUseCases.get_exchange_rate(from_currency, to_currency)

        if not rate:
            raise ApiRequestError(
                f"Не удалось получить курс {from_currency}→{to_currency}"
            )

        # Получение информации о валютах
        from_currency_obj = get_currency(from_currency)
        to_currency_obj = get_currency(to_currency)

        return {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": rate,
            "from_currency_info": from_currency_obj.get_display_info(),
            "to_currency_info": to_currency_obj.get_display_info(),
            "inverse_rate": 1.0 / rate if rate != 0 else 0,
            "last_updated": datetime.now().isoformat(),
        }
