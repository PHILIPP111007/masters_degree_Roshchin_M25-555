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
        # Создаем таблицу с помощью безопасного SQL-конструирования
        query = sql.SQL("CREATE TABLE {table} (").format(
            table=sql.Identifier(self.table_name())
        )

        # Добавляем колонки
        columns_def = []
        for k, v in sorted(self.columns().items(), key=lambda x: x[0]):
            col_def = sql.SQL("{column} {definition}").format(
                column=sql.Identifier(k), definition=sql.SQL(" ".join(v))
            )
            columns_def.append(col_def)

        # Добавляем ограничения таблицы
        constraints = self.table_constraints()
        foreign_keys = self.foreign_keys()

        all_constraints = columns_def + [sql.SQL(c) for c in constraints + foreign_keys]

        query = sql.SQL("CREATE TABLE {table} ({definitions})").format(
            table=sql.Identifier(self.table_name()),
            definitions=sql.SQL(", ").join(all_constraints),
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

    def find_by_position(self, num):
        # Безопасный запрос по позиции (с OFFSET)
        query = sql.SQL(
            "SELECT * FROM {table} ORDER BY {order_by} LIMIT 1 OFFSET %s"
        ).format(
            table=sql.Identifier(self.table_name()),
            order_by=sql.SQL(", ").join(map(sql.Identifier, self.primary_key())),
        )
        cur = self.dbconn.conn.cursor()
        cur.execute(query, (num - 1,))
        return cur.fetchone()

    def delete_by_id(self, id_value, id_column="id"):
        # Безопасное удаление по ID
        query = sql.SQL("DELETE FROM {table} WHERE {id_column} = %s").format(
            table=sql.Identifier(self.table_name()), id_column=sql.Identifier(id_column)
        )
        cur = self.dbconn.conn.cursor()
        cur.execute(query, (id_value,))
        self.dbconn.conn.commit()
        return cur.rowcount > 0

    def update(self, id_value, data_dict, id_column="id"):
        # Безопасное обновление записи
        if not data_dict:
            return False

        set_clauses = []
        values = []

        for column, value in data_dict.items():
            set_clauses.append(
                sql.SQL("{column} = %s").format(column=sql.Identifier(column))
            )
            values.append(value)

        values.append(id_value)  # Для WHERE условия

        query = sql.SQL(
            "UPDATE {table} SET {set_clause} WHERE {id_column} = %s"
        ).format(
            table=sql.Identifier(self.table_name()),
            set_clause=sql.SQL(", ").join(set_clauses),
            id_column=sql.Identifier(id_column),
        )

        cur = self.dbconn.conn.cursor()
        cur.execute(query, values)
        self.dbconn.conn.commit()
        return cur.rowcount > 0

    def execute_query(self, query, params=None):
        """Безопасное выполнение произвольного запроса"""
        cur = self.dbconn.conn.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)

        if query.strip().upper().startswith("SELECT"):
            return cur.fetchall()
        else:
            self.dbconn.conn.commit()
            return cur.rowcount

    def count(self):
        """Безопасный подсчет записей"""
        query = sql.SQL("SELECT COUNT(*) FROM {table}").format(
            table=sql.Identifier(self.table_name())
        )
        cur = self.dbconn.conn.cursor()
        cur.execute(query)
        return cur.fetchone()[0]
