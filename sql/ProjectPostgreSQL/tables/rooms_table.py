# Таблица помещений
from dbtable import *
from psycopg2 import sql


class RoomsTable(DbTable):
    def table_name(self):
        return "rooms"

    def columns(self):
        # Важно: порядок имеет значение!
        return {
            "id": ["serial", "PRIMARY KEY"],
            "room_name": ["varchar(100)", "NOT NULL"],
            "useful_volume": ["real", "NOT NULL"],
            "min_temperature": ["real"],
            "max_temperature": ["real"],
            "min_humidity": ["real"],
            "max_humidity": ["real"],
        }

    def column_names_without_id(self):
        # Явно задаем правильный порядок для вставки
        return [
            "room_name",
            "useful_volume",
            "min_temperature",
            "max_temperature",
            "min_humidity",
            "max_humidity",
        ]

    def primary_key(self):
        return ["id"]

    def find_by_position(self, num):
        sql_query = sql.SQL(
            "SELECT * FROM {table} ORDER BY room_name LIMIT 1 OFFSET %s"
        ).format(table=sql.Identifier(self.full_table_name()))
        cur = self.dbconn.conn.cursor()
        cur.execute(sql_query, (num - 1,))
        return cur.fetchone()

    def find_by_name(self, name):
        """Поиск по названию"""
        query = sql.SQL("SELECT * FROM {table} WHERE room_name = %s").format(
            table=sql.Identifier(self.full_table_name())
        )
        cur = self.dbconn.conn.cursor()
        cur.execute(query, (name,))
        return cur.fetchone()

    def table_constraints(self):
        return [
            "CHECK (useful_volume > 0)",
            "CHECK (COALESCE(min_temperature, -273) < COALESCE(max_temperature, 1000))",
            "CHECK (COALESCE(min_humidity, 0) < COALESCE(max_humidity, 100))",
            "CHECK (COALESCE(min_humidity, 0) >= 0 AND COALESCE(min_humidity, 0) <= 100)",
            "CHECK (COALESCE(max_humidity, 100) >= 0 AND COALESCE(max_humidity, 100) <= 100)",
        ]
