# Таблица помещений
from dbtable import *
from psycopg2 import sql


class RoomsTable(DbTable):
    def table_name(self):
        return "rooms"

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

    def column_names_without_id(self):
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

    def delete_by_position(self, num):
        """Удаление помещения по порядковому номеру"""
        room = self.find_by_position(num)
        if not room:
            return False, "Помещение не найдено"

        # Проверяем, есть ли связанные стеллажи
        sql_check = sql.SQL(
            "SELECT COUNT(*) FROM {racks_table} WHERE room_id = %s"
        ).format(racks_table=sql.Identifier(self.dbconn.prefix + "racks"))
        cur = self.dbconn.conn.cursor()
        cur.execute(sql_check, (room[0],))
        count = cur.fetchone()[0]

        if count > 0:
            return (
                False,
                f"Невозможно удалить помещение: имеется {count} связанных стеллажей",
            )

        # Удаляем помещение
        query = sql.SQL("DELETE FROM {table} WHERE id = %s").format(
            table=sql.Identifier(self.full_table_name())
        )
        cur.execute(query, (room[0],))
        self.dbconn.conn.commit()
        return True, "Помещение удалено"

    def update_by_position(self, num, data):
        """Обновление помещения по порядковому номеру"""
        room = self.find_by_position(num)
        if not room:
            return False, "Помещение не найдено"

        set_clauses = []
        values = []

        for key in [
            "room_name",
            "useful_volume",
            "min_temperature",
            "max_temperature",
            "min_humidity",
            "max_humidity",
        ]:
            if key in data:
                set_clauses.append(
                    sql.SQL("{column} = %s").format(column=sql.Identifier(key))
                )
                values.append(data[key])

        if not set_clauses:
            return False, "Нет данных для обновления"

        values.append(room[0])  # Для WHERE условия

        query = sql.SQL("UPDATE {table} SET {set_clause} WHERE id = %s").format(
            table=sql.Identifier(self.full_table_name()),
            set_clause=sql.SQL(", ").join(set_clauses),
        )

        try:
            cur = self.dbconn.conn.cursor()
            cur.execute(query, values)
            self.dbconn.conn.commit()
            return True, "Помещение обновлено"
        except Exception as e:
            self.dbconn.conn.rollback()
            return False, f"Ошибка при обновлении: {e}"

    def table_constraints(self):
        return [
            "CHECK (useful_volume > 0)",
            "CHECK (COALESCE(min_temperature, -273) < COALESCE(max_temperature, 1000))",
            "CHECK (COALESCE(min_humidity, 0) < COALESCE(max_humidity, 100))",
            "CHECK (COALESCE(min_humidity, 0) >= 0 AND COALESCE(min_humidity, 0) <= 100)",
            "CHECK (COALESCE(max_humidity, 100) >= 0 AND COALESCE(max_humidity, 100) <= 100)",
        ]
