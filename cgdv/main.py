# main.py
"""
GameMatch Bot - Telegram бот для знакомств геймеров
Точка входа в приложение
"""

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import Settings
from database.database import Database
from handlers import start, profile, matching, common

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска бота"""
    
    # Инициализация настроек
    settings = Settings()
    
    # Проверка конфигурации
    if not settings.validate():
        logger.error("❌ Ошибка в конфигурации. Проверьте настройки.")
        return
    
    # Инициализация базы данных
    db = Database()
    
    # Создание бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(matching.router)
    dp.include_router(common.router)  # Должен быть последним
    
    # Создание папки для данных
    os.makedirs('data', exist_ok=True)
    
    logger.info("🚀 GameMatch бот запускается...")
    
    # Уведомление админа о запуске
    try:
        await bot.send_message(
            settings.ADMIN_ID,
            "🤖 GameMatch бот успешно запущен!\n\n"
            f"📊 Версия: 1.0\n"
            f"🗂️ База данных: {db.db_path}"
        )
    except Exception as e:
        logger.warning(f"Не удалось отправить уведомление админу: {e}")
    
    try:
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")