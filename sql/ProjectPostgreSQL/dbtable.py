# Базовые действия с таблицами

from dbconnection import *
import psycopg2
from psycopg2 import sql


class DbTable:
    dbconn = None

    def __init__(self):
        return

    def table_name(self):
        return self.dbconn.prefix + "table"

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
        columns_def = []
        for k, v in sorted(self.columns().items(), key=lambda x: x[0]):
            col_def = sql.SQL("{column} {definition}").format(
                column=sql.Identifier(k), definition=sql.SQL(" ".join(v))
            )
            columns_def.append(col_def)

        constraints = self.table_constraints()
        foreign_keys = self.foreign_keys()

        all_definitions = columns_def + [sql.SQL(c) for c in constraints + foreign_keys]

        query = sql.SQL("CREATE TABLE {table} ({definitions})").format(
            table=sql.Identifier(self.table_name()),
            definitions=sql.SQL(", ").join(all_definitions),
        )

        cur = self.dbconn.conn.cursor()
        cur.execute(query)
        self.dbconn.conn.commit()
        return

    def drop(self):
        # Безопасное удаление таблицы
        query = sql.SQL("DROP TABLE IF EXISTS {table} CASCADE").format(
            table=sql.Identifier(self.table_name())
        )
        cur = self.dbconn.conn.cursor()
        cur.execute(query)
        self.dbconn.conn.commit()
        return

    def insert_one(self, vals):
        # Безопасная вставка с параметризованным запросом
        if len(vals) != len(self.column_names_without_id()):
            raise ValueError(
                f"Ожидается {len(self.column_names_without_id())} значений, получено {len(vals)}"
            )

        # Создаем плейсхолдеры для параметров
        placeholders = sql.SQL(", ").join([sql.Placeholder()] * len(vals))

        query = sql.SQL("INSERT INTO {table} ({columns}) VALUES ({values})").format(
            table=sql.Identifier(self.table_name()),
            columns=sql.SQL(", ").join(
                map(sql.Identifier, self.column_names_without_id())
            ),
            values=placeholders,
        )

        cur = self.dbconn.conn.cursor()
        cur.execute(query, vals)
        self.dbconn.conn.commit()
        return

    def first(self):
        # Безопасный запрос первого элемента
        query = sql.SQL("SELECT * FROM {table} ORDER BY {order_by} LIMIT 1").format(
            table=sql.Identifier(self.table_name()),
            order_by=sql.SQL(", ").join(map(sql.Identifier, self.primary_key())),
        )
        cur = self.dbconn.conn.cursor()
        cur.execute(query)
        return cur.fetchone()

    def last(self):
        # Безопасный запрос последнего элемента
        order_by_desc = [
            sql.SQL("{col} DESC").format(col=sql.Identifier(x))
            for x in self.primary_key()
        ]
        query = sql.SQL("SELECT * FROM {table} ORDER BY {order_by} LIMIT 1").format(
            table=sql.Identifier(self.table_name()),
            order_by=sql.SQL(", ").join(order_by_desc),
        )
        cur = self.dbconn.conn.cursor()
        cur.execute(query)
        return cur.fetchone()

    def all(self):
        # Безопасный запрос всех элементов
        query = sql.SQL("SELECT * FROM {table} ORDER BY {order_by}").format(
            table=sql.Identifier(self.table_name()),
            order_by=sql.SQL(", ").join(map(sql.Identifier, self.primary_key())),
        )
        cur = self.dbconn.conn.cursor()
        cur.execute(query)
        return cur.fetchall()
