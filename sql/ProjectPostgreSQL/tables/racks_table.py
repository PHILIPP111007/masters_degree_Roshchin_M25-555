# Таблица стеллажей
from dbtable import *
from psycopg2 import sql


class RacksTable(DbTable):
    def table_name(self):
        return self.dbconn.prefix + "racks"

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
        sql = "SELECT * FROM " + self.table_name()
        sql += " WHERE room_id = %s"
        sql += " ORDER BY rack_number"
        cur = self.dbconn.conn.cursor()
        cur.execute(sql, (room_id,))
        return cur.fetchall()

    def find_by_position(self, room_id, num):
        sql = "SELECT * FROM " + self.table_name()
        sql += " WHERE room_id = %s"
        sql += " ORDER BY rack_number"
        sql += " LIMIT 1 OFFSET %(offset)s"
        cur = self.dbconn.conn.cursor()
        cur.execute(sql, {"room_id": room_id, "offset": num - 1})
        return cur.fetchone()

    def delete_by_id(self, rack_id):
        sql = "DELETE FROM " + self.table_name() + " WHERE id = %s"
        cur = self.dbconn.conn.cursor()
        cur.execute(sql, (rack_id,))
        self.dbconn.conn.commit()
        return True

    def check_unique_rack_number(self, room_id, rack_number, exclude_id=None):
        query = sql.SQL(
            "SELECT COUNT(*) FROM {table} WHERE room_id = %s AND rack_number = %s"
        ).format(table=sql.Identifier(self.table_name()))

        params = [room_id, rack_number]

        if exclude_id:
            query = sql.SQL(
                "SELECT COUNT(*) FROM {table} WHERE room_id = %s AND rack_number = %s AND id != %s"
            ).format(table=sql.Identifier(self.table_name()))
            params.append(exclude_id)

        cur = self.dbconn.conn.cursor()
        cur.execute(query, params)
        return cur.fetchone()[0] == 0
