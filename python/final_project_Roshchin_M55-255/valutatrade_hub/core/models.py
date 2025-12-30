# реализация классов

import hashlib
import secrets
import string
from datetime import datetime
from typing import Dict, Optional


class User:
    def __init__(
        self,
        user_id: int,
        username: str,
        password: str,
        registration_date: datetime = None,
    ):
        """
        Конструктор класса User

        Args:
            user_id: уникальный идентификатор пользователя
            username: имя пользователя
            password: пароль пользователя
            registration_date: дата регистрации (по умолчанию текущее время)
        """

        self._user_id = user_id
        self.username = username  # Используем сеттер для проверки
        self._salt = self._generate_salt()
        self._hashed_password = self._hash_password(password)
        self._registration_date = registration_date or datetime.now()

    def _generate_salt(self, length: int = 8) -> str:
        """Генерирует случайную соль"""

        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _hash_password(self, password: str) -> str:
        """Хеширует пароль с использованием соли"""

        return hashlib.sha256((password + self._salt).encode()).hexdigest()

    @property
    def user_id(self) -> int:
        """Геттер для уникального идентификатора пользователя"""

        return self._user_id

    @user_id.setter
    def user_id(self, value: int):
        """Сеттер для уникального идентификатора пользователя"""

        if not isinstance(value, int):
            raise ValueError("User ID должен быть целым числом")
        if value <= 0:
            raise ValueError("User ID должен быть положительным числом")
        self._user_id = value

    @property
    def username(self) -> str:
        """Геттер для имени пользователя"""

        return self._username

    @username.setter
    def username(self, value: str):
        """Сеттер для имени пользователя"""

        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value.strip()

    @property
    def hashed_password(self) -> str:
        """Геттер для хешированного пароля"""

        return self._hashed_password

    @property
    def salt(self) -> str:
        """Геттер для соли"""

        return self._salt

    @property
    def registration_date(self) -> datetime:
        """Геттер для даты регистрации"""

        return self._registration_date

    @registration_date.setter
    def registration_date(self, value: datetime):
        """Сеттер для даты регистрации"""

        if not isinstance(value, datetime):
            raise ValueError("Дата регистрации должна быть объектом datetime")
        self._registration_date = value

    def get_user_info(self) -> dict:
        """Выводит информацию о пользователе (без пароля)"""

        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def change_password(self, new_password: str) -> bool:
        """Изменяет пароль пользователя"""

        if len(new_password) < 4:
            raise ValueError("Пароль должен содержать не менее 4 символов")

        # Генерируем новую соль и хешируем новый пароль
        self._salt = self._generate_salt()
        self._hashed_password = self._hash_password(new_password)
        return True

    def verify_password(self, password: str) -> bool:
        """Проверяет введённый пароль на совпадение"""

        # Хешируем введённый пароль с текущей солью
        test_hash = hashlib.sha256((password + self._salt).encode()).hexdigest()
        return test_hash == self._hashed_password

    def to_dict(self) -> dict:
        """Преобразует объект User в словарь для сохранения в JSON"""

        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Создаёт объект User из словаря (например, из JSON)"""

        user = cls(
            user_id=data["user_id"],
            username=data["username"],
            password="dummy",  # Временный пароль, т.к. хеш уже есть
        )
        # Заменяем временные значения на реальные из данных
        user._hashed_password = data["hashed_password"]
        user._salt = data["salt"]
        user._registration_date = datetime.fromisoformat(data["registration_date"])
        return user

    def __str__(self) -> str:
        """Строковое представление пользователя"""

        return f"User(id={self._user_id}, username='{self._username}')"

    def __repr__(self) -> str:
        """Представление объекта для отладки"""

        return f"User(user_id={self._user_id}, username='{self._username}', registration_date={self._registration_date})"


class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0):
        """
        Конструктор класса Wallet

        Args:
            currency_code: код валюты (например, "USD", "BTC")
            balance: начальный баланс (по умолчанию 0.0)
        """

        self.currency_code = currency_code  # Используем сеттер для проверки
        self.balance = balance  # Используем сеттер для проверки

    @property
    def currency_code(self) -> str:
        """Геттер для кода валюты"""

        return self._currency_code

    @currency_code.setter
    def currency_code(self, value: str):
        """Сеттер для кода валюты"""

        if not value or not isinstance(value, str):
            raise ValueError("Код валюты должен быть непустой строкой")
        if len(value.strip()) != 3:
            raise ValueError("Код валюты должен содержать ровно 3 символа")
        self._currency_code = value.strip().upper()

    @property
    def balance(self) -> float:
        """Геттер для баланса"""

        return self._balance

    @balance.setter
    def balance(self, value: float):
        """Сеттер для баланса с проверкой на отрицательные значения"""

        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    def deposit(self, amount: float) -> bool:
        """
        Пополнение баланса

        Args:
            amount: сумма для пополнения

        Returns:
            True если операция успешна

        Raises:
            ValueError: если сумма некорректна
        """

        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")

        self.balance += amount
        return True

    def withdraw(self, amount: float) -> bool:
        """
        Снятие средств с кошелька

        Args:
            amount: сумма для снятия

        Returns:
            True если операция успешна

        Raises:
            ValueError: если сумма некорректна или недостаточно средств
        """

        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        if amount > self.balance:
            raise ValueError(f"Недостаточно средств. Доступно: {self.balance}")

        self.balance -= amount
        return True

    def get_balance_info(self) -> dict:
        """Вывод информации о текущем балансе"""

        return {
            "currency_code": self.currency_code,
            "balance": self.balance,
            "balance_formatted": f"{self.balance:.2f} {self.currency_code}",
        }

    def to_dict(self) -> dict:
        """Преобразует объект Wallet в словарь для сохранения в JSON"""

        return {"currency_code": self.currency_code, "balance": self.balance}

    @classmethod
    def from_dict(cls, data: dict):
        """Создаёт объект Wallet из словаря"""

        return cls(currency_code=data["currency_code"], balance=data["balance"])

    def __str__(self) -> str:
        """Строковое представление кошелька"""

        return f"Wallet({self.currency_code}: {self.balance:.2f})"

    def __repr__(self) -> str:
        """Представление объекта для отладки"""

        return f"Wallet(currency_code='{self.currency_code}', balance={self.balance})"

    def __eq__(self, other) -> bool:
        """Сравнение кошельков по коду валюты"""

        if not isinstance(other, Wallet):
            return False
        return self.currency_code == other.currency_code


class Portfolio:
    # Фиктивные курсы валют для демонстрации
    # В реальном приложении эти данные должны получаться из API
    EXCHANGE_RATES = {
        "USD": {"USD": 1.0, "EUR": 0.92, "BTC": 0.000025, "GBP": 0.79, "JPY": 148.5},
        "EUR": {"USD": 1.09, "EUR": 1.0, "BTC": 0.000027, "GBP": 0.86, "JPY": 161.4},
        "BTC": {
            "USD": 40000.0,
            "EUR": 37000.0,
            "BTC": 1.0,
            "GBP": 31600.0,
            "JPY": 5940000.0,
        },
        "GBP": {"USD": 1.27, "EUR": 1.16, "BTC": 0.000032, "GBP": 1.0, "JPY": 188.0},
        "JPY": {
            "USD": 0.0067,
            "EUR": 0.0062,
            "BTC": 0.00000017,
            "GBP": 0.0053,
            "JPY": 1.0,
        },
    }

    def __init__(self, user_id: int, wallets: Dict[str, Wallet] = None):
        """
        Конструктор класса Portfolio

        Args:
            user_id: уникальный идентификатор пользователя
            wallets: словарь кошельков пользователя
        """

        self._user_id = user_id
        self._wallets = wallets or {}

    @property
    def user_id(self) -> int:
        """Геттер для ID пользователя"""

        return self._user_id

    @user_id.setter
    def user_id(self, value: int):
        """Сеттер для ID пользователя"""

        if not isinstance(value, int):
            raise ValueError("ID пользователя должен быть целым числом")
        if value <= 0:
            raise ValueError("ID пользователя должен быть положительным числом")
        self._user_id = value

    @property
    def wallets(self) -> Dict[str, Wallet]:
        """Геттер, возвращающий копию словаря кошельков"""

        return self._wallets.copy()

    @property
    def user(self) -> Optional[User]:
        """Геттер, возвращающий объект пользователя (заглушка)"""

        # В реальном приложении здесь должна быть логика получения пользователя из БД
        # Для демонстрации возвращаем None или можно реализовать связь с UserManager
        return None

    def add_currency(self, currency_code: str, initial_balance: float = 0.0) -> Wallet:
        """
        Добавляет новый кошелёк в портфель

        Args:
            currency_code: код валюты
            initial_balance: начальный баланс (по умолчанию 0.0)

        Returns:
            Созданный объект Wallet

        Raises:
            ValueError: если валюта уже существует или код валюты некорректен
        """

        currency_code = currency_code.upper()

        # Проверяем, что валюта еще не существует в портфеле
        if currency_code in self._wallets:
            raise ValueError(f"Валюта {currency_code} уже существует в портфеле")

        # Создаем новый кошелек
        wallet = Wallet(currency_code, initial_balance)
        self._wallets[currency_code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Optional[Wallet]:
        """
        Возвращает объект Wallet по коду валюты

        Args:
            currency_code: код валюты

        Returns:
            Объект Wallet или None, если не найден
        """

        currency_code = currency_code.upper()
        return self._wallets.get(currency_code)

    def get_total_value(self, base_currency: str = "USD") -> float:
        """
        Возвращает общую стоимость всех валют в указанной базовой валюте

        Args:
            base_currency: код базовой валюты для конвертации

        Returns:
            Общая стоимость в базовой валюте

        Raises:
            ValueError: если базовая валюта не поддерживается
        """

        base_currency = base_currency.upper()

        # Проверяем, что базовая валюта поддерживается
        if base_currency not in self.EXCHANGE_RATES:
            raise ValueError(f"Базовая валюта {base_currency} не поддерживается")

        total_value = 0.0

        for currency_code, wallet in self._wallets.items():
            # Пропускаем валюты, которые не имеют курса конвертации
            if currency_code not in self.EXCHANGE_RATES:
                print(f"Предупреждение: курс для {currency_code} не найден, пропускаем")
                continue

            # Получаем курс конвертации
            rate = self.EXCHANGE_RATES[currency_code].get(base_currency)
            if rate is None:
                print(
                    f"Предупреждение: курс {currency_code} -> {base_currency} не найден, пропускаем"
                )
                continue

            # Конвертируем и суммируем
            total_value += wallet.balance * rate

        return total_value

    def buy_currency(
        self, target_currency: str, amount: float, price_per_unit: float
    ) -> bool:
        """
        Покупка валюты (списывается с USD кошелька)

        Args:
            target_currency: код покупаемой валюты
            amount: количество покупаемой валюты
            price_per_unit: цена за единицу в USD

        Returns:
            True если операция успешна

        Raises:
            ValueError: если недостаточно средств или валюта не найдена
        """

        target_currency = target_currency.upper()

        # Проверяем параметры
        if amount <= 0:
            raise ValueError("Количество должно быть положительным числом")
        if price_per_unit <= 0:
            raise ValueError("Цена должна быть положительным числом")

        # Проверяем наличие USD кошелька
        usd_wallet = self.get_wallet("USD")
        if not usd_wallet:
            raise ValueError("USD кошелек не найден")

        # Вычисляем общую стоимость в USD
        total_cost_usd = amount * price_per_unit

        # Проверяем достаточно ли средств в USD кошельке
        if usd_wallet.balance < total_cost_usd:
            raise ValueError(
                f"Недостаточно USD. Нужно: {total_cost_usd:.2f}, есть: {usd_wallet.balance:.2f}"
            )

        # Получаем или создаем кошелек для целевой валюты
        target_wallet = self.get_wallet(target_currency)
        if not target_wallet:
            target_wallet = self.add_currency(target_currency)

        # Снимаем средства с USD кошелька
        usd_wallet.withdraw(total_cost_usd)

        # Пополняем целевой кошелек
        target_wallet.deposit(amount)

        return True

    def sell_currency(
        self, source_currency: str, amount: float, price_per_unit: float
    ) -> bool:
        """
        Продажа валюты (начисляется на USD кошелёк)

        Args:
            source_currency: код продаваемой валюты
            amount: количество продаваемой валюты
            price_per_unit: цена за единицу в USD

        Returns:
            True если операция успешна

        Raises:
            ValueError: если недостаточно валюты для продажи
        """

        source_currency = source_currency.upper()

        # Проверяем параметры
        if amount <= 0:
            raise ValueError("Количество должно быть положительным числом")
        if price_per_unit <= 0:
            raise ValueError("Цена должна быть положительным числом")

        # Проверяем наличие кошелька с продаваемой валютой
        source_wallet = self.get_wallet(source_currency)
        if not source_wallet:
            raise ValueError(f"Кошелек {source_currency} не найден")

        # Проверяем достаточно ли валюты для продажи
        if source_wallet.balance < amount:
            raise ValueError(
                f"Недостаточно {source_currency}. Нужно: {amount:.6f}, есть: {source_wallet.balance:.6f}"
            )

        # Проверяем наличие USD кошелька
        usd_wallet = self.get_wallet("USD")
        if not usd_wallet:
            raise ValueError("USD кошелек не найден")

        # Вычисляем выручку в USD
        total_revenue_usd = amount * price_per_unit

        # Снимаем средства с кошелька продаваемой валюты
        source_wallet.withdraw(amount)

        # Начисляем средства на USD кошелек
        usd_wallet.deposit(total_revenue_usd)

        return True

    def get_portfolio_info(self, base_currency: str = "USD") -> dict:
        """
        Возвращает полную информацию о портфеле

        Args:
            base_currency: код валюты для расчета общей стоимости

        Returns:
            Словарь с информацией о портфеле
        """

        wallets_info = {}
        for code, wallet in self._wallets.items():
            wallets_info[code] = wallet.get_balance_info()

        return {
            "user_id": self._user_id,
            "total_value": self.get_total_value(base_currency),
            "total_value_formatted": f"{self.get_total_value(base_currency):.2f} {base_currency}",
            "wallets": wallets_info,
            "wallets_count": len(self._wallets),
        }

    def to_dict(self) -> dict:
        """Преобразует объект Portfolio в словарь для сохранения в JSON"""
        wallets_dict = {}
        for currency_code, wallet in self._wallets.items():
            wallets_dict[currency_code] = wallet.to_dict()

        return {"user_id": self._user_id, "wallets": wallets_dict}

    @classmethod
    def from_dict(cls, data: dict):
        """Создаёт объект Portfolio из словаря"""

        wallets = {}
        for currency_code, wallet_data in data["wallets"].items():
            wallets[currency_code] = Wallet.from_dict(wallet_data)

        return cls(user_id=data["user_id"], wallets=wallets)

    def __str__(self) -> str:
        """Строковое представление портфеля"""

        total_value = self.get_total_value("USD")
        return f"Portfolio(user_id={self._user_id}, wallets={len(self._wallets)}, total_value={total_value:.2f} USD)"

    def __repr__(self) -> str:
        """Представление объекта для отладки"""

        return f"Portfolio(user_id={self._user_id}, wallets={self._wallets})"
