# ValutaTrade Hub

CLI приложение для управления крипто-портфелем с поддержкой фиатных и криптовалют.

## Возможности

- Регистрация и аутентификация пользователей
- Управление портфелем из нескольких валют
- Покупка и продажа валют
- Получение актуальных курсов валют
- Конвертация стоимости портфеля в базовую валюту
- Логирование всех операций
- Поддержка фиатных и криптовалют

## Установка

```bash
# Клонирование репозитория
git clone https://github.com/PHILIPP111007/masters_degree_Roshchin_M25-555.git
cd python/final_project_Roshchin_M55-255/

# Установка зависимостей
poetry install

# Активация виртуального окружения
poetry shell
```

## Примеры использования

Регистрация пользователя:

```bash
poetry run python main.py register --username alice --password 1234
```

Вход в систему:

```bash
poetry run python main.py login --username alice --password 1234
```

Просмотр портфеля:

```bash
poetry run python main.py show-portfolio
poetry run python main.py show-portfolio --base EUR
```

Покупка валюты:

```bash
poetry run python main.py buy --currency BTC --amount 0.000005
```

Продажа валюты:

```bash
poetry run python main.py sell --currency BTC --amount 0.01
```

Получение курса:

```bash
poetry run python main.py get-rate --from USD --to BTC
```

Список поддерживаемых валют:

```bash
poetry run python main.py list-currencies
```

Выход из системы:

```bash
poetry run python main.py logout
```

Справка:

```bash
poetry run python main.py help
```