# utils/validators.py
"""
Валидаторы для бота поиска сокомандников
"""

import re
from config.settings import Settings

class Validators:
    """Класс валидаторов"""
    
    def __init__(self):
        self.settings = Settings()
    
    def validate_name(self, name: str) -> tuple[bool, str]:
        """Валидация имени"""
        name = name.strip()
        
        if len(name) < 2:
            return False, "❌ Имя слишком короткое (минимум 2 символа)"
        
        if len(name) > self.settings.MAX_NAME_LENGTH:
            return False, f"❌ Имя слишком длинное (максимум {self.settings.MAX_NAME_LENGTH} символов)"
        
        # Проверяем что есть хотя бы две части (имя и фамилия)
        parts = name.split()
        if len(parts) < 2:
            return False, "❌ Введите имя и фамилию"
        
        # Проверяем что содержит только буквы и пробелы
        if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\s]+$', name):
            return False, "❌ Имя должно содержать только буквы"
        
        return True, ""
    
    def validate_nickname(self, nickname: str) -> tuple[bool, str]:
        """Валидация никнейма"""
        nickname = nickname.strip()
        
        if len(nickname) < 2:
            return False, "❌ Никнейм слишком короткий (минимум 2 символа)"
        
        if len(nickname) > self.settings.MAX_NICKNAME_LENGTH:
            return False, f"❌ Никнейм слишком длинный (максимум {self.settings.MAX_NICKNAME_LENGTH} символов)"
        
        # Проверяем допустимые символы
        if not re.match(r'^[a-zA-Z0-9а-яА-ЯёЁ_\-\.]+$', nickname):
            return False, "❌ Никнейм может содержать только буквы, цифры, _, -, ."
        
        return True, ""
    
    def validate_age(self, age_str: str) -> tuple[bool, str]:
        """Валидация возраста"""
        try:
            age = int(age_str.strip())
        except ValueError:
            return False, "❌ Возраст должен быть числом"
        
        if age < self.settings.MIN_AGE:
            return False, f"❌ Минимальный возраст: {self.settings.MIN_AGE} лет"
        
        if age > self.settings.MAX_AGE:
            return False, f"❌ Максимальный возраст: {self.settings.MAX_AGE} лет"
        
        return True, ""
    
    def validate_additional_info(self, info: str) -> tuple[bool, str]:
        """Валидация дополнительной информации"""
        info = info.strip()
        
        if len(info) > self.settings.MAX_INFO_LENGTH:
            return False, f"❌ Слишком много текста (максимум {self.settings.MAX_INFO_LENGTH} символов)"
        
        return True, ""