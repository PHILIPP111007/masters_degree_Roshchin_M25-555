"""
Планировщик периодического обновления курсов
"""

import logging
import threading
import time
from typing import Optional, Any

from valutatrade_hub.parser_service.config import config
from valutatrade_hub.parser_service.exceptions import RateFetchError
from valutatrade_hub.parser_service.updater import RatesUpdater

logger = logging.getLogger(__name__)


class RatesScheduler:
    """
    Планировщик для автоматического обновления курсов валют
    """

    def __init__(self):
        self.updater = RatesUpdater()
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running = False

    def start(self, interval: int = None) -> None:
        """
        Запуск планировщика

        Args:
            interval: Интервал обновления в секундах
                     (по умолчанию из конфигурации)
        """
        if self._is_running:
            logger.warning("Scheduler is already running")
            return

        if interval is None:
            interval = config.UPDATE_INTERVAL

        self._stop_event.clear()
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            args=(interval,),
            daemon=True,
            name="RatesScheduler",
        )
        self._scheduler_thread.start()
        self._is_running = True
        logger.info(f"Scheduler started with {interval} second interval")

    def stop(self) -> None:
        """Остановка планировщика"""
        if not self._is_running:
            return

        self._stop_event.set()
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        self._is_running = False
        logger.info("Scheduler stopped")

    def _scheduler_loop(self, interval: int) -> None:
        """
        Основной цикл планировщика

        Args:
            interval: Интервал обновления в секундах
        """
        logger.info("Scheduler loop started")

        while not self._stop_event.is_set():
            try:
                # Выполняем обновление
                result = self.updater.run_update()

                if result["success"]:
                    logger.info(
                        f"Scheduled update successful: {result['rates_count']} "
                        "rates updated"
                    )
                else:
                    logger.warning(
                        f"Scheduled update completed with errors: {result['errors']}"
                    )

            except RateFetchError as e:
                logger.error(f"Scheduled update failed: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error in scheduled update: {str(e)}")

            # Ждем указанный интервал или остановку
            for _ in range(interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)

        logger.info("Scheduler loop stopped")

    def run_once(self) -> dict[str, Any]:
        """
        Однократный запуск обновления

        Returns:
            Результат обновления
        """
        try:
            return self.updater.run_update()
        except Exception as e:
            logger.error(f"One-time update failed: {str(e)}")
            raise

    def is_running(self) -> bool:
        """
        Проверка, работает ли планировщик

        Returns:
            True если планировщик работает
        """
        return self._is_running

    def get_status(self) -> dict[str, Any]:
        """
        Получение статуса планировщика

        Returns:
            Информация о статусе планировщика
        """
        update_status = self.updater.get_update_status()
        return {
            "scheduler_running": self._is_running,
            "last_update": update_status["last_refresh"],
            "rates_count": update_status["rates_count"],
            "has_data": update_status["has_data"],
            "update_interval": config.UPDATE_INTERVAL,
        }
