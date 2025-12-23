import asyncio
import logging
from aiogram import Bot, Dispatcher
from .services.config import config
from .bot.handlers import router as meme_router
from .services.database import db_service
from .services.metrics import metrics_service

# Устанавливаем базовый уровень логирования
logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализация метрик
    if metrics_service.enabled:
        metrics_service.start_server()
    
    # Инициализация базы данных
    if db_service.enabled:
        await db_service.init_db()
    
    # Инициализация бота и диспетчера
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    
    # Подключение роутера с обработчиками
    dp.include_router(meme_router)
    
    # Запуск процесса поллинга
    try:
        logging.info("Starting meme-generator bot...")
        logging.info(f"Cache enabled: {config.CACHE_ENABLED}")
        logging.info(f"Face swap enabled: {config.FACE_SWAP_ENABLED}")
        logging.info(f"Database enabled: {db_service.enabled}")
        logging.info(f"Metrics enabled: {metrics_service.enabled}")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Error while running bot: {e}")
    finally:
        logging.info("Shutting down bot...")
        await bot.session.close()
        
        # Закрываем подключение к БД
        if db_service.enabled:
            await db_service.close()

if __name__ == "__main__":
    # Для загрузки переменных окружения из .env
    from dotenv import load_dotenv
    load_dotenv() 
    
    # Запускаем асинхронную функцию
    asyncio.run(main())
