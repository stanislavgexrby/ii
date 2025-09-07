# main.py
"""
TeammateBot - Бот для поиска сокомандников в Dota 2 и CS2
Точка входа в приложение
"""

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import Settings
from database.database import Database
from handlers import start, profile, search, likes

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
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
    # Важно: роутеры с FSM состояниями должны быть первыми!
    dp.include_router(profile.router)  # FSM для создания анкет
    dp.include_router(search.router)   # FSM для поиска
    dp.include_router(likes.router)    # Обработка лайков
    dp.include_router(start.router)    # Команды и основная навигация
    
    logger.info("📋 Роутеры зарегистрированы")
    
    # Создание папки для данных
    os.makedirs('data', exist_ok=True)
    
    logger.info("🚀 TeammateBot запускается...")
    
    # Уведомление админа о запуске
    try:
        stats = db.get_stats()
        await bot.send_message(
            settings.ADMIN_ID, 
            f"🤖 TeammateBot успешно запущен!\n\n"
            f"📊 Статистика:\n"
            f"• Всего пользователей: {stats['total_users']}\n"
            f"• Dota 2: {stats['dota_users']}\n"
            f"• CS2: {stats['cs_users']}\n"
            f"• Активных за неделю: {stats['active_users']}\n"
            f"• Матчей: {stats['total_matches']}\n\n"
            f"🎮 Бот готов к работе!"
        )
    except Exception as e:
        logger.warning(f"Не удалось отправить уведомление админу: {e}")
    
    try:
        # Запуск polling
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