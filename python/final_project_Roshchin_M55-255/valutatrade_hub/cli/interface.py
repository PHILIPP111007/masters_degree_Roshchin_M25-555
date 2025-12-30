# команды

import json
import os
import sys
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
import argparse
from pathlib import Path

from valutatrade_hub.core.models import User, Wallet, Portfolio


class CryptoPortfolioCLI:
    def __init__(self):
        """Инициализация CLI интерфейса"""
        self.current_user: Optional[User] = None
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

        # Пути к файлам данных
        self.users_file = self.data_dir / "users.json"
        self.portfolios_file = self.data_dir / "portfolios.json"
        self.rates_file = self.data_dir / "rates.json"
        self.session_file = self.data_dir / "session.json"  # Новый файл для сессии

        # Инициализация файлов, если они не существуют
        self._init_data_files()

        # Загружаем сессию, если она существует
        self._load_session()

        # Парсер аргументов командной строки
        self.parser = self._create_parser()

    def _init_data_files(self):
        """Инициализирует пустые файлы данных, если они не существуют"""
        if not self.users_file.exists():
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

        if not self.portfolios_file.exists():
            with open(self.portfolios_file, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

        if not self.rates_file.exists():
            self._init_rates_file()

    def _init_rates_file(self):
        """Инициализирует файл с курсами валют"""
        rates = {
            "EUR_USD": {"rate": 1.0786, "updated_at": datetime.now().isoformat()},
            "BTC_USD": {"rate": 59337.21, "updated_at": datetime.now().isoformat()},
            "USD_EUR": {"rate": 0.9271, "updated_at": datetime.now().isoformat()},
            "USD_BTC": {"rate": 0.00001685, "updated_at": datetime.now().isoformat()},
            "EUR_BTC": {"rate": 0.0000156, "updated_at": datetime.now().isoformat()},
            "BTC_EUR": {"rate": 64038.46, "updated_at": datetime.now().isoformat()},
            "source": "MockService",
            "last_refresh": datetime.now().isoformat(),
        }

        with open(self.rates_file, "w", encoding="utf-8") as f:
            json.dump(rates, f, indent=2, ensure_ascii=False)

    def _load_session(self):
        """Загружает текущую сессию из файла"""
        if not self.session_file.exists():
            return

        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            # Проверяем время сессии (например, сессия действительна 24 часа)
            if "login_time" in session_data:
                login_time = datetime.fromisoformat(session_data["login_time"])
                if datetime.now() - login_time > timedelta(hours=24):
                    print("Сессия истекла. Пожалуйста, войдите снова.")
                    self.session_file.unlink(missing_ok=True)
                    return

            # Загружаем данные пользователя
            if "user_id" in session_data and "username" in session_data:
                # Создаем объект пользователя
                self.current_user = User(
                    user_id=session_data["user_id"],
                    username=session_data["username"],
                    password="",
                )

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Ошибка загрузки сессии: {e}")
            self.session_file.unlink(missing_ok=True)

    def _create_parser(self) -> argparse.ArgumentParser:
        """Создает парсер аргументов командной строки"""
        parser = argparse.ArgumentParser(
            description="Crypto Portfolio Manager - CLI интерфейс",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Примеры использования:
  register --username alice --password 1234
  login --username alice --password 1234
  show-portfolio
  show-portfolio --base EUR
  buy --currency BTC --amount 0.05
  sell --currency BTC --amount 0.01
  get-rate --from USD --to BTC
            """,
        )

        subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

        # Команда register
        register_parser = subparsers.add_parser(
            "register", help="Регистрация нового пользователя"
        )
        register_parser.add_argument(
            "--username", required=True, help="Имя пользователя"
        )
        register_parser.add_argument("--password", required=True, help="Пароль")

        # Команда login
        login_parser = subparsers.add_parser("login", help="Вход в систему")
        login_parser.add_argument("--username", required=True, help="Имя пользователя")
        login_parser.add_argument("--password", required=True, help="Пароль")

        # Команда show-portfolio
        portfolio_parser = subparsers.add_parser(
            "show-portfolio", help="Показать портфель"
        )
        portfolio_parser.add_argument(
            "--base",
            default="USD",
            help="Базовая валюта для расчета (по умолчанию: USD)",
        )

        # Команда buy
        buy_parser = subparsers.add_parser("buy", help="Купить валюту")
        buy_parser.add_argument(
            "--currency", required=True, help="Код покупаемой валюты (например: BTC)"
        )
        buy_parser.add_argument(
            "--amount", type=float, required=True, help="Количество покупаемой валюты"
        )

        # Команда sell
        sell_parser = subparsers.add_parser("sell", help="Продать валюту")
        sell_parser.add_argument(
            "--currency", required=True, help="Код продаваемой валюты"
        )
        sell_parser.add_argument(
            "--amount", type=float, required=True, help="Количество продаваемой валюты"
        )

        # Команда get-rate
        rate_parser = subparsers.add_parser("get-rate", help="Получить курс валюты")
        rate_parser.add_argument(
            "--from", dest="from_currency", required=True, help="Исходная валюта"
        )
        rate_parser.add_argument(
            "--to", dest="to_currency", required=True, help="Целевая валюта"
        )

        return parser

    def _generate_salt(self, length: int = 8) -> str:
        """Генерирует случайную соль для хеширования пароля"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _hash_password(self, password: str, salt: str) -> str:
        """Хеширует пароль с использованием соли"""
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def _load_users(self) -> list:
        """Загружает пользователей из файла"""
        with open(self.users_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_users(self, users: list):
        """Сохраняет пользователей в файл"""
        with open(self.users_file, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)

    def _load_portfolios(self) -> list:
        """Загружает портфели из файла"""
        with open(self.portfolios_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_portfolios(self, portfolios: list):
        """Сохраняет портфели в файл"""
        with open(self.portfolios_file, "w", encoding="utf-8") as f:
            json.dump(portfolios, f, indent=2, ensure_ascii=False)

    def _load_rates(self) -> dict:
        """Загружает курсы валют из файла"""
        with open(self.rates_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_rates(self, rates: dict):
        """Сохраняет курсы валют в файл"""
        with open(self.rates_file, "w", encoding="utf-8") as f:
            json.dump(rates, f, indent=2, ensure_ascii=False)

    def _get_next_user_id(self) -> int:
        """Возвращает следующий доступный ID пользователя"""
        users = self._load_users()
        if not users:
            return 1
        return max(user["user_id"] for user in users) + 1

    def _get_exchange_rate(
        self, from_currency: str, to_currency: str
    ) -> Optional[float]:
        """
        Получает курс обмена между валютами.
        В реальном приложении здесь должен быть вызов API.
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return 1.0

        rates = self._load_rates()
        pair = f"{from_currency}_{to_currency}"

        # Проверяем свежесть данных (5 минут)
        if pair in rates:
            rate_data = rates[pair]
            updated_at = datetime.fromisoformat(rate_data["updated_at"])
            if datetime.now() - updated_at < timedelta(minutes=5):
                return rate_data["rate"]

        # Если данные устарели или отсутствуют, используем заглушку
        # В реальном приложении здесь должен быть запрос к Parser Service
        mock_rates = {
            "USD_EUR": 0.92,
            "EUR_USD": 1.09,
            "USD_BTC": 0.000025,
            "BTC_USD": 40000.0,
            "EUR_BTC": 0.000027,
            "BTC_EUR": 37000.0,
            "USD_GBP": 0.79,
            "GBP_USD": 1.27,
            "USD_JPY": 148.5,
            "JPY_USD": 0.0067,
        }

        if pair in mock_rates:
            # Обновляем кеш
            rates[pair] = {
                "rate": mock_rates[pair],
                "updated_at": datetime.now().isoformat(),
            }
            rates["source"] = "MockService"
            rates["last_refresh"] = datetime.now().isoformat()
            self._save_rates(rates)
            return mock_rates[pair]

        return None

    def _get_user_portfolio(self, user_id: int) -> Optional[Portfolio]:
        """Получает портфель пользователя по ID"""
        portfolios_data = self._load_portfolios()

        for portfolio_data in portfolios_data:
            if portfolio_data["user_id"] == user_id:
                wallets = {}
                for currency_code, wallet_data in portfolio_data["wallets"].items():
                    wallets[currency_code] = Wallet.from_dict(wallet_data)
                return Portfolio(user_id=user_id, wallets=wallets)

        return None

    def _save_user_portfolio(self, portfolio: Portfolio):
        """Сохраняет портфель пользователя"""
        portfolios_data = self._load_portfolios()

        # Ищем существующий портфель
        for i, portfolio_data in enumerate(portfolios_data):
            if portfolio_data["user_id"] == portfolio.user_id:
                portfolios_data[i] = portfolio.to_dict()
                break
        else:
            # Если не нашли, добавляем новый
            portfolios_data.append(portfolio.to_dict())

        self._save_portfolios(portfolios_data)

    def register(self, args):
        """Обрабатывает команду register"""
        username = args.username.strip()
        password = args.password

        # Валидация
        if not username:
            print("Ошибка: Имя пользователя не может быть пустым")
            return

        if len(password) < 4:
            print("Ошибка: Пароль должен быть не короче 4 символов")
            return

        # Проверка уникальности username
        users = self._load_users()
        for user in users:
            if user["username"].lower() == username.lower():
                print(f"Ошибка: Имя пользователя '{username}' уже занято")
                return

        # Создание нового пользователя
        user_id = self._get_next_user_id()
        salt = self._generate_salt()
        hashed_password = self._hash_password(password, salt)

        new_user = {
            "user_id": user_id,
            "username": username,
            "hashed_password": hashed_password,
            "salt": salt,
            "registration_date": datetime.now().isoformat(),
        }

        users.append(new_user)
        self._save_users(users)

        # Создание пустого портфеля
        portfolio = Portfolio(user_id=user_id)
        portfolio.add_currency("USD", 0.0)  # Создаем USD кошелек по умолчанию
        self._save_user_portfolio(portfolio)

        print(
            f"Пользователь '{username}' зарегистрирован (id={user_id}). Войдите: login --username {username} --password ****"
        )

    def login(self, args):
        """Обрабатывает команду login"""
        username = args.username.strip()
        password = args.password

        users = self._load_users()

        # Поиск пользователя
        user_data = None
        for user in users:
            if user["username"].lower() == username.lower():
                user_data = user
                break

        if not user_data:
            print(f"Ошибка: Пользователь '{username}' не найден")
            return

        # Проверка пароля
        salt = user_data["salt"]
        hashed_password = self._hash_password(password, salt)

        if hashed_password != user_data["hashed_password"]:
            print("Ошибка: Неверный пароль")
            return

        # Создаем объект User
        self.current_user = User(
            user_id=user_data["user_id"],
            username=user_data["username"],
            password="",  # Пароль не нужен, т.к. мы уже прошли аутентификацию
        )
        self.current_user._hashed_password = user_data["hashed_password"]
        self.current_user._salt = user_data["salt"]
        self.current_user._registration_date = datetime.fromisoformat(
            user_data["registration_date"]
        )

        print(f"Вы вошли как '{username}'")

    def show_portfolio(self, args):
        """Обрабатывает команду show-portfolio"""
        if not self.current_user:
            print("Ошибка: Сначала выполните login")
            return

        base_currency = args.base.upper()

        # Загружаем портфель пользователя
        portfolio = self._get_user_portfolio(self.current_user.user_id)
        if not portfolio:
            print(f"Портфель пользователя '{self.current_user.username}' не найден")
            return

        wallets = portfolio.wallets
        if not wallets:
            print(f"Портфель пользователя '{self.current_user.username}' пуст")
            return

        print(
            f"\nПортфель пользователя '{self.current_user.username}' (база: {base_currency}):"
        )
        print("-" * 50)

        total_value = 0.0

        for currency_code, wallet in sorted(wallets.items()):
            balance = wallet.balance

            if currency_code == base_currency:
                value_in_base = balance
            else:
                rate = self._get_exchange_rate(currency_code, base_currency)
                if rate:
                    value_in_base = balance * rate
                else:
                    print(f"  - {currency_code}: {balance:.4f}  → Курс недоступен")
                    continue

            total_value += value_in_base
            print(
                f"  - {currency_code}: {balance:10.4f}  → {value_in_base:10.2f} {base_currency}"
            )

        print("-" * 50)
        print(f"  ИТОГО: {total_value:>20.2f} {base_currency}\n")

    def buy(self, args):
        """Обрабатывает команду buy"""
        if not self.current_user:
            print("Ошибка: Сначала выполните login")
            return

        currency = args.currency.upper()
        amount = args.amount

        # Валидация
        if amount <= 0:
            print("Ошибка: 'amount' должен быть положительным числом")
            return

        if len(currency) != 3:
            print("Ошибка: Код валюты должен содержать 3 символа")
            return

        # Загружаем портфель
        portfolio = self._get_user_portfolio(self.current_user.user_id)
        if not portfolio:
            print("Ошибка: Портфель не найден")
            return

        # Получаем курс
        rate = self._get_exchange_rate(currency, "USD")
        if not rate:
            print(f"Ошибка: Не удалось получить курс для {currency}→USD")
            return

        # Вычисляем стоимость в USD
        cost_usd = amount * rate

        # Проверяем наличие USD кошелька и достаточность средств
        usd_wallet = portfolio.get_wallet("USD")
        if not usd_wallet:
            print("Ошибка: USD кошелек не найден")
            return

        if usd_wallet.balance < cost_usd:
            print(
                f"Ошибка: Недостаточно средств. Нужно: {cost_usd:.2f} USD, доступно: {usd_wallet.balance:.2f} USD"
            )
            return

        try:
            # Получаем или создаем кошелек для целевой валюты
            target_wallet = portfolio.get_wallet(currency)
            old_balance = target_wallet.balance if target_wallet else 0.0

            if not target_wallet:
                target_wallet = portfolio.add_currency(currency)

            # Выполняем покупку
            usd_wallet.withdraw(cost_usd)
            target_wallet.deposit(amount)

            # Сохраняем изменения
            self._save_user_portfolio(portfolio)

            # Выводим результат
            print(
                f"\nПокупка выполнена: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}"
            )
            print("Изменения в портфеле:")
            print(
                f"  - {currency}: было {old_balance:.4f} → стало {target_wallet.balance:.4f}"
            )
            print(
                f"  - USD: было {usd_wallet.balance + cost_usd:.2f} → стало {usd_wallet.balance:.2f}"
            )
            print(f"Оценочная стоимость покупки: {cost_usd:.2f} USD\n")

        except ValueError as e:
            print(f"Ошибка: {e}")

    def sell(self, args):
        """Обрабатывает команду sell"""
        if not self.current_user:
            print("Ошибка: Сначала выполните login")
            return

        currency = args.currency.upper()
        amount = args.amount

        # Валидация
        if amount <= 0:
            print("Ошибка: 'amount' должен быть положительным числом")
            return

        if len(currency) != 3:
            print("Ошибка: Код валюты должен содержать 3 символа")
            return

        # Загружаем портфель
        portfolio = self._get_user_portfolio(self.current_user.user_id)
        if not portfolio:
            print("Ошибка: Портфель не найден")
            return

        # Проверяем наличие кошелька с валютой
        source_wallet = portfolio.get_wallet(currency)
        if not source_wallet:
            print(
                f"Ошибка: У вас нет кошелька '{currency}'. Добавьте валюту: она создаётся автоматически при первой покупке."
            )
            return

        # Проверяем достаточность средств
        if source_wallet.balance < amount:
            print(
                f"Ошибка: Недостаточно средств: доступно {source_wallet.balance:.4f} {currency}, требуется {amount:.4f} {currency}"
            )
            return

        # Получаем курс
        rate = self._get_exchange_rate(currency, "USD")
        if not rate:
            print(f"Ошибка: Не удалось получить курс для {currency}→USD")
            return

        # Вычисляем выручку в USD
        revenue_usd = amount * rate

        # Проверяем наличие USD кошелька
        usd_wallet = portfolio.get_wallet("USD")
        if not usd_wallet:
            print("Ошибка: USD кошелек не найден")
            return

        try:
            # Сохраняем старые балансы
            old_source_balance = source_wallet.balance
            old_usd_balance = usd_wallet.balance

            # Выполняем продажу
            source_wallet.withdraw(amount)
            usd_wallet.deposit(revenue_usd)

            # Сохраняем изменения
            self._save_user_portfolio(portfolio)

            # Выводим результат
            print(
                f"\nПродажа выполнена: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}"
            )
            print("Изменения в портфеле:")
            print(
                f"  - {currency}: было {old_source_balance:.4f} → стало {source_wallet.balance:.4f}"
            )
            print(
                f"  - USD: было {old_usd_balance:.2f} → стало {usd_wallet.balance:.2f}"
            )
            print(f"Оценочная выручка: {revenue_usd:.2f} USD\n")

        except ValueError as e:
            print(f"Ошибка: {e}")

    def get_rate(self, args):
        """Обрабатывает команду get-rate"""
        from_currency = args.from_currency.upper()
        to_currency = args.to_currency.upper()

        # Валидация
        if len(from_currency) != 3 or len(to_currency) != 3:
            print("Ошибка: Коды валют должны содержать 3 символа")
            return

        # Получаем прямой курс
        rate = self._get_exchange_rate(from_currency, to_currency)
        if not rate:
            print(
                f"Ошибка: Курс {from_currency}→{to_currency} недоступен. Повторите попытку позже."
            )
            return

        # Получаем обратный курс
        reverse_rate = self._get_exchange_rate(to_currency, from_currency)

        # Получаем время обновления
        rates = self._load_rates()
        pair = f"{from_currency}_{to_currency}"

        if pair in rates:
            updated_at = datetime.fromisoformat(rates[pair]["updated_at"])
            updated_str = updated_at.strftime("%Y-%m-%d %H:%M:%S")
        else:
            updated_str = "только что"

        print(
            f"\nКурс {from_currency}→{to_currency}: {rate:.8f} (обновлено: {updated_str})"
        )

        if reverse_rate:
            print(f"Обратный курс {to_currency}→{from_currency}: {reverse_rate:.8f}")

        print()

    def run(self):
        """Запускает CLI интерфейс"""
        if len(sys.argv) == 1:
            self.parser.print_help()
            return

        args = self.parser.parse_args()

        if args.command == "register":
            self.register(args)
        elif args.command == "login":
            self.login(args)
        elif args.command == "show-portfolio":
            self.show_portfolio(args)
        elif args.command == "buy":
            self.buy(args)
        elif args.command == "sell":
            self.sell(args)
        elif args.command == "get-rate":
            self.get_rate(args)
        else:
            self.parser.print_help()
