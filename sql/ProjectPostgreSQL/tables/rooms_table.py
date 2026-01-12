# Таблица помещений
from dbtable import *
from psycopg2 import sql


class RoomsTable(DbTable):
    def table_name(self):
        return self.dbconn.prefix + "rooms"

    def columns(self):
        return {
            "id": ["serial", "PRIMARY KEY"],
            "room_name": ["varchar(100)", "NOT NULL"],
            "useful_volume": ["real", "NOT NULL"],
            "min_temperature": ["real"],
            "max_temperature": ["real"],
            "min_humidity": ["real"],
            "max_humidity": ["real"],
        }

    def primary_key(self):
        return ["id"]

    def find_by_position(self, num):
        sql = "SELECT * FROM " + self.table_name()
        sql += " ORDER BY room_name"
        sql += " LIMIT 1 OFFSET %(offset)s"
        cur = self.dbconn.conn.cursor()
        cur.execute(sql, {"offset": num - 1})
        return cur.fetchone()

    def delete_by_id(self, room_id):
        # Сначала проверяем, есть ли связанные стеллажи
        sql_check = sql.SQL(
            "SELECT COUNT(*) FROM {racks_table} WHERE room_id = %s"
        ).format(racks_table=sql.Identifier(self.dbconn.prefix + "racks"))
        cur = self.dbconn.conn.cursor()
        cur.execute(sql_check, (room_id,))
        count = cur.fetchone()[0]

        if count > 0:
            return (
                False,
                f"Невозможно удалить помещение: имеется {count} связанных стеллажей",
            )

        # Удаляем помещение
        query = sql.SQL("DELETE FROM {table} WHERE id = %s").format(
            table=sql.Identifier(self.table_name())
        )
        cur.execute(query, (room_id,))
        self.dbconn.conn.commit()
        return True, "Помещение удалено"

    def update(self, room_id, data):
        sql = "UPDATE " + self.table_name() + " SET "
        sql += "room_name = %s, useful_volume = %s, "
        sql += "min_temperature = %s, max_temperature = %s, "
        sql += "min_humidity = %s, max_humidity = %s "
        sql += "WHERE id = %s"

        cur = self.dbconn.conn.cursor()
        cur.execute(
            sql,
            (
                data["room_name"],
                data["useful_volume"],
                data["min_temperature"],
                data["max_temperature"],
                data["min_humidity"],
                data["max_humidity"],
                room_id,
            ),
        )
        self.dbconn.conn.commit()

    def table_constraints(self):
        return [
            "CHECK (useful_volume > 0)",
            "CHECK (COALESCE(min_temperature, -273) < COALESCE(max_temperature, 1000))",
            "CHECK (COALESCE(min_humidity, 0) < COALESCE(max_humidity, 100))",
            "CHECK (COALESCE(min_humidity, 0) >= 0 AND COALESCE(min_humidity, 0) <= 100)",
            "CHECK (COALESCE(max_humidity, 100) >= 0 AND COALESCE(max_humidity, 100) <= 100)",
        ]
