# config/settings.py
"""
Настройки бота для поиска сокомандников
"""

import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class Settings:
    """Класс настроек бота"""
    
    def __init__(self):
        # Основные настройки
        self.BOT_TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
        self.ADMIN_ID: int = int(os.getenv("ADMIN_ID", "123456789"))
        
        # Каналы для проверки подписки
        self.DOTA_CHANNEL_ID: str = os.getenv("DOTA_CHANNEL_ID", "@your_dota_channel")
        self.CS_CHANNEL_ID: str = os.getenv("CS_CHANNEL_ID", "@your_cs_channel")
        
        # База данных
        self.DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/teammates.db")
        
        # Лимиты
        self.MAX_NAME_LENGTH: int = int(os.getenv("MAX_NAME_LENGTH", "50"))
        self.MAX_NICKNAME_LENGTH: int = int(os.getenv("MAX_NICKNAME_LENGTH", "30"))
        self.MAX_INFO_LENGTH: int = int(os.getenv("MAX_INFO_LENGTH", "500"))
        self.MIN_AGE: int = int(os.getenv("MIN_AGE", "16"))
        self.MAX_AGE: int = int(os.getenv("MAX_AGE", "50"))
        
        # Рейтинговые диапазоны
        self.DOTA_MMR_RANGES: Dict[str, str] = {
            "herald": "Herald (0-770)",
            "guardian": "Guardian (770-1540)", 
            "crusader": "Crusader (1540-2310)",
            "archon": "Archon (2310-3080)",
            "legend": "Legend (3080-3850)",
            "ancient": "Ancient (3850-4620)",
            "divine": "Divine (4620-5420)",
            "immortal": "Immortal (5420+)"
        }
        
        self.CS_FACEIT_LEVELS: Dict[str, str] = {
            "1": "Уровень 1 (1-500 ELO)",
            "2": "Уровень 2 (501-750 ELO)",
            "3": "Уровень 3 (751-900 ELO)",
            "4": "Уровень 4 (901-1050 ELO)",
            "5": "Уровень 5 (1051-1200 ELO)",
            "6": "Уровень 6 (1201-1350 ELO)",
            "7": "Уровень 7 (1351-1530 ELO)",
            "8": "Уровень 8 (1531-1750 ELO)",
            "9": "Уровень 9 (1751-2000 ELO)",
            "10": "Уровень 10 (2000+ ELO)"
        }
        
        # Позиции в играх
        self.DOTA_POSITIONS: Dict[str, str] = {
            "pos1": "Керри (1 позиция)",
            "pos2": "Мидер (2 позиция)",
            "pos3": "Оффлейнер (3 позиция)",
            "pos4": "Софт саппорт (4 позиция)",
            "pos5": "Хард саппорт (5 позиция)",
            "any": "Любая позиция"
        }
        
        self.CS_POSITIONS: Dict[str, str] = {
            "rifler": "Райфлер",
            "awper": "AWP-ер",
            "support": "Саппорт",
            "entry": "Штурмовик",
            "igl": "Лидер команды (IGL)",
            "any": "Любая роль"
        }
    
    def validate(self) -> bool:
        """Валидация настроек"""
        errors = []
        
        if self.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            errors.append("BOT_TOKEN не установлен")
        
        if len(self.BOT_TOKEN) < 40:
            errors.append("BOT_TOKEN выглядит некорректно")
        
        if self.ADMIN_ID == 123456789:
            logger.warning("⚠️ ADMIN_ID не изменен с значения по умолчанию")
        
        if errors:
            for error in errors:
                logger.error(f"❌ {error}")
            return False
        
        logger.info("✅ Настройки валидны")
        return True
    
    def get_rating_options(self, game: str) -> Dict[str, str]:
        """Получить опции рейтинга для игры"""
        if game == "dota":
            return self.DOTA_MMR_RANGES
        elif game == "cs":
            return self.CS_FACEIT_LEVELS
        return {}
    
    def get_position_options(self, game: str) -> Dict[str, str]:
        """Получить опции позиций для игры"""
        if game == "dota":
            return self.DOTA_POSITIONS
        elif game == "cs":
            return self.CS_POSITIONS
        return {}
    
    def get_channel_id(self, game: str) -> str:
        """Получить ID канала для игры"""
        if game == "dota":
            return self.DOTA_CHANNEL_ID
        elif game == "cs":
            return self.CS_CHANNEL_ID
        return ""