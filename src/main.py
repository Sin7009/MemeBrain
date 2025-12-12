import asyncio
import logging
from aiogram import Bot, Dispatcher
from .services.config import config
from .bot.handlers import router as meme_router

# Устанавливаем базовый уровень логирования
logging.basicConfig(level=logging.INFO)

async def main():
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

if __name__ == "__main__":
    # Для загрузки переменных окружения из .env
    from dotenv import load_dotenv
    load_dotenv() 
    
    # Запускаем асинхронную функцию
    asyncio.run(main())
