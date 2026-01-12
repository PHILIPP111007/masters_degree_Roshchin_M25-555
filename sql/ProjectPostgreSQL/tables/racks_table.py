# Таблица стеллажей
from dbtable import *


class RacksTable(DbTable):
    def table_name(self):
        return self.dbconn.prefix + "racks"

    def columns(self):
        return {
            "id": ["serial", "PRIMARY KEY"],
            "room_id": ["integer", "REFERENCES rooms(id)", "NOT NULL"],
            "rack_number": ["varchar(20)", "NOT NULL"],
            "storage_spaces_count": ["integer", "NOT NULL"],
            "space_height": ["real", "NOT NULL"],
            "space_width": ["real", "NOT NULL"],
            "space_length": ["real", "NOT NULL"],
            "max_total_load": ["real", "NOT NULL"],
        }

    def primary_key(self):
        return ["id"]

    def table_constraints(self):
        return [
            "UNIQUE (rack_number, room_id)",
            "CHECK (storage_spaces_count > 0)",
            "CHECK (space_height > 0 AND space_width > 0 AND space_length > 0)",
            "CHECK (max_total_load >= 0)",
        ]

    def all_by_room_id(self, room_id):
        sql = "SELECT * FROM " + self.table_name()
        sql += " WHERE room_id = %s"
        sql += " ORDER BY rack_number"
        cur = self.dbconn.conn.cursor()
        cur.execute(sql, (room_id,))
        return cur.fetchall()

    def find_by_room_and_number(self, room_id, rack_number):
        sql = "SELECT * FROM " + self.table_name()
        sql += " WHERE room_id = %s AND rack_number = %s"
        cur = self.dbconn.conn.cursor()
        cur.execute(sql, (room_id, rack_number))
        return cur.fetchone()
