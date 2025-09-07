import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class Settings:
    """Класс настроек бота"""
    
    def __init__(self):
        # Основные настройки бота
        self.BOT_TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
        self.ADMIN_ID: int = int(os.getenv("ADMIN_ID", "123456789"))
        
        # Настройки базы данных
        self.DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/gamebot.db")
        
        # Настройки приложения
        self.DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        
        # Лимиты приложения
        self.MAX_BIO_LENGTH: int = int(os.getenv("MAX_BIO_LENGTH", "500"))
        self.MAX_NAME_LENGTH: int = int(os.getenv("MAX_NAME_LENGTH", "50"))
        self.DAILY_LIKES_LIMIT: int = int(os.getenv("DAILY_LIKES_LIMIT", "50"))
        
        # Настройки поиска
        self.MATCHES_PER_REQUEST: int = int(os.getenv("MATCHES_PER_REQUEST", "1"))
        self.MIN_AGE: int = int(os.getenv("MIN_AGE", "16"))
        self.MAX_AGE: int = int(os.getenv("MAX_AGE", "99"))
    
    def validate(self) -> bool:
        """Валидация конфигурации"""
        errors = []
        
        # Проверка токена бота
        if self.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            errors.append("BOT_TOKEN не установлен")
        
        if len(self.BOT_TOKEN) < 40:
            errors.append("BOT_TOKEN выглядит некорректно")
        
        # Проверка Admin ID
        if self.ADMIN_ID == 123456789:
            logger.warning("⚠️ ADMIN_ID не изменен с значения по умолчанию")
        
        # Проверка лимитов
        if not (16 <= self.MIN_AGE <= self.MAX_AGE <= 120):
            errors.append("Некорректные ограничения возраста")
        
        if errors:
            for error in errors:
                logger.error(f"❌ {error}")
            return False
        
        logger.info("✅ Конфигурация прошла валидацию")
        return True
    
    def get_database_url(self) -> str:
        """Получить URL базы данных"""
        return f"sqlite:///{self.DATABASE_PATH}"