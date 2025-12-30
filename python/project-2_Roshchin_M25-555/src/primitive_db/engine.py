import sys

from src.primitive_db.core import (
    create_database,
    create_table,
    delete,
    drop_table,
    info,
    insert,
    list_tables,
    load_database,
    select,
    update,
)
from src.primitive_db.utils import clear_cache, parse_expression


def run():
    """
    В цикле:
    1) Загружайте актуальные метаданные с помощью load_metadata.
    2) Запрашивайте ввод у пользователя.
    3) Разбирайте введенную строку на команду и аргументы.
    4) После каждой успешной операции (create_table, drop_table) сохраняйте
    измененные метаданные с помощью save_metadata.
    """

    help_string = """
***База данных***

Функции:
* <command> load_database <file_path> -  подключить базу данных
* <command> create_database <имя_базы_данных> <file_path> - создать базу данных
* <command> create_table <имя_таблицы> <table_path> <столбец1:тип> <столбец2:тип> .. - 
создать таблицу
* <command> list_tables - показать список всех таблиц
* <command> drop_table <имя_таблицы> - удалить таблицу
* <command> info <имя_таблицы> - вывести информацию о таблице.
* <command> clear_cache - очистка кеша

* <command> insert into <имя_таблицы> values (<значение1>, <значение2>, ...) -
создать запись.
* <command> select from <имя_таблицы> where <столбец> = <значение> - прочитать
записи по условию.
* <command> select from <имя_таблицы> - прочитать все записи.
* <command> update <имя_таблицы> set <столбец1> = <новое_значение1> where
<столбец_условия> = <значение_условия> - обновить запись.
* <command> delete from <имя_таблицы> where <столбец> = <значение> - удалить запись.

* <command> exit - выход из программы
* <command> help - справочная информация
"""

    print(help_string)

    while True:
        try:
            args = input("Введите команду: ")
            args = args.split(" ")

            if len(args) == 0:
                print("Введите комманду!")
                continue

            command = args[0]

            if command == "help":
                print(help_string)
            elif command == "exit":
                sys.exit(0)
            elif command == "load_database":
                if len(args) < 2:
                    print("Не приведены данные")
                    continue

                file_path = args[1]
                load_database(file_path=file_path)
            elif command == "create_database":
                if len(args) < 3:
                    print("Не приведены данные")
                    continue

                database_name = args[1]
                file_path = args[2]
                create_database(file_path=file_path, database_name=database_name)
            elif command == "list_tables":
                list_tables()
            elif command == "create_table":
                if len(args) < 3:
                    print("Не приведены данные")
                    continue

                table_name = args[1]
                table_path = args[2]
                columns = args[3:]
                create_table(
                    table_name=table_name,
                    table_path=table_path,
                    columns=columns,
                )
            elif command == "drop_table":
                if len(args) < 2:
                    print("Не приведены данные")
                    continue

                table_name = args[1]
                drop_table(table_name=table_name)
            elif command == "info":
                if len(args) != 2:
                    print("Не приведены данные")
                    continue
                table_name = args[1]
                info(table_name=table_name)
            elif command == "clear_cache":
                clear_cache()
            elif command == "select":
                if len(args) < 3:
                    print("Не приведены данные")
                    continue
                table_name = args[2]
                where_clause = None

                flag = True
                for i in range(len(args)):
                    if args[i] == "where":
                        if len(args[i + 1 :]) == 0:
                            print("Не приведены данные")
                            flag = False
                            break
                        where_clause = parse_expression(args[i + 1 :])
                if flag:
                    select(table_name=table_name, where_clause=where_clause)
            elif command == "insert":
                if len(args) < 5 or args[1] != "into" or args[3] != "values":
                    print("Не приведены данные")
                    continue

                table_name = args[2]
                values = " ".join(args[4:])
                insert(table_name=table_name, values=values)
            elif command == "update":
                if len(args) < 4 or args[2] != "set":
                    print("Не приведены данные")
                    continue

                table_name = args[1]
                where_clause = None
                set_clause = None

                flag = True
                for i in range(len(args)):
                    if args[i] == "where":
                        if len(args[i + 1 :]) == 0:
                            print("Не приведены данные")
                            flag = False
                            break
                        where_clause = parse_expression(args[i + 1 :])

                if where_clause is None:
                    print("Ошибка")
                    return

                flag = True
                data = []
                for i in range(len(args)):
                    if args[i] == "set":
                        for j in range(i + 1, len(args) + 1):
                            if args[j] == "where":
                                break
                            data.append(args[j])
                        set_clause = parse_expression(data)
                        break

                if set_clause is None:
                    print("Ошибка")
                    return

                update(
                    table_name=table_name,
                    where_clause=where_clause,
                    set_clause=set_clause,
                )
            elif command == "delete":
                if len(args) < 3:
                    print("Не приведены данные")
                    continue
                table_name = args[2]
                where_clause = None

                flag = True
                for i in range(len(args)):
                    if args[i] == "where":
                        if len(args[i + 1 :]) == 0:
                            print("Не приведены данные")
                            flag = False
                            break
                        where_clause = parse_expression(args[i + 1 :])
                if flag:
                    delete(table_name=table_name, where_clause=where_clause)
            else:
                print(f"Функции <{command}> нет. Попробуйте снова.")
        except KeyboardInterrupt:
            sys.exit(0)
