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
        return {"id": ["serial", "PRIMARY KEY"]}

    def column_names(self):
        # Возвращаем имена колонок в порядке их определения
        return list(self.columns().keys())

    def primary_key(self):
        return ["id"]

    def column_names_without_id(self):
        # Возвращаем имена колонок без ID в порядке определения
        cols = self.column_names()
        if "id" in cols:
            cols.remove("id")
        return cols

    def table_constraints(self):
        return []

    def foreign_keys(self):
        return []

    def create(self):
        """Создание таблицы"""
        try:
            self.dbconn.conn.rollback()

            columns_def = []
            # Сохраняем порядок колонок как в columns()
            for k, v in self.columns().items():
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

    def drop(self):
        """Удаление таблицы"""
        try:
            self.dbconn.conn.rollback()

            query = sql.SQL("DROP TABLE IF EXISTS {table} CASCADE").format(
                table=sql.Identifier(self.full_table_name())
            )

            cur = self.dbconn.conn.cursor()
            cur.execute(query)
            self.dbconn.conn.commit()
            return True
        except psycopg2.Error as e:
            self.dbconn.conn.rollback()
            print(f"Ошибка при удалении таблицы {self.full_table_name()}: {e}")
            return False

    def insert_one(self, vals):
        """Вставка одной записи"""
        try:
            self.dbconn.conn.rollback()

            column_names = self.column_names_without_id()
            if len(vals) != len(column_names):
                print(
                    f"Ошибка: ожидается {len(column_names)} значений для колонок {column_names}, получено {len(vals)}"
                )
                return False

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

    def all(self):
        """Получение всех записей"""
        try:
            self.dbconn.conn.rollback()

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
            print(f"Ошибка при запросе всех записей: {e}")
            return []
