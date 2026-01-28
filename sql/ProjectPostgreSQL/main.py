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
        self.current_room_position = -1
        self.current_room_obj = None
        return

    def initialize_database(self):
        """Инициализация базы данных при запуске"""
        print("Инициализация базы данных...")

        # Проверяем соединение
        if not self.connection.test():
            print("✗ Не удалось подключиться к базе данных")
            return False

        print("✓ Соединение с базой данных установлено")

        # Создаем таблицы если их нет
        rt = RoomsTable()
        rkt = RacksTable()

        rt.create()
        rkt.create()

        # Проверяем, есть ли данные
        rooms = rt.all()
        if not rooms:
            print("База данных пуста, вы можете добавить данные через меню")
        else:
            print(f"✓ В базе данных {len(rooms)} помещений")

        return True

    def show_main_menu(self):
        """Главное меню"""
        menu = """
===========================================
     СИСТЕМА УПРАВЛЕНИЯ СКЛАДОМ
===========================================
Основное меню:
    1 - Просмотр и управление помещениями
    2 - Сброс и инициализация базы данных
    9 - Выход
==========================================="""
        print(menu)
        return

    def read_next_step(self):
        return input("\nВыберите действие: ").strip()

    def after_main_menu(self, next_step):
        if next_step == "2":
            self.reset_database()
            return "0"
        elif next_step != "1" and next_step != "9":
            print("✗ Неверный выбор. Пожалуйста, введите 1, 2 или 9.")
            return "0"
        else:
            return next_step

    def show_rooms_menu(self):
        """Меню работы с помещениями"""
        print("\n" + "=" * 50)
        print("УПРАВЛЕНИЕ ПОМЕЩЕНИЯМИ")
        print("=" * 50)

        rt = RoomsTable()
        rooms = rt.all()

        if not rooms:
            print("\nПомещений пока нет.")
        else:
            print("\nСписок помещений:")
            print("№  Название                  Объем (м³)  Температура    Влажность")
            print("-" * 70)

            for i, room in enumerate(rooms, 1):
                temp_min = room[3] if room[3] is not None else "-"
                temp_max = room[4] if room[4] is not None else "-"
                humidity_min = room[5] if room[5] is not None else "-"
                humidity_max = room[6] if room[6] is not None else "-"

                temp_range = f"{temp_min}-{temp_max}°C"
                humidity_range = f"{humidity_min}-{humidity_max}%"
                print(
                    f"{i:<3} {room[1]:<25} {room[2]:<11.1f} {temp_range:<14} {humidity_range}"
                )

        menu = """
Действия:
    0 - Назад в главное меню
    1 - Добавить новое помещение
    2 - Удалить помещение
    3 - Редактировать помещение
    4 - Просмотреть стеллажи в помещении
    9 - Выход"""
        print(menu)

        return self.read_next_step()

    def after_rooms_menu(self, next_step):
        if next_step == "0":
            return "0"
        elif next_step == "1":
            self.add_room_manual()
            return "1"
        elif next_step == "2":
            self.delete_room()
            return "1"
        elif next_step == "3":
            self.edit_room()
            return "1"
        elif next_step == "4":
            self.select_room_for_racks()
            return "1"
        elif next_step == "9":
            return "9"
        else:
            print("✗ Неверный выбор.")
            return "1"

    def add_room_manual(self):
        """Ручное добавление помещения"""
        print("\n" + "=" * 50)
        print("ДОБАВЛЕНИЕ НОВОГО ПОМЕЩЕНИЯ")
        print("=" * 50)
        print("\nВведите данные нового помещения.")
        print("Для отмены введите '0' в любое поле.")

        # Название помещения
        while True:
            name = input("\nНазвание помещения: ").strip()
            if name == "0":
                print("✗ Добавление отменено.")
                return

            if not name:
                print("✗ Название не может быть пустым.")
                continue

            if len(name) > 100:
                print("✗ Название слишком длинное (максимум 100 символов).")
                continue

            # Проверка уникальности
            rt = RoomsTable()
            if rt.find_by_name(name):
                print(f"✗ Помещение с названием '{name}' уже существует.")
                continue

            break

        # Полезный объем
        while True:
            volume = input("Полезный объем (м³): ").strip()
            if volume == "0":
                print("✗ Добавление отменено.")
                return

            try:
                volume_val = float(volume)
                if volume_val <= 0:
                    print("✗ Объем должен быть положительным числом.")
                    continue
                break
            except ValueError:
                print("✗ Пожалуйста, введите число.")

        # Температура (опционально)
        print("\nДиапазон температур (можно не указывать):")
        temp_min = None
        temp_max = None

        temp_min_input = input(
            "  Минимальная температура (°C, Enter для пропуска): "
        ).strip()
        if temp_min_input == "0":
            print("✗ Добавление отменено.")
            return

        if temp_min_input:
            try:
                temp_min = float(temp_min_input)
            except ValueError:
                print("✗ Некорректное значение температуры.")
                return

        if temp_min is not None:
            temp_max_input = input(
                "  Максимальная температура (°C, Enter для пропуска): "
            ).strip()
            if temp_max_input == "0":
                print("✗ Добавление отменено.")
                return

            if temp_max_input:
                try:
                    temp_max = float(temp_max_input)
                    if temp_max <= temp_min:
                        print(
                            "✗ Максимальная температура должна быть больше минимальной."
                        )
                        return
                except ValueError:
                    print("✗ Некорректное значение температуры.")
                    return

        # Влажность (опционально)
        print("\nДиапазон влажности (можно не указывать):")
        humidity_min = None
        humidity_max = None

        humidity_min_input = input(
            "  Минимальная влажность (%, Enter для пропуска): "
        ).strip()
        if humidity_min_input == "0":
            print("✗ Добавление отменено.")
            return

        if humidity_min_input:
            try:
                humidity_min = float(humidity_min_input)
                if humidity_min < 0 or humidity_min > 100:
                    print("✗ Влажность должна быть в диапазоне 0-100%.")
                    return
            except ValueError:
                print("✗ Некорректное значение влажности.")
                return

        if humidity_min is not None:
            humidity_max_input = input(
                "  Максимальная влажность (%, Enter для пропуска): "
            ).strip()
            if humidity_max_input == "0":
                print("✗ Добавление отменено.")
                return

            if humidity_max_input:
                try:
                    humidity_max = float(humidity_max_input)
                    if humidity_max <= humidity_min:
                        print(
                            "✗ Максимальная влажность должна быть больше минимальной."
                        )
                        return
                    if humidity_max > 100:
                        print("✗ Влажность не может превышать 100%.")
                        return
                except ValueError:
                    print("✗ Некорректное значение влажности.")
                    return

        # Подготавливаем данные для вставки
        data = [name, volume_val, temp_min, temp_max, humidity_min, humidity_max]

        # Вставляем в базу данных
        rt = RoomsTable()
        if rt.insert_one(data):
            print(f"\n✓ Помещение '{name}' успешно добавлено!")
        else:
            print("\n✗ Ошибка при добавлении помещения.")

    def delete_room(self):
        """Удаление помещения"""
        rt = RoomsTable()
        rooms = rt.all()

        if not rooms:
            print("\n✗ Нет помещений для удаления.")
            return

        print("\n" + "=" * 50)
        print("УДАЛЕНИЕ ПОМЕЩЕНИЯ")
        print("=" * 50)
        print("\nВыберите помещение для удаления:")

        for i, room in enumerate(rooms, 1):
            print(f"{i}. {room[1]}")

        print("0. Отмена")

        while True:
            try:
                choice = input("\nНомер помещения: ").strip()
                if choice == "0":
                    print("✗ Удаление отменено.")
                    return

                num = int(choice)
                if num < 1 or num > len(rooms):
                    print(f"✗ Пожалуйста, введите число от 1 до {len(rooms)}.")
                    continue

                room = rooms[num - 1]
                print(f"\nВы выбрали: {room[1]}")
                print(f"Объем: {room[2]} м³")

                confirm = (
                    input("Вы уверены, что хотите удалить это помещение? (да/нет): ")
                    .strip()
                    .lower()
                )
                if confirm != "да":
                    print("✗ Удаление отменено.")
                    return

                success, message = rt.delete_by_position(num)
                print(f"\n{message}")
                break

            except ValueError:
                print("✗ Пожалуйста, введите число.")

    def edit_room(self):
        """Редактирование помещения"""
        rt = RoomsTable()
        rooms = rt.all()

        if not rooms:
            print("\n✗ Нет помещений для редактирования.")
            return

        print("\n" + "=" * 50)
        print("РЕДАКТИРОВАНИЕ ПОМЕЩЕНИЯ")
        print("=" * 50)
        print("\nВыберите помещение для редактирования:")

        for i, room in enumerate(rooms, 1):
            print(f"{i}. {room[1]}")

        print("0. Отмена")

        while True:
            try:
                choice = input("\nНомер помещения: ").strip()
                if choice == "0":
                    print("✗ Редактирование отменено.")
                    return

                num = int(choice)
                if num < 1 or num > len(rooms):
                    print(f"✗ Пожалуйста, введите число от 1 до {len(rooms)}.")
                    continue

                room = rooms[num - 1]
                self.edit_room_details(num, room)
                break

            except ValueError:
                print("✗ Пожалуйста, введите число.")

    def edit_room_details(self, position, room):
        """Редактирование деталей помещения"""
        print(f"\nРедактирование помещения: {room[1]}")
        print("(оставьте поле пустым, чтобы сохранить текущее значение)")
        print("(введите '0' для отмены)")

        data = {}

        # Название
        current_name = room[1]
        new_name = input(f"\nНазвание [{current_name}]: ").strip()
        if new_name == "0":
            print("✗ Редактирование отменено.")
            return

        if new_name:
            if len(new_name) > 100:
                print("✗ Название слишком длинное!")
                return

            # Проверка уникальности
            rt = RoomsTable()
            existing = rt.find_by_name(new_name)
            if existing and existing[0] != room[0]:
                print(f"✗ Помещение с названием '{new_name}' уже существует!")
                return

            data["room_name"] = new_name

        # Объем
        current_volume = room[2]
        new_volume = input(f"Объем (м³) [{current_volume}]: ").strip()
        if new_volume == "0":
            print("✗ Редактирование отменено.")
            return

        if new_volume:
            try:
                volume_val = float(new_volume)
                if volume_val <= 0:
                    print("✗ Объем должен быть положительным числом!")
                    return
                data["useful_volume"] = volume_val
            except ValueError:
                print("✗ Пожалуйста, введите число.")
                return

        # Температура
        current_min_temp = room[3]
        current_max_temp = room[4]
        print(
            f"\nТекущий диапазон температур: {current_min_temp or 'не задано'}-{current_max_temp or 'не задано'}°C"
        )
        print("(оставьте поля пустыми, чтобы удалить диапазон)")

        new_min_temp = input("Минимальная температура (°C): ").strip()
        if new_min_temp == "0":
            print("✗ Редактирование отменено.")
            return

        if new_min_temp:
            try:
                data["min_temperature"] = float(new_min_temp)

                new_max_temp = input("Максимальная температура (°C): ").strip()
                if new_max_temp == "0":
                    print("✗ Редактирование отменено.")
                    return

                if new_max_temp:
                    max_temp = float(new_max_temp)
                    if max_temp <= data["min_temperature"]:
                        print(
                            "✗ Максимальная температура должна быть больше минимальной!"
                        )
                        return
                    data["max_temperature"] = max_temp
                else:
                    data["max_temperature"] = None
            except ValueError:
                print("✗ Пожалуйста, введите число.")
                return
        else:
            # Если минимальная не указана, проверяем максимальную
            new_max_temp = input("Максимальная температура (°C): ").strip()
            if new_max_temp == "0":
                print("✗ Редактирование отменено.")
                return

            if new_max_temp:
                print(
                    "✗ Если задана максимальная температура, должна быть задана и минимальная!"
                )
                return
            else:
                data["min_temperature"] = None
                data["max_temperature"] = None

        # Влажность
        current_min_hum = room[5]
        current_max_hum = room[6]
        print(
            f"\nТекущий диапазон влажности: {current_min_hum or 'не задано'}-{current_max_hum or 'не задано'}%"
        )
        print("(оставьте поля пустыми, чтобы удалить диапазон)")

        new_min_hum = input("Минимальная влажность (%): ").strip()
        if new_min_hum == "0":
            print("✗ Редактирование отменено.")
            return

        if new_min_hum:
            try:
                min_hum = float(new_min_hum)
                if min_hum < 0 or min_hum > 100:
                    print("✗ Влажность должна быть от 0 до 100%!")
                    return
                data["min_humidity"] = min_hum

                new_max_hum = input("Максимальная влажность (%): ").strip()
                if new_max_hum == "0":
                    print("✗ Редактирование отменено.")
                    return

                if new_max_hum:
                    max_hum = float(new_max_hum)
                    if max_hum <= data["min_humidity"]:
                        print(
                            "✗ Максимальная влажность должна быть больше минимальной!"
                        )
                        return
                    if max_hum > 100:
                        print("✗ Влажность не может превышать 100%!")
                        return
                    data["max_humidity"] = max_hum
                else:
                    data["max_humidity"] = None
            except ValueError:
                print("✗ Пожалуйста, введите число.")
                return
        else:
            new_max_hum = input("Максимальная влажность (%): ").strip()
            if new_max_hum == "0":
                print("✗ Редактирование отменено.")
                return

            if new_max_hum:
                print(
                    "✗ Если задана максимальная влажность, должна быть задана и минимальная!"
                )
                return
            else:
                data["min_humidity"] = None
                data["max_humidity"] = None

        # Если нет изменений
        if not data:
            print("\nℹ Нет изменений для сохранения.")
            return

        # Сохраняем изменения
        rt = RoomsTable()
        success, message = rt.update_by_position(position, data)
        print(f"\n{message}")

    def select_room_for_racks(self):
        """Выбор помещения для работы со стеллажами"""
        rt = RoomsTable()
        rooms = rt.all()

        if not rooms:
            print("\n✗ Нет помещений. Сначала добавьте помещение.")
            return

        print("\n" + "=" * 50)
        print("ВЫБОР ПОМЕЩЕНИЯ ДЛЯ РАБОТЫ СО СТЕЛЛАЖАМИ")
        print("=" * 50)
        print("\nВыберите помещение:")

        for i, room in enumerate(rooms, 1):
            print(f"{i}. {room[1]}")

        print("0. Назад")

        while True:
            try:
                choice = input("\nНомер помещения: ").strip()
                if choice == "0":
                    return

                num = int(choice)
                if num < 1 or num > len(rooms):
                    print(f"✗ Пожалуйста, введите число от 1 до {len(rooms)}.")
                    continue

                room = rooms[num - 1]
                self.current_room_position = num
                self.current_room_obj = room
                self.show_racks_menu()
                break

            except ValueError:
                print("✗ Пожалуйста, введите число.")

    def show_racks_menu(self):
        """Меню работы со стеллажами"""
        if not self.current_room_obj:
            return

        room_name = self.current_room_obj[1]
        room_id = self.current_room_obj[0]

        print(f"\n" + "=" * 50)
        print(f"СТЕЛЛАЖИ В ПОМЕЩЕНИИ: {room_name}")
        print("=" * 50)

        rkt = RacksTable()
        racks = rkt.all_by_room_id(room_id)

        if not racks:
            print("\nСтеллажей в этом помещении пока нет.")
        else:
            print("\nСписок стеллажей:")
            print("№  Номер стеллажа  Ячеек  Размеры (В×Ш×Г, м)  Макс. нагрузка (кг)")
            print("-" * 70)

            for i, rack in enumerate(racks, 1):
                dimensions = f"{rack[4]:.1f}×{rack[5]:.1f}×{rack[6]:.1f}"
                print(
                    f"{i:<3} {rack[2]:<15} {rack[3]:<6} {dimensions:<19} {rack[7]:.1f}"
                )

        menu = """
Действия:
    0 - Назад к выбору помещения
    1 - Добавить стеллаж
    2 - Удалить стеллаж
    9 - Выход в главное меню"""
        print(menu)

        choice = self.read_next_step()
        self.after_racks_menu(choice)

    def after_racks_menu(self, choice):
        if choice == "0":
            self.current_room_obj = None
            self.current_room_position = -1
            return
        elif choice == "1":
            self.add_rack_manual()
            self.show_racks_menu()
        elif choice == "2":
            self.delete_rack()
            self.show_racks_menu()
        elif choice == "9":
            self.current_room_obj = None
            self.current_room_position = -1
            return "0"
        else:
            print("✗ Неверный выбор.")
            self.show_racks_menu()

    def add_rack_manual(self):
        """Ручное добавление стеллажа"""
        if not self.current_room_obj:
            print("✗ Сначала выберите помещение.")
            return

        room_name = self.current_room_obj[1]
        room_id = self.current_room_obj[0]

        print(f"\n" + "=" * 50)
        print(f"ДОБАВЛЕНИЕ СТЕЛЛАЖА В ПОМЕЩЕНИЕ: {room_name}")
        print("=" * 50)
        print("\nВведите данные нового стеллажа.")
        print("Для отмены введите '0' в любое поле.")

        # Номер стеллажа
        rkt = RacksTable()
        while True:
            rack_number = input("\nНомер стеллажа: ").strip()
            if rack_number == "0":
                print("✗ Добавление отменено.")
                return

            if not rack_number:
                print("✗ Номер стеллажа не может быть пустым.")
                continue

            if len(rack_number) > 20:
                print("✗ Номер слишком длинный (максимум 20 символов).")
                continue

            # Проверка уникальности в помещении
            if not rkt.check_unique_rack_number(room_id, rack_number):
                print(
                    f"✗ Стеллаж с номером '{rack_number}' уже существует в этом помещении."
                )
                continue

            break

        # Количество ячеек
        while True:
            count = input("Количество ячеек: ").strip()
            if count == "0":
                print("✗ Добавление отменено.")
                return

            try:
                count_val = int(count)
                if count_val <= 0:
                    print("✗ Количество ячеек должно быть положительным числом.")
                    continue
                if count_val > 1000:
                    print("✗ Слишком большое количество ячеек.")
                    continue
                break
            except ValueError:
                print("✗ Пожалуйста, введите целое число.")

        # Размеры ячейки
        print("\nРазмеры ячейки (в метрах):")

        dimensions = ["высоту", "ширину", "длину"]
        dim_values = []

        for dim in dimensions:
            while True:
                value = input(f"  {dim.capitalize()}: ").strip()
                if value == "0":
                    print("✗ Добавление отменено.")
                    return

                try:
                    value_val = float(value)
                    if value_val <= 0:
                        print(f"✗ {dim.capitalize()} должна быть положительной.")
                        continue
                    if value_val > 100:
                        print("✗ Слишком большое значение.")
                        continue
                    dim_values.append(value_val)
                    break
                except ValueError:
                    print("✗ Пожалуйста, введите число.")

        # Максимальная нагрузка
        while True:
            load = input("Максимальная нагрузка (кг): ").strip()
            if load == "0":
                print("✗ Добавление отменено.")
                return

            try:
                load_val = float(load)
                if load_val < 0:
                    print("✗ Нагрузка не может быть отрицательной.")
                    continue
                if load_val > 1000000:
                    print("✗ Слишком большая нагрузка.")
                    continue
                break
            except ValueError:
                print("✗ Пожалуйста, введите число.")

        # Подготавливаем данные
        data = [
            room_id,
            rack_number,
            count_val,
            dim_values[0],
            dim_values[1],
            dim_values[2],
            load_val,
        ]

        # Вставляем в базу
        if rkt.insert_one(data):
            print(
                f"\n✓ Стеллаж '{rack_number}' успешно добавлен в помещение '{room_name}'!"
            )
        else:
            print("\n✗ Ошибка при добавлении стеллажа.")

    def delete_rack(self):
        """Удаление стеллажа"""
        if not self.current_room_obj:
            print("✗ Сначала выберите помещение.")
            return

        room_id = self.current_room_obj[0]
        room_name = self.current_room_obj[1]

        rkt = RacksTable()
        racks = rkt.all_by_room_id(room_id)

        if not racks:
            print(f"\n✗ В помещении '{room_name}' нет стеллажей.")
            return

        print(f"\nУдаление стеллажа из помещения: {room_name}")
        print("\nВыберите стеллаж для удаления:")

        for i, rack in enumerate(racks, 1):
            print(f"{i}. Стеллаж {rack[2]} - {rack[3]} ячеек, нагрузка: {rack[7]} кг")

        print("0. Отмена")

        while True:
            try:
                choice = input("\nНомер стеллажа: ").strip()
                if choice == "0":
                    print("✗ Удаление отменено.")
                    return

                num = int(choice)
                if num < 1 or num > len(racks):
                    print(f"✗ Пожалуйста, введите число от 1 до {len(racks)}.")
                    continue

                rack = racks[num - 1]
                print(f"\nВы выбрали: Стеллаж {rack[2]}")
                print(f"Количество ячеек: {rack[3]}")
                print(f"Размеры: {rack[4]}×{rack[5]}×{rack[6]} м")
                print(f"Максимальная нагрузка: {rack[7]} кг")

                confirm = input("Вы уверены? (да/нет): ").strip().lower()
                if confirm != "да":
                    print("✗ Удаление отменено.")
                    return

                success, message = rkt.delete_by_position(room_id, num)
                print(f"\n{message}")
                break

            except ValueError:
                print("✗ Пожалуйста, введите число.")

    def reset_database(self):
        """Полный сброс базы данных"""
        print("\n" + "=" * 50)
        print("ПОЛНЫЙ СБРОС БАЗЫ ДАННЫХ")
        print("=" * 50)
        print("\nВНИМАНИЕ: Это действие удалит ВСЕ данные!")
        print("Все помещения и стеллажи будут безвозвратно удалены.")

        confirm = input("\nВы уверены? (да/нет): ").strip().lower()
        if confirm != "да":
            print("✗ Сброс отменен.")
            return

        print("\nВыполняется сброс базы данных...")

        # Удаляем таблицы
        rkt = RacksTable()
        rt = RoomsTable()

        rkt.drop()
        rt.drop()

        # Создаем таблицы заново
        rt.create()
        rkt.create()

        print("\n" + "=" * 50)
        print("✓ База данных сброшена и инициализирована!")
        print("Теперь вы можете добавить новые данные.")
        print("=" * 50)

    def main_cycle(self):
        """Основной цикл программы"""
        # Инициализация при запуске
        if not self.initialize_database():
            print("\nНе удалось инициализировать базу данных.")
            print("Проверьте настройки подключения в project_config.py")
            return

        current_menu = "0"

        while current_menu != "9":
            if current_menu == "0":
                self.show_main_menu()
                next_step = self.read_next_step()
                current_menu = self.after_main_menu(next_step)
            elif current_menu == "1":
                next_step = self.show_rooms_menu()
                current_menu = self.after_rooms_menu(next_step)

        print("\n" + "=" * 50)
        print("Спасибо за использование системы!")
        print("=" * 50)


if __name__ == "__main__":
    m = Main()
    m.main_cycle()
