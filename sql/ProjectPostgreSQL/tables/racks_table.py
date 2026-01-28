# Таблица стеллажей
from dbtable import *
from psycopg2 import sql


class RacksTable(DbTable):
    def table_name(self):
        return "racks"

    def columns(self):
        return {
            "id": ["serial", "PRIMARY KEY"],
            "room_id": ["integer", "NOT NULL"],
            "rack_number": ["varchar(20)", "NOT NULL"],
            "storage_spaces_count": ["integer", "NOT NULL"],
            "space_height": ["real", "NOT NULL"],
            "space_width": ["real", "NOT NULL"],
            "space_length": ["real", "NOT NULL"],
            "max_total_load": ["real", "NOT NULL"],
        }

    def column_names_without_id(self):
        return [
            "room_id",
            "rack_number",
            "storage_spaces_count",
            "space_height",
            "space_width",
            "space_length",
            "max_total_load",
        ]

    def primary_key(self):
        return ["id"]

    def foreign_keys(self):
        return [
            "FOREIGN KEY (room_id) REFERENCES {prefix}rooms(id) ON DELETE CASCADE".format(
                prefix=self.dbconn.prefix
            )
        ]

    def table_constraints(self):
        return [
            "UNIQUE (rack_number, room_id)",
            "CHECK (storage_spaces_count > 0)",
            "CHECK (space_height > 0 AND space_width > 0 AND space_length > 0)",
            "CHECK (max_total_load >= 0)",
        ]

    def all_by_room_id(self, room_id):
        """Получить все стеллажи для помещения"""
        query = sql.SQL(
            "SELECT * FROM {table} WHERE room_id = %s ORDER BY rack_number"
        ).format(table=sql.Identifier(self.full_table_name()))
        cur = self.dbconn.conn.cursor()
        cur.execute(query, (room_id,))
        return cur.fetchall()

    def find_by_position(self, room_id, num):
        """Найти стеллаж по порядковому номеру в конкретном помещении"""
        query = sql.SQL("""
            SELECT * FROM {table} 
            WHERE room_id = %s 
            ORDER BY rack_number 
            LIMIT 1 OFFSET %s
        """).format(table=sql.Identifier(self.full_table_name()))
        cur = self.dbconn.conn.cursor()
        cur.execute(query, (room_id, num - 1))
        return cur.fetchone()

    def delete_by_position(self, room_id, num):
        """Удалить стеллаж по порядковому номеру"""
        rack = self.find_by_position(room_id, num)
        if not rack:
            return False, "Стеллаж не найден"

        query = sql.SQL("DELETE FROM {table} WHERE id = %s").format(
            table=sql.Identifier(self.full_table_name())
        )
        cur = self.dbconn.conn.cursor()
        cur.execute(query, (rack[0],))
        self.dbconn.conn.commit()
        return True, "Стеллаж удален"

    def check_unique_rack_number(self, room_id, rack_number):
        """Проверить уникальность номера стеллажа в помещении"""
        query = sql.SQL(
            "SELECT COUNT(*) FROM {table} WHERE room_id = %s AND rack_number = %s"
        ).format(table=sql.Identifier(self.full_table_name()))

        cur = self.dbconn.conn.cursor()
        cur.execute(query, (room_id, rack_number))
        return cur.fetchone()[0] == 0
