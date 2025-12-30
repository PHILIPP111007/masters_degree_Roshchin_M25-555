def constants():
    """Возвращает модуль как объект констант"""
    import sys

    return sys.modules[__name__]


constants().DATABASE_PATH = None
constants().SEPARATOR = ";"
constants().CACHE = {}

CONST = constants()
