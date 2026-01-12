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
        query = sql.SQL(
            "SELECT * FROM {table} WHERE room_id = %s ORDER BY rack_number"
        ).format(table=sql.Identifier(self.table_name()))
        cur = self.dbconn.conn.cursor()
        cur.execute(query, (room_id,))
        return cur.fetchall()

    def find_by_position(self, room_id, num):
        """Поиск стеллажа по порядковому номеру в списке для конкретного помещения"""
        query = sql.SQL("""
            SELECT * FROM {table} 
            WHERE room_id = %s 
            ORDER BY rack_number 
            LIMIT 1 OFFSET %s
        """).format(table=sql.Identifier(self.table_name()))
        cur = self.dbconn.conn.cursor()
        cur.execute(query, (room_id, num - 1))
        return cur.fetchone()

    def delete_by_position(self, room_id, num):
        """Удаление по порядковому номеру в списке"""
        rack = self.find_by_position(room_id, num)
        if not rack:
            return False, "Стеллаж не найден"

        return self.delete_by_id(rack[0])

    def delete_by_id(self, rack_id):
        """Внутренний метод удаления по ID"""
        query = sql.SQL("DELETE FROM {table} WHERE id = %s").format(
            table=sql.Identifier(self.table_name())
        )
        cur = self.dbconn.conn.cursor()
        cur.execute(query, (rack_id,))
        self.dbconn.conn.commit()
        return True, "Стеллаж удален"

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

    def get_room_name_for_rack(self, rack_id):
        """Получить название помещения для стеллажа (внутренний метод)"""
        query = sql.SQL("""
            SELECT r.room_name 
            FROM {rooms_table} r
            JOIN {racks_table} rk ON r.id = rk.room_id
            WHERE rk.id = %s
        """).format(
            rooms_table=sql.Identifier(self.dbconn.prefix + "rooms"),
            racks_table=sql.Identifier(self.table_name()),
        )
        cur = self.dbconn.conn.cursor()
        cur.execute(query, (rack_id,))
        result = cur.fetchone()
        return result[0] if result else None
