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
        self.room_id = -1
        self.room_obj = None
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
        menu = """\nСистема управления складскими помещениями
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
            print("\nВы уверены, что хотите удалить все данные? (да/нет)")
            confirm = input("=> ").strip().lower()
            if confirm == "да":
                self.db_drop()
                self.db_init()
                self.db_insert_somethings()
                print("Таблицы созданы заново!")
            else:
                print("Операция отменена.")
            return "0"
        elif next_step != "1" and next_step != "9":
            print("Выбрано неверное число! Повторите ввод!")
            return "0"
        else:
            return next_step

    def show_rooms(self):
        self.room_id = -1
        print("\nСписок помещений:")
        print("№  Название            Объем    Температура   Влажность")
        print("-" * 60)

        lst = RoomsTable().all()
        if not lst:
            print("Помещений нет")
        else:
            for i, room in enumerate(lst, 1):
                temp_range = (
                    f"{room[3]}-{room[4]}°C" if room[3] and room[4] else "не задано"
                )
                humidity_range = (
                    f"{room[5]}-{room[6]}%" if room[5] and room[6] else "не задано"
                )
                print(
                    f"{i:<3} {room[1]:<20} {room[2]:<8.1f} {temp_range:<14} {humidity_range}"
                )

        menu = """\nДальнейшие операции:
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
            print("Выбрано неверное число! Повторите ввод!")
            return "1"
        return next_step

    def show_add_room(self):
        print("\n--- Добавление нового помещения ---")
        data = {}

        # Название помещения
        while True:
            data["room_name"] = input(
                "Введите название помещения (0 - отмена): "
            ).strip()
            if data["room_name"] == "0":
                return
            if len(data["room_name"]) == 0:
                print("Название не может быть пустым!")
                continue
            if len(data["room_name"]) > 100:
                print("Название слишком длинное (макс. 100 символов)!")
                continue
            break

        # Полезный объем
        while True:
            try:
                volume = input("Введите полезный объем (м³): ").strip()
                if volume == "0":
                    return
                volume = float(volume)
                if volume <= 0:
                    print("Объем должен быть положительным числом!")
                    continue
                data["useful_volume"] = volume
                break
            except ValueError:
                print("Введите число!")

        # Температура
        print("\nДиапазон температур (оставьте пустым, если не требуется):")
        while True:
            try:
                temp_min = input("Минимальная температура (°C): ").strip()
                if temp_min == "":
                    data["min_temperature"] = None
                    break
                data["min_temperature"] = float(temp_min)
                break
            except ValueError:
                print("Введите число!")

        if data["min_temperature"] is not None:
            while True:
                try:
                    temp_max = input("Максимальная температура (°C): ").strip()
                    if temp_max == "":
                        data["max_temperature"] = None
                        break
                    data["max_temperature"] = float(temp_max)
                    if data["max_temperature"] <= data["min_temperature"]:
                        print(
                            "Максимальная температура должна быть больше минимальной!"
                        )
                        continue
                    break
                except ValueError:
                    print("Введите число!")
        else:
            data["max_temperature"] = None

        # Влажность
        print("\nДиапазон влажности (оставьте пустым, если не требуется):")
        while True:
            try:
                humidity_min = input("Минимальная влажность (%): ").strip()
                if humidity_min == "":
                    data["min_humidity"] = None
                    break
                humidity_min = float(humidity_min)
                if humidity_min < 0 or humidity_min > 100:
                    print("Влажность должна быть от 0 до 100%!")
                    continue
                data["min_humidity"] = humidity_min
                break
            except ValueError:
                print("Введите число!")

        if data["min_humidity"] is not None:
            while True:
                try:
                    humidity_max = input("Максимальная влажность (%): ").strip()
                    if humidity_max == "":
                        data["max_humidity"] = None
                        break
                    humidity_max = float(humidity_max)
                    if humidity_max <= data["min_humidity"]:
                        print("Максимальная влажность должна быть больше минимальной!")
                        continue
                    if humidity_max > 100:
                        print("Влажность не может превышать 100%!")
                        continue
                    data["max_humidity"] = humidity_max
                    break
                except ValueError:
                    print("Введите число!")
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
            print("\nПомещение успешно добавлено!")
        except Exception as e:
            print(f"\nОшибка при добавлении: {e}")

    def show_delete_room(self):
        print("\n--- Удаление помещения ---")

        # Показываем список помещений
        lst = RoomsTable().all()
        if not lst:
            print("Помещений нет")
            return

        for i, room in enumerate(lst, 1):
            print(f"{i}. {room[1]}")

        while True:
            try:
                num = input(
                    "\nВведите номер помещения для удаления (0 - отмена): "
                ).strip()
                if num == "0":
                    return

                num = int(num)
                if num < 1 or num > len(lst):
                    print("Неверный номер!")
                    continue

                room = lst[num - 1]
                print(f"\nВы выбрали: {room[1]}")
                confirm = input("Вы уверены? (да/нет): ").strip().lower()
                if confirm != "да":
                    print("Операция отменена.")
                    return

                rt = RoomsTable()
                success, message = rt.delete_by_id(room[0])
                print(message)
                break

            except ValueError:
                print("Введите число!")
            except Exception as e:
                print(f"Ошибка: {e}")

    def show_edit_room(self):
        print("\n--- Редактирование помещения ---")

        lst = RoomsTable().all()
        if not lst:
            print("Помещений нет")
            return

        for i, room in enumerate(lst, 1):
            print(f"{i}. {room[1]}")

        while True:
            try:
                num = input(
                    "\nВведите номер помещения для редактирования (0 - отмена): "
                ).strip()
                if num == "0":
                    return

                num = int(num)
                if num < 1 or num > len(lst):
                    print("Неверный номер!")
                    continue

                room = lst[num - 1]
                self.room_id = room[0]
                self.room_obj = room
                self.edit_room_details()
                break

            except ValueError:
                print("Введите число!")

    def edit_room_details(self):
        print(f"\nРедактирование помещения: {self.room_obj[1]}")
        print("(оставьте поле пустым, чтобы сохранить текущее значение)\n")

        data = {}

        # Название
        current = self.room_obj[1]
        new_name = input(f"Название [{current}]: ").strip()
        data["room_name"] = new_name if new_name else current

        # Объем
        current = self.room_obj[2]
        while True:
            try:
                new_volume = input(f"Полезный объем (м³) [{current}]: ").strip()
                if new_volume == "":
                    data["useful_volume"] = current
                    break
                volume = float(new_volume)
                if volume <= 0:
                    print("Объем должен быть положительным числом!")
                    continue
                data["useful_volume"] = volume
                break
            except ValueError:
                print("Введите число!")

        # Температура
        current_min = self.room_obj[3]
        current_max = self.room_obj[4]
        print(
            f"\nТекущий диапазон температур: {current_min or 'не задано'}-{current_max or 'не задано'}°C"
        )

        while True:
            try:
                new_min = input(
                    "Минимальная температура (°C) [оставьте пустым для удаления]: "
                ).strip()
                if new_min == "":
                    data["min_temperature"] = None
                    break
                data["min_temperature"] = float(new_min)
                break
            except ValueError:
                print("Введите число!")

        if data["min_temperature"] is not None:
            while True:
                try:
                    new_max = input(
                        "Максимальная температура (°C) [оставьте пустым для удаления]: "
                    ).strip()
                    if new_max == "":
                        data["max_temperature"] = None
                        break
                    max_temp = float(new_max)
                    if max_temp <= data["min_temperature"]:
                        print(
                            "Максимальная температура должна быть больше минимальной!"
                        )
                        continue
                    data["max_temperature"] = max_temp
                    break
                except ValueError:
                    print("Введите число!")
        else:
            data["max_temperature"] = None

        # Влажность
        current_min_h = self.room_obj[5]
        current_max_h = self.room_obj[6]
        print(
            f"\nТекущий диапазон влажности: {current_min_h or 'не задано'}-{current_max_h or 'не задано'}%"
        )

        if current_min_h is not None and current_max_h is not None:
            while True:
                try:
                    new_min_h = input(
                        "Минимальная влажность (%) [оставьте пустым для удаления]: "
                    ).strip()
                    if new_min_h == "":
                        data["min_humidity"] = None
                        break
                    min_h = float(new_min_h)
                    if min_h < 0 or min_h > 100:
                        print("Влажность должна быть от 0 до 100%!")
                        continue
                    data["min_humidity"] = min_h
                    break
                except ValueError:
                    print("Введите число!")

            if data["min_humidity"] is not None:
                while True:
                    try:
                        new_max_h = input(
                            "Максимальная влажность (%) [оставьте пустым для удаления]: "
                        ).strip()
                        if new_max_h == "":
                            data["max_humidity"] = None
                            break
                        max_h = float(new_max_h)
                        if max_h <= data["min_humidity"]:
                            print(
                                "Максимальная влажность должна быть больше минимальной!"
                            )
                            continue
                        if max_h > 100:
                            print("Влажность не может превышать 100%!")
                            continue
                        data["max_humidity"] = max_h
                        break
                    except ValueError:
                        print("Введите число!")
            else:
                data["max_humidity"] = None
        else:
            data["min_humidity"] = None
            data["max_humidity"] = None

        try:
            rt = RoomsTable()
            rt.update(self.room_id, data)
            print("\nПомещение успешно обновлено!")
        except Exception as e:
            print(f"\nОшибка при обновлении: {e}")

    def show_racks_by_room(self):
        if self.room_id == -1:
            self.select_room()
            if self.room_id == -1:
                return "1"

        print(f"\nПомещение: {self.room_obj[1]}")
        print("Стеллажи:")
        print("№  Номер    Ячеек  Размеры (В×Ш×Г)   Макс. нагрузка")
        print("-" * 60)

        lst = RacksTable().all_by_room_id(self.room_id)
        if not lst:
            print("Стеллажей нет")
        else:
            for i, rack in enumerate(lst, 1):
                dimensions = f"{rack[4]:.1f}×{rack[5]:.1f}×{rack[6]:.1f} м"
                print(
                    f"{i:<3} {rack[2]:<8} {rack[3]:<6} {dimensions:<17} {rack[7]:.1f} кг"
                )

        menu = """\nДальнейшие операции:
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
            self.room_id = -1
            self.room_obj = None
            return "6"
        elif next_step == "0":
            return "0"
        elif next_step == "1":
            return "1"
        elif next_step == "9":
            return "9"
        else:
            print("Выбрано неверное число!")
            return "6"

    def select_room(self):
        print("\n--- Выбор помещения ---")
        lst = RoomsTable().all()

        if not lst:
            print("Помещений нет")
            return

        for i, room in enumerate(lst, 1):
            print(f"{i}. {room[1]}")

        while True:
            try:
                num = input("\nВведите номер помещения (0 - отмена): ").strip()
                if num == "0":
                    self.room_id = -1
                    return

                num = int(num)
                if num < 1 or num > len(lst):
                    print("Неверный номер!")
                    continue

                room = RoomsTable().find_by_position(num)
                if not room:
                    print("Помещение не найдено!")
                    continue

                self.room_id = room[0]
                self.room_obj = room
                break

            except ValueError:
                print("Введите число!")

    def show_add_rack(self):
        print(f"\n--- Добавление стеллажа в помещение: {self.room_obj[1]} ---")

        data = {"room_id": self.room_id}

        # Номер стеллажа
        rkt = RacksTable()
        while True:
            rack_number = input("Введите номер стеллажа (0 - отмена): ").strip()
            if rack_number == "0":
                return

            if len(rack_number) == 0:
                print("Номер не может быть пустым!")
                continue

            if len(rack_number) > 20:
                print("Номер слишком длинный (макс. 20 символов)!")
                continue

            # Проверка уникальности номера в помещении
            if not rkt.check_unique_rack_number(self.room_id, rack_number):
                print("Стеллаж с таким номером уже существует в этом помещении!")
                continue

            data["rack_number"] = rack_number
            break

        # Количество ячеек
        while True:
            try:
                count = input("Введите количество ячеек: ").strip()
                if count == "0":
                    return
                count = int(count)
                if count <= 0:
                    print("Количество должно быть положительным числом!")
                    continue
                if count > 1000:
                    print("Слишком большое количество ячеек!")
                    continue
                data["storage_spaces_count"] = count
                break
            except ValueError:
                print("Введите целое число!")

        # Размеры
        dimensions = [
            ("высоту", "space_height"),
            ("ширину", "space_width"),
            ("длину", "space_length"),
        ]

        for dim_name, field_name in dimensions:
            while True:
                try:
                    value = input(f"Введите {dim_name} ячейки (м): ").strip()
                    if value == "0":
                        return
                    value = float(value)
                    if value <= 0:
                        print(f"{dim_name.capitalify()} должна быть положительной!")
                        continue
                    if value > 100:
                        print("Слишком большое значение!")
                        continue
                    data[field_name] = value
                    break
                except ValueError:
                    print("Введите число!")

        # Максимальная нагрузка
        while True:
            try:
                load = input("Введите максимальную нагрузку (кг): ").strip()
                if load == "0":
                    return
                load = float(load)
                if load < 0:
                    print("Нагрузка не может быть отрицательной!")
                    continue
                if load > 1000000:
                    print("Слишком большая нагрузка!")
                    continue
                data["max_total_load"] = load
                break
            except ValueError:
                print("Введите число!")

        try:
            rkt.insert_one(
                [
                    data["room_id"],
                    data["rack_number"],
                    data["storage_spaces_count"],
                    data["space_height"],
                    data["space_width"],
                    data["space_length"],
                    data["max_total_load"],
                ]
            )
            print("\nСтеллаж успешно добавлен!")
        except Exception as e:
            print(f"\nОшибка при добавлении: {e}")

    def show_delete_rack(self):
        print(f"\n--- Удаление стеллажа из помещения: {self.room_obj[1]} ---")

        lst = RacksTable().all_by_room_id(self.room_id)
        if not lst:
            print("Стеллажей нет")
            return

        for i, rack in enumerate(lst, 1):
            print(f"{i}. Стеллаж {rack[2]} - {rack[3]} ячеек, нагрузка: {rack[7]} кг")

        while True:
            try:
                num = input(
                    "\nВведите номер стеллажа для удаления (0 - отмена): "
                ).strip()
                if num == "0":
                    return

                num = int(num)
                if num < 1 or num > len(lst):
                    print("Неверный номер!")
                    continue

                rack = RacksTable().find_by_position(self.room_id, num)
                if not rack:
                    print("Стеллаж не найден!")
                    continue

                print(f"\nВы выбрали: Стеллаж {rack[2]}")
                confirm = input("Вы уверены? (да/нет): ").strip().lower()
                if confirm != "да":
                    print("Операция отменена.")
                    return

                rkt = RacksTable()
                if rkt.delete_by_id(rack[0]):
                    print("Стеллаж удален!")
                else:
                    print("Ошибка при удалении!")
                break

            except ValueError:
                print("Введите число!")
            except Exception as e:
                print(f"Ошибка: {e}")

    def main_cycle(self):
        current_menu = "0"
        next_step = None

        # Инициализация базы при первом запуске
        try:
            rt = RoomsTable()
            rt.create()
            rkt = RacksTable()
            rkt.create()
        except:
            pass

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

        print("\nДо свидания!")
        return

    def test(self):
        DbTable.dbconn.test()


if __name__ == "__main__":
    m = Main()
    m.main_cycle()
