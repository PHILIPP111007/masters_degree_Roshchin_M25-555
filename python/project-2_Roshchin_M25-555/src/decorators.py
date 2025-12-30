import time

from prettytable import PrettyTable

from src.primitive_db.constants import CONST


def handle_db_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print(
                "Ошибка: Файл данных не найден. Возможно, база данных не "
                "инициализирована."
            )
        except KeyError as e:
            print(f"Ошибка: Таблица или столбец {e} не найден.")
        except ValueError as e:
            print(f"Ошибка валидации: {e}")
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")

    return wrapper


def confirm_action(func):
    def wrapper(*args, **kwargs):
        answer = input("Выдействительно хотите это совершить? (y/n) ")
        if answer == "y":
            return func(*args, **kwargs)

    return wrapper


def log_time(func):
    def wrapper(*args, **kwargs):
        t_1 = time.monotonic()
        result = func(*args, **kwargs)
        t_2 = time.monotonic()
        result_time = t_2 - t_1
        print(f"Функция проработала {result_time:.3} секунд")
        return result

    return wrapper


def create_cacher(func):
    def wrapper(*args, **kwargs):
        cache_key = f"{func.__name__}_{args}_{sorted(kwargs.items())}"

        if cache_key in CONST.CACHE:
            print("Используется кешированный результат")
            cached_data = CONST.CACHE[cache_key]

            # Восстанавливаем и выводим таблицу
            table = PrettyTable()
            table.field_names = cached_data["field_names"]
            table.add_rows(cached_data["rows"])
            print(table)
            return None
        else:
            result = func(*args, **kwargs)
            CONST.CACHE[cache_key] = result
        return result

    return wrapper
