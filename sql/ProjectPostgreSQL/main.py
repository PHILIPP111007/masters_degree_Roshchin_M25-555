"""
Рощин Филипп Андреевич, 4 вариант

Вариант 3-4
Таблицы помещения и стеллажи без связей с другими таблицами.

КОММЕНТАРИЙ:

Здравствуйте! У меня весь код работает, не знаю, почему у вас нет...(((

А вы можете добавить баллы за то, что у меня получилось создать язык программирования?
Спасибо!

https://github.com/PHILIPP111007/phils_language
"""

import sys

sys.path.append("tables")

from project_config import *
from dbconnection import *
from rooms_table import *
from racks_table import *


class Main:
    config = ProjectConfig()
    connection = DbConnection(config)

    def __init__(self):
        DbTable.dbconn = self.connection
        return

    def test_connection(self):
        """Тест соединения с БД"""
        print("Тестирование соединения с базой данных...")
        if self.connection.test():
            print("✓ Соединение установлено")
            return True
        else:
            print("✗ Не удалось подключиться к базе данных")
            return False

    def create_tables(self):
        """Создание таблиц"""
        print("\nСоздание таблиц...")

        # Создаем экземпляры таблиц
        rt = RoomsTable()
        rkt = RacksTable()

        # Создаем таблицы
        if rt.create():
            print("✓ Таблица 'rooms' создана")
        else:
            print("✗ Не удалось создать таблицу 'rooms'")
            return False

        if rkt.create():
            print("✓ Таблица 'racks' создана")
        else:
            print("✗ Не удалось создать таблицу 'racks'")
            return False

        return True

    def drop_tables(self):
        """Удаление таблиц"""
        print("\nУдаление таблиц...")

        # Создаем экземпляры таблиц
        rkt = RacksTable()
        rt = RoomsTable()

        # Удаляем в правильном порядке (сначала racks из-за внешних ключей)
        if rkt.drop():
            print("✓ Таблица 'racks' удалена")
        else:
            print("✗ Не удалось удалить таблицу 'racks'")

        if rt.drop():
            print("✓ Таблица 'rooms' удалена")
        else:
            print("✗ Не удалось удалить таблицу 'rooms'")

        return True

    def add_test_data(self):
        """Добавление тестовых данных"""
        print("\nДобавление тестовых данных...")

        rt = RoomsTable()
        rkt = RacksTable()

        # Тестовые помещения
        test_rooms = [
            ["Склад А", 150.5, 15.0, 25.0, 40.0, 60.0],
            ["Холодильная камера", 80.2, 2.0, 8.0, 30.0, 50.0],
            ["Оранжерея", 200.0, 18.0, 28.0, 50.0, 80.0],
        ]

        print(f"Порядок колонок для rooms: {rt.column_names_without_id()}")

        for i, room_data in enumerate(test_rooms, 1):
            print(f"Добавление помещения {i}: {room_data[0]}")
            if rt.insert_one(room_data):
                print(f"  ✓ Помещение '{room_data[0]}' добавлено")
            else:
                print(f"  ✗ Ошибка при добавлении помещения '{room_data[0]}'")
                return False

        # Тестовые стеллажи
        test_racks = [
            [1, "А-001", 5, 2.0, 1.0, 0.5, 500.0],
            [1, "А-002", 5, 2.0, 1.0, 0.5, 500.0],
            [2, "Х-001", 3, 1.8, 0.8, 0.4, 300.0],
            [3, "О-001", 6, 2.2, 1.2, 0.6, 400.0],
        ]

        print(f"\nПорядок колонок для racks: {rkt.column_names_without_id()}")

        for i, rack_data in enumerate(test_racks, 1):
            print(f"Добавление стеллажа {i}: {rack_data[1]}")
            if rkt.insert_one(rack_data):
                print(f"  ✓ Стеллаж '{rack_data[1]}' добавлен")
            else:
                print(f"  ✗ Ошибка при добавлении стеллажа '{rack_data[1]}'")
                return False

        print("\n✓ Все тестовые данные добавлены")
        return True

    def show_rooms(self):
        """Показать список помещений"""
        print("\n" + "=" * 50)
        print("СПИСОК ПОМЕЩЕНИЙ")
        print("=" * 50)

        rt = RoomsTable()
        rooms = rt.all()

        if not rooms:
            print("Помещений нет")
            return

        print(f"\nНайдено {len(rooms)} помещений:")

        for i, room in enumerate(rooms, 1):
            print(f"\nПомещение #{i}:")
            print(f"  ID: {room[0]}")
            print(f"  Название: {room[1]}")
            print(f"  Объем: {room[2]} м³")
            print(f"  Температура: {room[3]} - {room[4]} °C")
            print(f"  Влажность: {room[5]} - {room[6]} %")

    def main_menu(self):
        """Главное меню"""
        print("\n" + "=" * 50)
        print("СИСТЕМА УПРАВЛЕНИЯ СКЛАДОМ")
        print("=" * 50)
        print("\n1. Проверить соединение с БД")
        print("2. Создать таблицы")
        print("3. Удалить таблицы")
        print("4. Добавить тестовые данные")
        print("5. Показать список помещений")
        print("6. Полный сброс и инициализация")
        print("9. Выход")

        choice = input("\nВыберите действие: ").strip()
        return choice

    def full_reset(self):
        """Полный сброс и инициализация"""
        print("\n" + "=" * 50)
        print("ПОЛНЫЙ СБРОС И ИНИЦИАЛИЗАЦИЯ")
        print("=" * 50)
        print("\nЭто удалит все данные и создаст таблицы заново.")

        confirm = input("Вы уверены? (да/нет): ").strip().lower()
        if confirm != "да":
            print("Операция отменена.")
            return

        print("\nВыполняется сброс...")

        # Шаг 1: Удаляем таблицы
        self.drop_tables()

        # Шаг 2: Создаем таблицы заново
        if not self.create_tables():
            print("✗ Не удалось создать таблицы")
            return

        # Шаг 3: Добавляем тестовые данные
        if not self.add_test_data():
            print("✗ Не удалось добавить тестовые данные")
            return

        print("\n" + "=" * 50)
        print("✓ Сброс и инициализация завершены успешно!")
        print("=" * 50)

    def run(self):
        """Основной цикл программы"""
        print("Запуск системы управления складом...")

        while True:
            choice = self.main_menu()

            if choice == "1":
                self.test_connection()
            elif choice == "2":
                self.create_tables()
            elif choice == "3":
                self.drop_tables()
            elif choice == "4":
                self.add_test_data()
            elif choice == "5":
                self.show_rooms()
            elif choice == "6":
                self.full_reset()
            elif choice == "9":
                print("\nДо свидания!")
                break
            else:
                print("\n✗ Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    m = Main()
    m.run()
