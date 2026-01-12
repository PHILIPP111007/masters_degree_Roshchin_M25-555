"""
Рощин Филипп Андреевич, 4 вариант

Вариант 3-4
Таблицы помещения и стеллажи без связей с другими таблицами.
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
        self.current_room_position = -1  # Храним порядковый номер помещения
        self.current_room_obj = None
        return

    def db_init(self):
        rt = RoomsTable()
        rkt = RacksTable()
        rt.create()
        rkt.create()
        return

    def db_insert_somethings(self):
        rt = RoomsTable()
        rkt = RacksTable()

        # Добавляем тестовые помещения
        rt.insert_one(["Склад А", 150.5, 15.0, 25.0, 40.0, 60.0])
        rt.insert_one(["Холодильная камера", 80.2, 2.0, 8.0, 30.0, 50.0])
        rt.insert_one(["Оранжерея", 200.0, 18.0, 28.0, 50.0, 80.0])

        # Добавляем тестовые стеллажи
        rkt.insert_one([1, "А-001", 5, 2.0, 1.0, 0.5, 500.0])
        rkt.insert_one([1, "А-002", 5, 2.0, 1.0, 0.5, 500.0])
        rkt.insert_one([2, "Х-001", 3, 1.8, 0.8, 0.4, 300.0])
        rkt.insert_one([3, "О-001", 6, 2.2, 1.2, 0.6, 400.0])

    def db_drop(self):
        rkt = RacksTable()
        rt = RoomsTable()
        rkt.drop()
        rt.drop()
        return

    def show_main_menu(self):
        menu = """\n=== Система управления складскими помещениями ===
