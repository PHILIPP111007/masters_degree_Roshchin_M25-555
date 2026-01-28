# Базовые действия с таблицами

from dbconnection import *
import psycopg2
from psycopg2 import sql


class DbTable:
    dbconn = None

    def __init__(self):
        return

    def table_name(self):
        # Возвращаем только имя таблицы без префикса
        return "table"

    def full_table_name(self):
        # Полное имя таблицы с префиксом
        if self.dbconn.prefix:
            if self.dbconn.prefix.endswith("."):
                # Если префикс заканчивается точкой, убираем её
                return self.dbconn.prefix.rstrip(".") + "_" + self.table_name()
            elif not self.dbconn.prefix.endswith("_"):
                return self.dbconn.prefix + "_" + self.table_name()
        return self.dbconn.prefix + self.table_name()

    def columns(self):
        return {"test": ["integer", "PRIMARY KEY"]}

    def column_names(self):
        return sorted(self.columns().keys(), key=lambda x: x)

    def primary_key(self):
        return ["id"]

    def column_names_without_id(self):
        res = sorted(self.columns().keys(), key=lambda x: x)
        if "id" in res:
            res.remove("id")
        return res

    def table_constraints(self):
        return []

    def foreign_keys(self):
        return []

    def create(self):
        # Безопасное создание таблицы
        try:
            self.dbconn.conn.rollback()  # Сбрасываем любую активную транзакцию

            columns_def = []
            for k, v in sorted(self.columns().items(), key=lambda x: x[0]):
                col_def = sql.SQL("{column} {definition}").format(
                    column=sql.Identifier(k), definition=sql.SQL(" ".join(v))
                )
                columns_def.append(col_def)

            constraints = self.table_constraints()
            foreign_keys = self.foreign_keys()

            all_definitions = columns_def + [
                sql.SQL(c) for c in constraints + foreign_keys
            ]

            query = sql.SQL(
                "CREATE TABLE IF NOT EXISTS {table} ({definitions})"
            ).format(
                table=sql.Identifier(self.full_table_name()),
                definitions=sql.SQL(", ").join(all_definitions),
            )

            cur = self.dbconn.conn.cursor()
            cur.execute(query)
            self.dbconn.conn.commit()
            return True
        except psycopg2.Error as e:
            self.dbconn.conn.rollback()
            print(f"Ошибка при создании таблицы {self.full_table_name()}: {e}")
            return False
        except Exception as e:
            self.dbconn.conn.rollback()
            print(f"Неизвестная ошибка: {e}")
            return False

    def insert_one(self, vals):
        # Безопасная вставка с параметризованным запросом
        try:
            self.dbconn.conn.rollback()  # Сбрасываем любую активную транзакцию

            column_names = self.column_names_without_id()
            if len(vals) != len(column_names):
                raise ValueError(
                    f"Ожидается {len(column_names)} значений ({column_names}), получено {len(vals)}"
                )

            # Создаем плейсхолдеры для параметров
            placeholders = sql.SQL(", ").join([sql.Placeholder()] * len(vals))

            query = sql.SQL("INSERT INTO {table} ({columns}) VALUES ({values})").format(
                table=sql.Identifier(self.full_table_name()),
                columns=sql.SQL(", ").join(map(sql.Identifier, column_names)),
                values=placeholders,
            )

            cur = self.dbconn.conn.cursor()
            cur.execute(query, vals)
            self.dbconn.conn.commit()
            return True
        except psycopg2.Error as e:
            self.dbconn.conn.rollback()
            print(f"Ошибка при вставке в таблицу {self.full_table_name()}: {e}")
            return False
        except Exception as e:
            self.dbconn.conn.rollback()
            print(f"Неизвестная ошибка при вставке: {e}")
            return False

    def first(self):
        # Безопасный запрос первого элемента
        try:
            self.dbconn.conn.rollback()  # Сбрасываем любую активную транзакцию

            query = sql.SQL("SELECT * FROM {table} ORDER BY {order_by} LIMIT 1").format(
                table=sql.Identifier(self.full_table_name()),
                order_by=sql.SQL(", ").join(map(sql.Identifier, self.primary_key())),
            )
            cur = self.dbconn.conn.cursor()
            cur.execute(query)
            return cur.fetchone()
        except psycopg2.Error as e:
            self.dbconn.conn.rollback()
            print(f"Ошибка при запросе: {e}")
            return None

    def last(self):
        # Безопасный запрос последнего элемента
        try:
            self.dbconn.conn.rollback()  # Сбрасываем любую активную транзакцию

            order_by_desc = [
                sql.SQL("{col} DESC").format(col=sql.Identifier(x))
                for x in self.primary_key()
            ]
            query = sql.SQL("SELECT * FROM {table} ORDER BY {order_by} LIMIT 1").format(
                table=sql.Identifier(self.full_table_name()),
                order_by=sql.SQL(", ").join(order_by_desc),
            )
            cur = self.dbconn.conn.cursor()
            cur.execute(query)
            return cur.fetchone()
        except psycopg2.Error as e:
            self.dbconn.conn.rollback()
            print(f"Ошибка при запросе: {e}")
            return None

    def all(self):
        # Безопасный запрос всех элементов
        try:
            self.dbconn.conn.rollback()  # Сбрасываем любую активную транзакцию

            query = sql.SQL("SELECT * FROM {table} ORDER BY {order_by}").format(
                table=sql.Identifier(self.full_table_name()),
                order_by=sql.SQL(", ").join(map(sql.Identifier, self.primary_key())),
            )
            cur = self.dbconn.conn.cursor()
            cur.execute(query)
            return cur.fetchall()
        except psycopg2.Error as e:
            self.dbconn.conn.rollback()
            # Если таблицы не существует, возвращаем пустой список
            if "relation" in str(e) and "does not exist" in str(e):
                return []
            print(f"Ошибка при запросе всех записей из {self.full_table_name()}: {e}")
            return []
