import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.config import config
from app.core.database.connection import db_manager
from app.bot.handlers import register_all_handlers
from app.tasks.scheduler import start_scheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO if config.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Главная функция"""
    logger.info("🚀 Запуск Яшел Трекер...")
    
    # Инициализация базы данных
    await db_manager.initialize_database()
    
    # Создание бота и диспетчера
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрация обработчиков
    register_all_handlers(dp)
    
    # Запуск планировщика задач
    start_scheduler()
    
    try:
        logger.info("✅ Бот запущен и готов к работе")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    finally:
        await bot.session.close()
        logger.info("👋 Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())
