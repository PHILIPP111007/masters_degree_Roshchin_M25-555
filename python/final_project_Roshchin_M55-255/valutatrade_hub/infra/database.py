"""
Singleton для управления JSON-хранилищем
"""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from valutatrade_hub.core.exceptions import DatabaseError
from valutatrade_hub.infra.settings import settings


class DatabaseManager:
    """
    Singleton для управления JSON-хранилищем данных
    """

    _instance = None
    _lock = threading.Lock()
    _file_locks: Dict[str, threading.Lock] = {}

    def __new__(cls):
        """
        Реализация Singleton через __new__
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Инициализация менеджера базы данных"""
        if getattr(self, "_initialized", False):
            return

        self.data_dir = settings.get_data_dir()
        self.data_dir.mkdir(exist_ok=True)

        # Инициализация файлов блокировок
        self._init_file_locks()

        self._initialized = True

    def _init_file_locks(self):
        """Инициализация блокировок для файлов"""
        files = ["users", "portfolios", "rates", "session"]
        for file in files:
            self._file_locks[file] = threading.Lock()

    def _get_file_lock(self, filename: str) -> threading.Lock:
        """
        Получение блокировки для файла

        Args:
            filename: Имя файла

        Returns:
            Объект блокировки
        """
        # Извлекаем имя файла без расширения
        name = Path(filename).stem

        # Создаем блокировку, если ее нет
        if name not in self._file_locks:
            self._file_locks[name] = threading.Lock()

        return self._file_locks[name]

    def _get_file_path(self, filename: str) -> Path:
        """
        Получение полного пути к файлу

        Args:
            filename: Имя файла

        Returns:
            Полный путь
        """
        return self.data_dir / f"{filename}.json"

    def load_data(self, filename: str, default: Any = None) -> Any:
        """
        Загрузка данных из JSON файла

        Args:
            filename: Имя файла
            default: Значение по умолчанию, если файл не существует

        Returns:
            Загруженные данные

        Raises:
            DatabaseError: При ошибке чтения файла
        """
        file_path = self._get_file_path(filename)

        # Если файл не существует, возвращаем значение по умолчанию
        if not file_path.exists():
            return default if default is not None else []

        lock = self._get_file_lock(filename)

        with lock:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                raise DatabaseError(f"Ошибка загрузки файла {filename}: {e}")

    def save_data(self, filename: str, data: Any) -> None:
        """
        Сохранение данных в JSON файл

        Args:
            filename: Имя файла
            data: Данные для сохранения

        Raises:
            DatabaseError: При ошибке записи файла
        """
        file_path = self._get_file_path(filename)

        # Создаем директорию, если ее нет
        file_path.parent.mkdir(exist_ok=True)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise DatabaseError(f"Ошибка сохранения файла {filename}: {e}")

    def update_data(self, filename: str, update_func: callable) -> Any:
        """
        Атомарное обновление данных в файле

        Args:
            filename: Имя файла
            update_func: Функция для обновления данных
                         Принимает текущие данные, возвращает обновленные

        Returns:
            Результат выполнения update_func

        Raises:
            DatabaseError: При ошибке чтения/записи файла
        """
        # lock = self._get_file_lock(filename)

        # with lock:
        try:
            # Загружаем данные
            data = self.load_data(filename, default=[])

            # Обновляем данные
            result = update_func(data)

            # Сохраняем обновленные данные
            self.save_data(filename, data)

            return result
        except Exception as e:
            raise DatabaseError(f"Ошибка обновления файла {filename}: {e}")

    def find_one(self, filename: str, condition: callable) -> Optional[Any]:
        """
        Поиск одного элемента в данных

        Args:
            filename: Имя файла
            condition: Функция-условие для поиска

        Returns:
            Найденный элемент или None
        """
        data = self.load_data(filename, default=[])

        for item in data:
            if condition(item):
                return item

        return None

    def find_all(self, filename: str, condition: callable = None) -> List[Any]:
        """
        Поиск всех элементов в данных

        Args:
            filename: Имя файла
            condition: Функция-условие для фильтрации

        Returns:
            Список найденных элементов
        """
        data = self.load_data(filename, default=[])

        if condition is None:
            return data

        return [item for item in data if condition(item)]

    def insert(self, filename: str, item: Any) -> None:
        """
        Вставка нового элемента в данные

        Args:
            filename: Имя файла
            item: Элемент для вставки
        """

        def update_func(data):
            data.append(item)
            return item

        self.update_data(filename, update_func)

    def update(self, filename: str, condition: callable, update_func: callable) -> bool:
        """
        Обновление элемента в данных

        Args:
            filename: Имя файла
            condition: Функция-условие для поиска элемента
            update_func: Функция для обновления элемента

        Returns:
            True если элемент был обновлен, иначе False
        """

        def bulk_update_func(data):
            for i, item in enumerate(data):
                if condition(item):
                    data[i] = update_func(item)
                    return True
            return False

        return self.update_data(filename, bulk_update_func)

    def delete(self, filename: str, condition: callable) -> bool:
        """
        Удаление элемента из данных

        Args:
            filename: Имя файла
            condition: Функция-условие для поиска элемента

        Returns:
            True если элемент был удален, иначе False
        """

        def bulk_update_func(data):
            for i, item in enumerate(data):
                if condition(item):
                    del data[i]
                    return True
            return False

        return self.update_data(filename, bulk_update_func)

    def backup(self, filename: str) -> Path:
        """
        Создание резервной копии файла

        Args:
            filename: Имя файла

        Returns:
            Путь к резервной копии
        """
        file_path = self._get_file_path(filename)

        if not file_path.exists():
            raise DatabaseError(
                f"Файл {filename} не существует для резервного копирования"
            )

        backup_dir = self.data_dir / "backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{filename}_{timestamp}.json"

        try:
            with open(file_path, "r", encoding="utf-8") as src:
                data = json.load(src)

            with open(backup_path, "w", encoding="utf-8") as dst:
                json.dump(data, dst, indent=2, ensure_ascii=False)

            return backup_path
        except Exception as e:
            raise DatabaseError(f"Ошибка создания резервной копии {filename}: {e}")


# Глобальный экземпляр менеджера базы данных
db_manager = DatabaseManager()
