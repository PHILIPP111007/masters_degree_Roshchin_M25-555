"""
CLI интерфейс для ValutaTrade Hub
"""

import argparse
import sys
from typing import Any, Dict, Optional

from valutatrade_hub.core.currencies import get_supported_currency_codes
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    AuthenticationError,
    CurrencyNotFoundError,
    InsufficientFundsError,
    UserNotFoundError,
    ValidationError,
)
from valutatrade_hub.core.usecases import (
    ExchangeRateUseCases,
    PortfolioUseCases,
    UserUseCases,
)
from valutatrade_hub.infra.settings import settings
from valutatrade_hub.logging_config import get_logger, setup_logging
from valutatrade_hub.parser_service import RatesStorage, RatesUpdater

logger = get_logger(__name__)


class CryptoPortfolioCLI:
    """CLI интерфейс для управления крипто-портфелем"""

    def __init__(self):
        """Инициализация CLI"""
        self.current_user: Optional[Dict[str, Any]] = None

        # Настройка логирования
        setup_logging(
            log_dir=settings.get_log_dir(),
            log_level=settings.get_log_level(),
            log_format=settings.get_log_format(),
        )

        # Загрузка текущей сессии
        self._load_session()

        # Создание парсера аргументов
        self.parser = self._create_parser()

    def _load_session(self):
        """Загрузка текущей сессии"""
        try:
            self.current_user = UserUseCases.get_current_session()
            if self.current_user:
                logger.info(
                    "Сессия загружена",
                    extra={
                        "username": self.current_user.get("username"),
                        "user_id": self.current_user.get("user_id"),
                    },
                )
        except Exception as e:
            logger.warning(f"Ошибка при загрузке сессии: {e}")

    def _create_parser(self) -> argparse.ArgumentParser:
        """Создание парсера аргументов командной строки"""
        parser = argparse.ArgumentParser(
            description="ValutaTrade Hub - Управление крипто-портфелем",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_help_epilog(),
        )

        subparsers = parser.add_subparsers(
            dest="command", help="Доступные команды", metavar="КОМАНДА"
        )

        # Команда register
        register_parser = subparsers.add_parser(
            "register", help="Регистрация нового пользователя"
        )
        register_parser.add_argument(
            "--username", "-u", required=True, help="Имя пользователя"
        )
        register_parser.add_argument("--password", "-p", required=True, help="Пароль")

        # Команда login
        login_parser = subparsers.add_parser("login", help="Вход в систему")
        login_parser.add_argument(
            "--username", "-u", required=True, help="Имя пользователя"
        )
        login_parser.add_argument("--password", "-p", required=True, help="Пароль")

        # Команда logout
        subparsers.add_parser("logout", help="Выход из системы")

        # Команда show-portfolio
        portfolio_parser = subparsers.add_parser(
            "show-portfolio", help="Показать портфель"
        )
        portfolio_parser.add_argument(
            "--base",
            "-b",
            default=settings.get_default_base_currency(),
            help=f"Базовая валюта (по умолчанию:"
            f"{settings.get_default_base_currency()})",
        )

        # Команда buy
        buy_parser = subparsers.add_parser("buy", help="Купить валюту")
        buy_parser.add_argument(
            "--currency", "-c", required=True, help="Код покупаемой валюты"
        )
        buy_parser.add_argument(
            "--amount",
            "-a",
            type=float,
            required=True,
            help="Количество покупаемой валюты",
        )

        # Команда sell
        sell_parser = subparsers.add_parser("sell", help="Продать валюту")
        sell_parser.add_argument(
            "--currency", "-c", required=True, help="Код продаваемой валюты"
        )
        sell_parser.add_argument(
            "--amount",
            "-a",
            type=float,
            required=True,
            help="Количество продаваемой валюты",
        )

        # Команда get-rate
        rate_parser = subparsers.add_parser("get-rate", help="Получить курс валюты")
        rate_parser.add_argument(
            "--from", "-f", dest="from_currency", required=True, help="Исходная валюта"
        )
        rate_parser.add_argument(
            "--to", "-t", dest="to_currency", required=True, help="Целевая валюта"
        )

        # Команда update-rates
        update_parser = subparsers.add_parser(
            "update-rates", help="Обновить курсы валют"
        )
        update_parser.add_argument(
            "--source",
            choices=["coingecko", "exchangerate"],
            help="Обновить данные только из указанного источника",
        )

        # Команда show-rates
        show_rates_parser = subparsers.add_parser(
            "show-rates", help="Показать курсы из кеша"
        )
        show_rates_parser.add_argument(
            "--currency", "-c", help="Показать курс только для указанной валюты"
        )
        show_rates_parser.add_argument(
            "--top", "-t", type=int, help="Показать N самых дорогих криптовалют"
        )
        show_rates_parser.add_argument(
            "--base", "-b", default="USD", help="Базовая валюта для отображения"
        )

        # Команда list-currencies
        subparsers.add_parser(
            "list-currencies", help="Показать список поддерживаемых валют"
        )

        # Команда help
        subparsers.add_parser("help", help="Показать справку")

        return parser

    def _get_help_epilog(self) -> str:
        """Получение текста помощи"""
        return """
Примеры использования:
  register --username alice --password 1234
  login --username alice --password 1234
  logout
  show-portfolio --base EUR
  buy --currency BTC --amount 0.05
  sell --currency BTC --amount 0.01
  get-rate --from USD --to BTC
  list-currencies
  help
        """

    def run(self):
        """Запуск CLI интерфейса"""
        if len(sys.argv) == 1:
            self.parser.print_help()
            return

        args = self.parser.parse_args()

        # Обработка команды help
        if args.command == "help":
            self.parser.print_help()
            return

        # Обработка команды list-currencies
        if args.command == "list-currencies":
            self._list_currencies()
            return

        # Обработка команды logout
        if args.command == "logout":
            self._logout()
            return

        # Проверка авторизации для защищенных команд
        auth_required_commands = ["show-portfolio", "buy", "sell"]
        if args.command in auth_required_commands and not self.current_user:
            print("Ошибка: Сначала выполните login")
            return

        # Выполнение команды
        try:
            if args.command == "register":
                self._register(args)
            elif args.command == "login":
                self._login(args)
            elif args.command == "show-portfolio":
                self._show_portfolio(args)
            elif args.command == "buy":
                self._buy(args)
            elif args.command == "sell":
                self._sell(args)
            elif args.command == "get-rate":
                self._get_rate(args)
            elif args.command == "update-rates":
                self.update_rates(args)
            elif args.command == "show-rates":
                self.show_rates(args)
            else:
                self.parser.print_help()

        except ValidationError as e:
            print(f"Ошибка валидации: {e}")
        except UserNotFoundError as e:
            print(f"Ошибка: {e}")
        except AuthenticationError as e:
            print(f"Ошибка аутентификации: {e}")
        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e}")
            print(
                "Используйте команду 'list-currencies'"
                "для просмотра поддерживаемых валют"
            )
        except InsufficientFundsError as e:
            print(f"Ошибка: {e}")
        except ApiRequestError as e:
            print(f"Ошибка: {e}")
            print("Повторите попытку позже или проверьте подключение к сети")
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            logger.error(f"Неизвестная ошибка при выполнении команды: {e}")

    def _register(self, args):
        """Обработка команды register"""
        result = UserUseCases.register_user(args.username, args.password)
        print(f"✓ {result['message']} (ID: {result['user_id']})")

    def _login(self, args):
        """Обработка команды login"""
        result = UserUseCases.authenticate_user(args.username, args.password)
        self.current_user = UserUseCases.get_current_session()
        print(f"✓ {result['message']}")

    def _logout(self):
        """Обработка команды logout"""
        if self.current_user:
            result = UserUseCases.logout_user(self.current_user["user_id"])
            self.current_user = None
            print(f"✓ {result['message']}")
        else:
            print("Вы не вошли в систему")

    def update_rates(self, args):
        """Обработка команды update-rates"""

        try:
            updater = RatesUpdater()

            if args.source:
                result = updater.run_update(source=args.source)
                source_msg = f" from {args.source}"
            else:
                result = updater.run_update()
                source_msg = ""

            if result["success"]:
                print(f"\n✓ Update successful{source_msg}")
                print(f"  Rates updated: {result['rates_count']}")
                print(f"  Sources: {', '.join(result['sources_updated'])}")
                print(f"  Last refresh: {result['last_refresh']}")

                if result["errors"]:
                    print("\n⚠  Warnings:")
                    for error in result["errors"]:
                        print(f"  {error}")
            else:
                print(f"\n✗ Update failed{source_msg}")
                if result["errors"]:
                    print("  Errors:")
                    for error in result["errors"]:
                        print(f"  {error}")

        except Exception as e:
            print(f"\n✗ Error during update: {str(e)}")
            print("  Check logs/parser.log for details")

    def show_rates(self, args):
        """Обработка команды show-rates"""
        try:
            storage = RatesStorage()
            rates_data = storage.load_current_rates()

            if not rates_data.get("pairs"):
                print(
                    "Локальный кеш курсов пуст. Выполните "
                    "'update-rates', чтобы загрузить данные."
                )
                return

            pairs = rates_data["pairs"]
            last_refresh = rates_data.get("last_refresh", "Unknown")
            source = rates_data.get("source", "Unknown")

            print(f"\nRates from cache (updated at {last_refresh}, source: {source}):")
            print("=" * 60)

            # Фильтрация по валюте
            if args.currency:
                currency = args.currency.upper()
                filtered_pairs = {
                    k: v
                    for k, v in pairs.items()
                    if k.startswith(f"{currency}_") or k.endswith(f"_{currency}")
                }
                if not filtered_pairs:
                    print(f"Курс для '{args.currency}' не найден в кеше.")
                    return
                pairs = filtered_pairs

            # Сортировка и ограничение
            sorted_pairs = sorted(
                pairs.items(), key=lambda x: x[1]["rate"], reverse=True
            )

            if args.top:
                sorted_pairs = sorted_pairs[: args.top]

            # Вывод
            for pair_key, data in sorted_pairs:
                rate = data["rate"]
                updated = data["updated_at"]
                source = data.get("source", "Unknown")
                print(
                    f"  {pair_key}: {rate:.6f} (updated: {updated}, source: {source})"
                )

            print(f"\nTotal rates shown: {len(sorted_pairs)}")

        except Exception as e:
            print(f"Ошибка при чтении кеша: {str(e)}")

    def _show_portfolio(self, args):
        """Обработка команды show-portfolio"""
        portfolio_info = PortfolioUseCases.get_user_portfolio(
            self.current_user["user_id"], args.base
        )

        print(f"\nПортфель пользователя '{portfolio_info.get('username', 'Unknown')}'")
        print(f"Базовая валюта: {args.base}")
        print("=" * 60)

        total_value = portfolio_info["total_value"]
        wallets = portfolio_info["wallets"]

        if not wallets:
            print("Портфель пуст")
            return

        # Вывод информации о кошельках
        for currency_code, wallet_info in sorted(wallets.items()):
            balance = wallet_info["balance"]
            value_in_base = wallet_info["value_in_base"]
            currency_info = wallet_info.get("currency_info", "")

            print(f"\n{currency_code}:")
            print(f"  Баланс: {balance:.6f}")
            print(f"  Стоимость в {args.base}: {value_in_base:.2f}")
            if currency_info:
                print(f"  {currency_info}")

        print("\n" + "=" * 60)
        print(f"ИТОГО в {args.base}: {total_value:,.2f}")
        print(f"Количество валют: {len(wallets)}")

    def _buy(self, args):
        """Обработка команды buy"""
        result = PortfolioUseCases.buy_currency(
            self.current_user["user_id"], args.currency, args.amount
        )

        print(f"\n✓ {result['message']}")
        print(f"Курс: {result['rate']:.6f} USD/{args.currency}")
        print(f"Стоимость: {result['cost_usd']:.2f} USD")
        print("\nИзменения в портфеле:")
        print(
            f"  {args.currency}: {result['old_target_balance']:.6f}"
            f" → {result['new_target_balance']:.6f}"
        )
        print(
            f"  USD: {result['old_usd_balance']:.2f} → {result['new_usd_balance']:.2f}"
        )

    def _sell(self, args):
        """Обработка команды sell"""
        result = PortfolioUseCases.sell_currency(
            self.current_user["user_id"], args.currency, args.amount
        )

        print(f"\n✓ {result['message']}")
        print(f"Курс: {result['rate']:.6f} USD/{args.currency}")
        print(f"Выручка: {result['revenue_usd']:.2f} USD")
        print("\nИзменения в портфеле:")
        print(
            f"  {args.currency}: {result['old_source_balance']:.6f}"
            f" → {result['new_source_balance']:.6f}"
        )
        print(
            f"  USD: {result['old_usd_balance']:.2f} → {result['new_usd_balance']:.2f}"
        )

    def _get_rate(self, args):
        """Обработка команды get-rate"""
        rate_info = ExchangeRateUseCases.get_rate_info(
            args.from_currency, args.to_currency
        )

        print(f"\nКурс {args.from_currency} → {args.to_currency}")
        print("=" * 40)
        print(f"1 {args.from_currency} = {rate_info['rate']:.8f} {args.to_currency}")
        print(
            f"1 {args.to_currency} = {rate_info['inverse_rate']:.8f}"
            f" {args.from_currency}"
        )
        print("\nИнформация о валютах:")
        print(f"  {rate_info['from_currency_info']}")
        print(f"  {rate_info['to_currency_info']}")

    def _list_currencies(self):
        """Обработка команды list-currencies"""
        supported_codes = get_supported_currency_codes()

        print(f"\nПоддерживаемые валюты ({len(supported_codes)}):")
        print("=" * 60)

        # Разделение на фиатные и криптовалюты
        fiat_currencies = []
        crypto_currencies = []

        for code in sorted(supported_codes):
            if code in ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY", "RUB"]:
                fiat_currencies.append(code)
            else:
                crypto_currencies.append(code)

        if fiat_currencies:
            print("\nФиатные валюты:")
            print(", ".join(fiat_currencies))

        if crypto_currencies:
            print("\nКриптовалюты:")
            print(", ".join(crypto_currencies))

        print("\nИспользуйте 'get-rate --from USD --to BTC' для получения курса")
        print("Используйте 'buy --currency BTC --amount 0.01' для покупки")
