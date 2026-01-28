# Таблица стеллажей
from dbtable import *
from psycopg2 import sql


class RacksTable(DbTable):
    def table_name(self):
        return "racks"

    def columns(self):
        # Важно: порядок имеет значение!
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
        # Явно задаем правильный порядок для вставки
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
