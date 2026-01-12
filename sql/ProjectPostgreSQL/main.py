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
        menu = """Система управления складскими помещениями
Основное меню (выберите цифру в соответствии с необходимым действием): 
    1 - просмотр помещений;
    2 - сброс и инициализация таблиц;
    9 - выход."""
        print(menu)
        return

    def read_next_step(self):
        return input("=> ").strip()

    def after_main_menu(self, next_step):
        if next_step == "2":
            self.db_drop()
            self.db_init()
            self.db_insert_somethings()
            print("Таблицы созданы заново!")
            return "0"
        elif next_step != "1" and next_step != "9":
            print("Выбрано неверное число! Повторите ввод!")
            return "0"
        else:
            return next_step

    def show_rooms(self):
        self.room_id = -1
        menu = """Список помещений:
№\tНазвание\tОбъем\tТемпература\tВлажность"""
        print(menu)
        lst = RoomsTable().all()
        for i, room in enumerate(lst, 1):
            temp_range = f"{room[3]}-{room[4]}°C" if room[3] and room[4] else "н/д"
            humidity_range = f"{room[5]}-{room[6]}%" if room[5] and room[6] else "н/д"
            print(f"{i}\t{room[1]}\t{room[2]}м³\t{temp_range}\t{humidity_range}")

        menu = """Дальнейшие операции: 
    0 - возврат в главное меню;
    3 - добавление нового помещения;
    4 - удаление помещения;
    5 - просмотр стеллажей в помещении;
    9 - выход."""
        print(menu)
        return

    def after_show_rooms(self, next_step):
        while True:
            if next_step == "4":
                print("Пока не реализовано!")
                return "1"
            elif next_step == "6" or next_step == "7":
                print("Пока не реализовано!")
                next_step = "5"
            elif next_step == "5":
                next_step = self.show_racks_by_room()
            elif next_step != "0" and next_step != "9" and next_step != "3":
                print("Выбрано неверное число! Повторите ввод!")
                return "1"
            else:
                return next_step

    def show_add_room(self):
        data = []

        # Название помещения
        data.append(input("Введите название помещения (1 - отмена): ").strip())
        if data[0] == "1":
            return
        while len(data[0].strip()) == 0:
            data[0] = input(
                "Название не может быть пустым! Введите название заново (1 - отмена):"
            ).strip()
            if data[0] == "1":
                return

        # Полезный объем
        while True:
            try:
                volume = input("Введите полезный объем (м³) (1 - отмена): ").strip()
                if volume == "1":
                    return
                volume = float(volume)
                if volume <= 0:
                    print("Объем должен быть положительным числом!")
                    continue
                data.append(volume)
                break
            except ValueError:
                print("Введите число!")

        # Минимальная температура
        temp_min = input(
            "Введите минимальную температуру (Enter для пропуска): "
        ).strip()
        data.append(float(temp_min) if temp_min else None)

        # Максимальная температура
        temp_max = input(
            "Введите максимальную температуру (Enter для пропуска): "
        ).strip()
        data.append(float(temp_max) if temp_max else None)

        # Минимальная влажность
        humidity_min = input(
            "Введите минимальную влажность % (Enter для пропуска): "
        ).strip()
        data.append(float(humidity_min) if humidity_min else None)

        # Максимальная влажность
        humidity_max = input(
            "Введите максимальную влажность % (Enter для пропуска): "
        ).strip()
        data.append(float(humidity_max) if humidity_max else None)

        RoomsTable().insert_one(data)
        print("Помещение успешно добавлено!")
        return

    def show_racks_by_room(self):
        if self.room_id == -1:
            while True:
                num = input("Укажите номер строки с помещением (0 - отмена): ")
                while len(num.strip()) == 0:
                    num = input(
                        "Пустая строка. Повторите ввод! Укажите номер строки с помещением (0 - отмена): "
                    )
                if num == "0":
                    return "1"
                try:
                    room = RoomsTable().find_by_position(int(num))
                    if not room:
                        print("Введено неверное число!")
                    else:
                        self.room_id = int(room[0])
                        self.room_obj = room
                        break
                except ValueError:
                    print("Введите число!")

        print(f"\nПомещение: {self.room_obj[1]}")
        print(f"Объем: {self.room_obj[2]} м³")

        print("\nСтеллажи в помещении:")
        print("№\tНомер\tЯчеек\tРазмеры (В×Ш×Г)\tМакс. нагрузка")

        lst = RacksTable().all_by_room_id(self.room_id)
        if not lst:
            print("Стеллажей нет")
        else:
            for i, rack in enumerate(lst, 1):
                dimensions = f"{rack[4]}×{rack[5]}×{rack[6]} м"
                print(f"{i}\t{rack[2]}\t{rack[3]}\t{dimensions}\t{rack[7]} кг")

        menu = """Дальнейшие операции:
    0 - возврат в главное меню;
    1 - возврат к просмотру помещений;
    6 - добавление нового стеллажа;
    7 - удаление стеллажа;
    9 - выход."""
        print(menu)
        return self.read_next_step()

    def show_add_rack(self):
        if self.room_id == -1:
            print("Сначала выберите помещение!")
            return

        data = [self.room_id]

        # Номер стеллажа
        data.append(input("Введите номер стеллажа (1 - отмена): ").strip())
        if data[1] == "1":
            return
        while len(data[1].strip()) == 0:
            data[1] = input(
                "Номер не может быть пустым! Введите номер заново (1 - отмена):"
            ).strip()
            if data[1] == "1":
                return

        # Количество ячеек
        while True:
            try:
                count = input("Введите количество ячеек: ").strip()
                count = int(count)
                if count <= 0:
                    print("Количество должно быть положительным числом!")
                    continue
                data.append(count)
                break
            except ValueError:
                print("Введите целое число!")

        # Размеры
        dimensions = ["высоту", "ширину", "длину"]
        for dim_name in dimensions:
            while True:
                try:
                    value = input(f"Введите {dim_name} ячейки (м): ").strip()
                    value = float(value)
                    if value <= 0:
                        print(f"{dim_name.capitalize()} должна быть положительной!")
                        continue
                    data.append(value)
                    break
                except ValueError:
                    print("Введите число!")

        # Максимальная нагрузка
        while True:
            try:
                load = input("Введите максимальную нагрузку (кг): ").strip()
                load = float(load)
                if load < 0:
                    print("Нагрузка не может быть отрицательной!")
                    continue
                data.append(load)
                break
            except ValueError:
                print("Введите число!")

        RacksTable().insert_one(data)
        print("Стеллаж успешно добавлен!")
        return

    def main_cycle(self):
        current_menu = "0"
        next_step = None
        while current_menu != "9":
            if current_menu == "0":
                self.show_main_menu()
                next_step = self.read_next_step()
                current_menu = self.after_main_menu(next_step)
            elif current_menu == "1":
                self.show_rooms()
                next_step = self.read_next_step()
                current_menu = self.after_show_rooms(next_step)
            elif current_menu == "3":
                self.show_add_room()
                current_menu = "1"
            elif current_menu == "6":
                self.show_add_rack()
                current_menu = "5"
            elif current_menu == "5":
                current_menu = self.show_racks_by_room()
        print("До свидания!")
        return

    def test(self):
        DbTable.dbconn.test()


m = Main()
# Откомментируйте для теста соединения с БД
# m.test()
m.main_cycle()
