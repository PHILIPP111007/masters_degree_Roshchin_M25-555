import json
import os
import re

from src.decorators import handle_db_errors
from src.primitive_db.constants import CONST


@handle_db_errors
def check_table_exists(table_name: str) -> str | None:
    """
    Check if table exists and returns table path.
    """

    if CONST.DATABASE_PATH is None or (
        CONST.DATABASE_PATH is not None and not os.path.exists(CONST.DATABASE_PATH)
    ):
        print(
            f"DATABASE {CONST.DATABASE_PATH} не подключена, вызовите <load_database> "
            "команду"
        )
        return None

    with open(CONST.DATABASE_PATH, "r", encoding="utf-8") as file:
        data: dict = json.load(file)

    tables = data.get("tables")
    if not isinstance(tables, list):
        print("Данные повреждены")
        return None

    for table in tables:
        if not isinstance(table, dict):
            continue
        name = table.get("name")
        if name == table_name:
            path = table.get("path")
            if path is not None and os.path.exists(path):
                return path
            else:
                print(f"Таблицы {table_name} не существует")
                return None
    print(f"Таблицы {table_name} не существует")
    return None


@handle_db_errors
def get_table_columns(table_name: str) -> list[dict[str, str]] | None:
    if CONST.DATABASE_PATH is None or (
        CONST.DATABASE_PATH is not None and not os.path.exists(CONST.DATABASE_PATH)
    ):
        print(
            f"DATABASE {CONST.DATABASE_PATH} не подключена, вызовите <load_database> "
            "команду"
        )
        return None

    with open(CONST.DATABASE_PATH, "r", encoding="utf-8") as file:
        data: dict = json.load(file)

    tables = data.get("tables")
    if not isinstance(tables, list):
        print("Данные повреждены")
        return None

    for table in tables:
        if not isinstance(table, dict):
            continue
        name = table.get("name")
        if name == table_name:
            columns: list[dict[str, str]] | None = table.get("columns")
            return columns
    return None


@handle_db_errors
def process_where_clause(
    table_name: str, where_clause: dict[str, str]
) -> dict[str, str | int | bool] | None:
    columns = get_table_columns(table_name=table_name)
    if columns is None:
        return None

    where_clause_processed: dict[str, str | int | bool] = {}
    for key, value in where_clause.items():
        for column in columns:
            if column["name"] != key:
                continue
            t = column["type"]

            new_value: str | int | bool | None = None
            if t == "str":
                new_value = str(value)
            elif t == "int":
                new_value = int(value)
            elif t == "bool":
                new_value = bool(int(value))

            if new_value is None:
                return None
            where_clause_processed[key] = new_value
    return where_clause_processed


def parse_expression(where_clause: list[str]) -> dict[str, str]:
    """
    Парсит условие WHERE из SQL-запроса и возвращает словарь с условиями.

    Args:
        where_clause: Список строк с условиями после WHERE

    Returns:
        Словарь, где ключи - названия полей, значения - условия
    """
    condition_str = " ".join(where_clause).strip()
    condition_str = re.sub(r"\s+", " ", condition_str)

    result = {}

    conditions = re.split(r"\s+(AND|OR)\s+", condition_str, flags=re.IGNORECASE)
    conditions = [cond for cond in conditions if cond.upper() not in ["AND", "OR"]]

    for condition in conditions:
        condition = condition.strip()
        if not condition:
            continue

        patterns = [
            # Простое равенство: field = value
            r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)$",
            # Неравенство: field != value или field <> value
            r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*(!=|<>)\s*(.+)$",
            # Сравнения: field > value, field < value, field >= value, field <= value
            r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*(>|<|>=|<=)\s*(.+)$",
        ]

        for pattern in patterns:
            match = re.match(pattern, condition, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    field, value = match.groups()
                    value = re.sub('"', "", value)
                    result[field] = value.strip()
                elif len(match.groups()) == 3:
                    field, operator, value = match.groups()
                    result[field] = f"{operator} {value}".strip()
                break
        else:
            # Если ни один паттерн не подошел, добавляем как есть
            result["unknown"] = condition

    return result


def clear_cache():
    """Очищает весь кеш"""
    CONST.CACHE.clear()
    print("Кеш очищен")
