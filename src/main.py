import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Устанавливаем базовый уровень логирования
logging.basicConfig(level=logging.INFO)


class SingleInstanceLock:
    """Примитивный PID-lock, чтобы не запускать несколько polling-инстансов."""

    def __init__(self, lock_path: str = "/tmp/memebrain_bot.lock"):
        self.lock_file = Path(lock_path)
        self.acquired = False

    @staticmethod
    def _is_process_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def acquire(self) -> bool:
        current_pid = os.getpid()

        if self.lock_file.exists():
            try:
                existing_pid_raw = self.lock_file.read_text(encoding="utf-8").strip()
                existing_pid = int(existing_pid_raw)
            except (ValueError, OSError):
                existing_pid = None

            if existing_pid and self._is_process_alive(existing_pid):
                logging.error("MemeBrain уже запущен (PID %s). Второй инстанс не будет стартован.", existing_pid)
                return False

            # stale lock
            try:
                self.lock_file.unlink(missing_ok=True)
            except OSError:
                logging.error("Не удалось удалить stale lock-файл: %s", self.lock_file)
                return False

        try:
            self.lock_file.write_text(str(current_pid), encoding="utf-8")
            self.acquired = True
            return True
        except OSError as e:
            logging.error("Не удалось создать lock-файл %s: %s", self.lock_file, e)
            return False

    def release(self) -> None:
        if not self.acquired:
            return
        try:
            self.lock_file.unlink(missing_ok=True)
        except OSError as e:
            logging.warning("Не удалось удалить lock-файл %s: %s", self.lock_file, e)
        finally:
            self.acquired = False


async def main():
    # Важно: подгружаем .env ДО импортов, которые валидируют конфиг
    load_dotenv()

    from aiogram import Bot, Dispatcher
    from .services.config import config
    from .bot.handlers import router as meme_router

    lock = SingleInstanceLock()
    if not lock.acquire():
        return

    # Инициализация бота и диспетчера
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    # Подключение роутера с обработчиками
    dp.include_router(meme_router)

    # Запуск процесса поллинга
    try:
        logging.info("Starting meme-generator bot...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Error while running bot: {e}")
    finally:
        logging.info("Shutting down bot...")
        await bot.session.close()
        lock.release()


if __name__ == "__main__":
    # Запускаем асинхронную функцию
    asyncio.run(main())
