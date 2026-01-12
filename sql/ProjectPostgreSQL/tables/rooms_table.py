# Таблица помещений
from dbtable import *


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

    def find_by_position(self, num):
        sql = "SELECT * FROM " + self.table_name()
        sql += " ORDER BY "
        sql += ", ".join(self.primary_key())
        sql += " LIMIT 1 OFFSET %(offset)s"
        cur = self.dbconn.conn.cursor()
        cur.execute(sql, {"offset": num - 1})
        return cur.fetchone()

    def table_constraints(self):
        return [
            "CHECK (useful_volume > 0)",
            "CHECK (min_temperature < max_temperature)",
            "CHECK (min_humidity < max_humidity)",
        ]