Основное меню:
    1 - Просмотр помещений
    2 - Сброс и инициализация таблиц
    9 - Выход"""
        print(menu)
        return

    def read_next_step(self):
        return input("=> ").strip()

    def after_main_menu(self, next_step):
        if next_step == "2":
            print("\nВНИМАНИЕ: Это удалит все данные!")
            print("Вы уверены, что хотите удалить все данные? (да/нет)")
            confirm = input("=> ").strip().lower()
            if confirm == "да":
                self.db_drop()
                self.db_init()
                self.db_insert_somethings()
                print("✓ Таблицы созданы заново с тестовыми данными!")
            else:
                print("✗ Операция отменена.")
            return "0"
        elif next_step != "1" and next_step != "9":
            print("✗ Выбрано неверное число! Повторите ввод!")
            return "0"
        else:
            return next_step

    def show_rooms(self):
        self.current_room_position = -1
        self.current_room_obj = None

        print("\n=== Список помещений ===")

        rt = RoomsTable()
        lst = rt.all()

        if not lst:
            print("Помещений нет")
        else:
            print("№  Название                  Объем (м³)  Температура    Влажность")
            print("-" * 70)

            for i, room in enumerate(lst, 1):
                temp_range = f"{room[3] or ' -'}-{room[4] or '-'}°C"
                humidity_range = f"{room[5] or ' -'}-{room[6] or '-'}%"
                print(
                    f"{i:<3} {room[1]:<25} {room[2]:<11.1f} {temp_range:<14} {humidity_range}"
                )

        menu = """\nДействия с помещениями:
    0 - Возврат в главное меню
    3 - Добавление нового помещения
    4 - Удаление помещения
    5 - Редактирование помещения
    6 - Просмотр стеллажей в помещении
    9 - Выход"""
        print(menu)
        return

    def after_show_rooms(self, next_step):
        if next_step == "3":
            self.show_add_room()
            return "1"
        elif next_step == "4":
            self.show_delete_room()
            return "1"
        elif next_step == "5":
            self.show_edit_room()
            return "1"
        elif next_step == "6":
            next_step = self.show_racks_by_room()
        elif next_step != "0" and next_step != "9":
            print("✗ Выбрано неверное число! Повторите ввод!")
            return "1"
        return next_step

    def show_add_room(self):
        print("\n--- Добавление нового помещения ---")
        print("(введите '0' в любое поле для отмены)")

        data = {}

        # Название помещения
        while True:
            data["room_name"] = input("Название помещения: ").strip()
            if data["room_name"] == "0":
                print("✗ Операция отменена.")
                return

            if len(data["room_name"]) == 0:
                print("✗ Название не может быть пустым!")
                continue

            if len(data["room_name"]) > 100:
                print("✗ Название слишком длинное (макс. 100 символов)!")
                continue

            # Проверяем уникальность названия
            rt = RoomsTable()
            existing = rt.find_by_name(data["room_name"])
            if existing:
                print(f"✗ Помещение с названием '{data['room_name']}' уже существует!")
                continue

            break

        # Полезный объем
        while True:
            volume = input("Полезный объем (м³): ").strip()
            if volume == "0":
                print("✗ Операция отменена.")
                return

            try:
                volume_val = float(volume)
                if volume_val <= 0:
                    print("✗ Объем должен быть положительным числом!")
                    continue
                data["useful_volume"] = volume_val
                break
            except ValueError:
                print("✗ Введите число!")

        # Температура (опционально)
        print("\nДиапазон температур (можно не указывать):")
        temp_min = input("  Минимальная температура (°C): ").strip()
        if temp_min == "0":
            print("✗ Операция отменена.")
            return

        if temp_min:
            try:
                data["min_temperature"] = float(temp_min)
            except ValueError:
                print("✗ Введите число или оставьте пустым!")
                return
        else:
            data["min_temperature"] = None

        if data["min_temperature"] is not None:
            temp_max = input("  Максимальная температура (°C): ").strip()
            if temp_max == "0":
                print("✗ Операция отменена.")
                return

            if temp_max:
                try:
                    max_temp = float(temp_max)
                    if max_temp <= data["min_temperature"]:
                        print(
                            "✗ Максимальная температура должна быть больше минимальной!"
                        )
                        return
                    data["max_temperature"] = max_temp
                except ValueError:
                    print("✗ Введите число или оставьте пустым!")
                    return
            else:
                data["max_temperature"] = None
        else:
            data["max_temperature"] = None

        # Влажность (опционально)
        print("\nДиапазон влажности (можно не указывать):")
        humidity_min = input("  Минимальная влажность (%): ").strip()
        if humidity_min == "0":
            print("✗ Операция отменена.")
            return

        if humidity_min:
            try:
                min_h = float(humidity_min)
                if min_h < 0 or min_h > 100:
                    print("✗ Влажность должна быть от 0 до 100%!")
                    return
                data["min_humidity"] = min_h
            except ValueError:
                print("✗ Введите число или оставьте пустым!")
                return
        else:
            data["min_humidity"] = None

        if data["min_humidity"] is not None:
            humidity_max = input("  Максимальная влажность (%): ").strip()
            if humidity_max == "0":
                print("✗ Операция отменена.")
                return

            if humidity_max:
                try:
                    max_h = float(humidity_max)
                    if max_h <= data["min_humidity"]:
                        print(
                            "✗ Максимальная влажность должна быть больше минимальной!"
                        )
                        return
                    if max_h > 100:
                        print("✗ Влажность не может превышать 100%!")
                        return
                    data["max_humidity"] = max_h
                except ValueError:
                    print("✗ Введите число или оставьте пустым!")
                    return
            else:
                data["max_humidity"] = None
        else:
            data["max_humidity"] = None

        try:
            rt = RoomsTable()
            rt.insert_one(
                [
                    data["room_name"],
                    data["useful_volume"],
                    data["min_temperature"],
                    data["max_temperature"],
                    data["min_humidity"],
                    data["max_humidity"],
                ]
            )
            print("\n✓ Помещение успешно добавлено!")
        except Exception as e:
            print(f"\n✗ Ошибка при добавлении: {e}")

    def show_delete_room(self):
        print("\n--- Удаление помещения ---")
        print("(введите '0' для отмены)")

        rt = RoomsTable()
        lst = rt.all()

        if not lst:
            print("Помещений нет")
            return

        print("\nСписок помещений:")
        for i, room in enumerate(lst, 1):
            print(f"{i}. {room[1]}")

        while True:
            try:
                num_str = input("\nВведите номер помещения для удаления: ").strip()
                if num_str == "0":
                    print("✗ Операция отменена.")
                    return

                num = int(num_str)
                if num < 1 or num > len(lst):
                    print(f"✗ Неверный номер! Введите число от 1 до {len(lst)}")
                    continue

                room = rt.find_by_position(num)
                if not room:
                    print("✗ Помещение не найдено!")
                    continue

                print(f"\nВы выбрали: {room[1]}")
                print(f"Объем: {room[2]} м³")

                confirm = (
                    input("Вы уверены, что хотите удалить это помещение? (да/нет): ")
                    .strip()
                    .lower()
                )
                if confirm != "да":
                    print("✗ Операция отменена.")
                    return

                success, message = rt.delete_by_position(num)
                print(f"\n{message}")
                break

            except ValueError:
                print("✗ Введите число!")
            except Exception as e:
                print(f"✗ Ошибка: {e}")

    def show_edit_room(self):
        print("\n--- Редактирование помещения ---")
        print("(введите '0' для отмены)")

        rt = RoomsTable()
        lst = rt.all()

        if not lst:
            print("Помещений нет")
            return

        print("\nСписок помещений:")
        for i, room in enumerate(lst, 1):
            print(f"{i}. {room[1]}")

        while True:
            try:
                num_str = input(
                    "\nВведите номер помещения для редактирования: "
                ).strip()
                if num_str == "0":
                    print("✗ Операция отменена.")
                    return

                num = int(num_str)
                if num < 1 or num > len(lst):
                    print(f"✗ Неверный номер! Введите число от 1 до {len(lst)}")
                    continue

                room = rt.find_by_position(num)
                if not room:
                    print("✗ Помещение не найдено!")
                    continue

                self.edit_room_details(num, room)
                break

            except ValueError:
                print("✗ Введите число!")

    def edit_room_details(self, position, room):
        print(f"\n--- Редактирование помещения: {room[1]} ---")
        print("(оставьте поле пустым, чтобы сохранить текущее значение)")
        print("(введите '0' для отмены)")

        data = {}

        # Название
        current_name = room[1]
        new_name = input(f"\nНазвание [{current_name}]: ").strip()
        if new_name == "0":
            print("✗ Операция отменена.")
            return

        if new_name:
            if len(new_name) > 100:
                print("✗ Название слишком длинное!")
                return

            # Проверяем уникальность названия
            rt = RoomsTable()
            existing = rt.find_by_name(new_name)
            if existing and existing[0] != room[0]:
                print(f"✗ Помещение с названием '{new_name}' уже существует!")
                return

            data["room_name"] = new_name
        else:
            data["room_name"] = current_name

        # Объем
        current_volume = room[2]
        new_volume = input(f"Полезный объем (м³) [{current_volume}]: ").strip()
        if new_volume == "0":
            print("✗ Операция отменена.")
            return

        if new_volume:
            try:
                volume_val = float(new_volume)
                if volume_val <= 0:
                    print("✗ Объем должен быть положительным числом!")
                    return
                data["useful_volume"] = volume_val
            except ValueError:
                print("✗ Введите число!")
                return
        else:
            data["useful_volume"] = current_volume

        # Температура
        current_min_temp = room[3]
        current_max_temp = room[4]
        print(
            f"\nТекущий диапазон температур: {current_min_temp or 'не задано'}-{current_max_temp or 'не задано'}°C"
        )
        print("(оставьте оба поля пустыми, чтобы удалить диапазон)")

        new_min_temp = input("Минимальная температура (°C): ").strip()
        if new_min_temp == "0":
            print("✗ Операция отменена.")
            return

        if new_min_temp:
            try:
                data["min_temperature"] = float(new_min_temp)

                new_max_temp = input("Максимальная температура (°C): ").strip()
                if new_max_temp == "0":
                    print("✗ Операция отменена.")
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
                print("✗ Введите число!")
                return
        else:
            # Если минимальная не указана, проверяем максимальную
            new_max_temp = input("Максимальная температура (°C): ").strip()
            if new_max_temp == "0":
                print("✗ Операция отменена.")
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
        print("(оставьте оба поля пустыми, чтобы удалить диапазон)")

        new_min_hum = input("Минимальная влажность (%): ").strip()
        if new_min_hum == "0":
            print("✗ Операция отменена.")
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
                    print("✗ Операция отменена.")
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
                print("✗ Введите число!")
                return
        else:
            new_max_hum = input("Максимальная влажность (%): ").strip()
            if new_max_hum == "0":
                print("✗ Операция отменена.")
                return

            if new_max_hum:
                print(
                    "✗ Если задана максимальная влажность, должна быть задана и минимальная!"
                )
                return
            else:
                data["min_humidity"] = None
                data["max_humidity"] = None

        try:
            rt = RoomsTable()
            success, message = rt.update_by_position(position, data)
            print(f"\n{message}")
        except Exception as e:
            print(f"\n✗ Ошибка при обновлении: {e}")

    def select_room_for_racks(self):
        """Выбор помещения для работы со стеллажами"""
        print("\n--- Выбор помещения ---")

        rt = RoomsTable()
        lst = rt.all()

        if not lst:
            print("Помещений нет")
            return -1, None

        print("\nСписок помещений:")
        for i, room in enumerate(lst, 1):
            print(f"{i}. {room[1]}")

        while True:
            try:
                num_str = input("\nВведите номер помещения: ").strip()
                if num_str == "0":
                    return -1, None

                num = int(num_str)
                if num < 1 or num > len(lst):
                    print(f"✗ Неверный номер! Введите число от 1 до {len(lst)}")
                    continue

                room = rt.find_by_position(num)
                if not room:
                    print("✗ Помещение не найдено!")
                    continue

                return num, room

            except ValueError:
                print("✗ Введите число!")

    def show_racks_by_room(self):
        if self.current_room_position == -1:
            position, room = self.select_room_for_racks()
            if position == -1:
                return "1"
            self.current_room_position = position
            self.current_room_obj = room

        print(f"\n=== Помещение: {self.current_room_obj[1]} ===")
        print("Список стеллажей:")

        rkt = RacksTable()
        lst = rkt.all_by_room_id(self.current_room_obj[0])

        if not lst:
            print("Стеллажей нет")
        else:
            print("№  Номер стеллажа  Ячеек  Размеры (В×Ш×Г, м)  Макс. нагрузка (кг)")
            print("-" * 70)

            for i, rack in enumerate(lst, 1):
                dimensions = f"{rack[4]:.1f}×{rack[5]:.1f}×{rack[6]:.1f}"
                print(
                    f"{i:<3} {rack[2]:<15} {rack[3]:<6} {dimensions:<19} {rack[7]:.1f}"
                )

        menu = """\nДействия со стеллажами:
    0 - Возврат в главное меню
    1 - Возврат к просмотру помещений
    2 - Добавление стеллажа
    3 - Удаление стеллажа
    4 - Выбрать другое помещение
    9 - Выход"""
        print(menu)

        next_step = self.read_next_step()
        return self.after_show_racks(next_step)

    def after_show_racks(self, next_step):
        if next_step == "2":
            self.show_add_rack()
            return "6"
        elif next_step == "3":
            self.show_delete_rack()
            return "6"
        elif next_step == "4":
            self.current_room_position = -1
            self.current_room_obj = None
            return "6"
        elif next_step == "0":
            return "0"
        elif next_step == "1":
            return "1"
        elif next_step == "9":
            return "9"
        else:
            print("✗ Выбрано неверное число!")
            return "6"

    def show_add_rack(self):
        print(f"\n--- Добавление стеллажа в помещение: {self.current_room_obj[1]} ---")
        print("(введите '0' в любое поле для отмены)")

        rkt = RacksTable()

        # Номер стеллажа
        while True:
            rack_number = input("Номер стеллажа: ").strip()
            if rack_number == "0":
                print("✗ Операция отменена.")
                return

            if len(rack_number) == 0:
                print("✗ Номер не может быть пустым!")
                continue

            if len(rack_number) > 20:
                print("✗ Номер слишком длинный (макс. 20 символов)!")
                continue

            # Проверка уникальности номера в помещении
            if not rkt.check_unique_rack_number(self.current_room_obj[0], rack_number):
                print("✗ Стеллаж с таким номером уже существует в этом помещении!")
                continue

            break

        # Количество ячеек
        while True:
            count_str = input("Количество ячеек: ").strip()
            if count_str == "0":
                print("✗ Операция отменена.")
                return

            try:
                count = int(count_str)
                if count <= 0:
                    print("✗ Количество должно быть положительным числом!")
                    continue
                if count > 1000:
                    print("✗ Слишком большое количество ячеек!")
                    continue
                break
            except ValueError:
                print("✗ Введите целое число!")

        # Размеры ячейки
        dimensions = [("высоту", "height"), ("ширину", "width"), ("длину", "length")]

        dim_values = {}
        for dim_name, _ in dimensions:
            while True:
                value_str = input(f"{dim_name.capitalize()} ячейки (м): ").strip()
                if value_str == "0":
                    print("✗ Операция отменена.")
                    return

                try:
                    value = float(value_str)
                    if value <= 0:
                        print(f"✗ {dim_name.capitalize()} должна быть положительной!")
                        continue
                    if value > 100:
                        print("✗ Слишком большое значение!")
                        continue
                    dim_values[dim_name] = value
                    break
                except ValueError:
                    print("✗ Введите число!")

        # Максимальная нагрузка
        while True:
            load_str = input("Максимальная нагрузка (кг): ").strip()
            if load_str == "0":
                print("✗ Операция отменена.")
                return

            try:
                load = float(load_str)
                if load < 0:
                    print("✗ Нагрузка не может быть отрицательной!")
                    continue
                if load > 1000000:
                    print("✗ Слишком большая нагрузка!")
                    continue
                break
            except ValueError:
                print("✗ Введите число!")

        try:
            rkt.insert_one(
                [
                    self.current_room_obj[0],
                    rack_number,
                    count,
                    dim_values["высоту"],
                    dim_values["ширину"],
                    dim_values["длину"],
                    load,
                ]
            )
            print("\n✓ Стеллаж успешно добавлен!")
        except Exception as e:
            print(f"\n✗ Ошибка при добавлении: {e}")

    def show_delete_rack(self):
        print(f"\n--- Удаление стеллажа из помещения: {self.current_room_obj[1]} ---")
        print("(введите '0' для отмены)")

        rkt = RacksTable()
        lst = rkt.all_by_room_id(self.current_room_obj[0])

        if not lst:
            print("Стеллажей нет")
            return

        print("\nСписок стеллажей:")
        for i, rack in enumerate(lst, 1):
            print(f"{i}. Стеллаж {rack[2]} - {rack[3]} ячеек, нагрузка: {rack[7]} кг")

        while True:
            try:
                num_str = input("\nВведите номер стеллажа для удаления: ").strip()
                if num_str == "0":
                    print("✗ Операция отменена.")
                    return

                num = int(num_str)
                if num < 1 or num > len(lst):
                    print(f"✗ Неверный номер! Введите число от 1 до {len(lst)}")
                    continue

                rack = rkt.find_by_position(self.current_room_obj[0], num)
                if not rack:
                    print("✗ Стеллаж не найдено!")
                    continue

                print(f"\nВы выбрали: Стеллаж {rack[2]}")
                print(f"Ячеек: {rack[3]}, Нагрузка: {rack[7]} кг")

                confirm = input("Вы уверены? (да/нет): ").strip().lower()
                if confirm != "да":
                    print("✗ Операция отменена.")
                    return

                success, message = rkt.delete_by_position(self.current_room_obj[0], num)
                print(f"\n{message}")
                break

            except ValueError:
                print("✗ Введите число!")
            except Exception as e:
                print(f"✗ Ошибка: {e}")

    def main_cycle(self):
        current_menu = "0"
        next_step = None

        # Инициализация базы при первом запуске
        try:
            rt = RoomsTable()
            rkt = RacksTable()
            # Пробуем получить список помещений для проверки
            rt.all()
        except:
            print("\nИнициализация базы данных...")
            self.db_init()
            self.db_insert_somethings()
            print("✓ База данных инициализирована с тестовыми данными")

        print("\n" + "=" * 50)
        print("Добро пожаловать в систему управления складом!")
        print("=" * 50)

        while current_menu != "9":
            if current_menu == "0":
                self.show_main_menu()
                next_step = self.read_next_step()
                current_menu = self.after_main_menu(next_step)
            elif current_menu == "1":
                self.show_rooms()
                next_step = self.read_next_step()
                current_menu = self.after_show_rooms(next_step)
            elif current_menu == "6":
                current_menu = self.show_racks_by_room()

        print("\n" + "=" * 50)
        print("До свидания! Спасибо за использование системы.")
        print("=" * 50)
        return

    def test(self):
        DbTable.dbconn.test()


if __name__ == "__main__":
    m = Main()
    m.main_cycle()
