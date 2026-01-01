# Примеры использования

Регистрация пользователя:

```bash
python main.py register --username alice --password 1234
```

Вход в систему:

```bash
python main.py login --username alice --password 1234
```

Просмотр портфеля:

```bash
python main.py show-portfolio
python main.py show-portfolio --base EUR
```

Покупка валюты:

```bash
python main.py buy --currency BTC --amount 0.000005
```

Продажа валюты:

```bash
python main.py sell --currency BTC --amount 0.01
```

Получение курса:

```bash
python main.py get-rate --from USD --to BTC
```
