# utils/__init__.py
"""Пакет утилит"""

# utils/questions.py
"""
Конфигурация вопросов для анкеты
ЗДЕСЬ ЛЕГКО ИЗМЕНИТЬ ВСЕ ВОПРОСЫ
"""

from typing import Dict, Any, Callable

# ============================================================================
# НАСТРОЙКА ВОПРОСОВ АНКЕТЫ - ИЗМЕНЯЙТЕ ЗДЕСЬ!
# ============================================================================

PROFILE_QUESTIONS: Dict[str, Dict[str, Any]] = {
    "name": {
        "text": "👤 Как вас зовут или какой у вас игровой ник?",
        "validation": lambda x: len(x.strip()) >= 2 and len(x.strip()) <= 50,
        "error": "❌ Имя должно содержать от 2 до 50 символов"
    },
    
    "age": {
        "text": "🎂 Сколько вам лет? (16-99)",
        "validation": lambda x: x.isdigit() and 16 <= int(x) <= 99,
        "error": "❌ Возраст должен быть числом от 16 до 99",
        "process": lambda x: int(x)  # Преобразуем в число
    },
    
    "bio": {
        "text": "📝 Расскажите немного о себе (что любите в играх, как проводите время)",
        "validation": lambda x: len(x.strip()) >= 10 and len(x.strip()) <= 500,
        "error": "❌ Расскажите о себе подробнее (от 10 до 500 символов)"
    },
    
    "games": {
        "text": "🎮 В какие игры вы играете?",
        "type": "keyboard",
        "options": {
            "dota2": "🎮 Dota 2",
            "cs2": "🔫 CS2", 
            "both": "🎯 Обе игры",
            "other": "🎲 Другие игры"
        }
    },
    
    "skill_level": {
        "text": "🏆 Ваш примерный уровень игры?",
        "type": "keyboard", 
        "options": {
            "beginner": "🟢 Новичок",
            "casual": "🟡 Любитель", 
            "advanced": "🟠 Продвинутый",
            "pro": "🔴 Профессиональный"
        }
    },
    
    "play_time": {
        "text": "⏰ Когда обычно играете?",
        "type": "keyboard",
        "options": {
            "morning": "🌅 Утром",
            "day": "☀️ Днем",
            "evening": "🌆 Вечером", 
            "night": "🌙 Ночью",
            "flexible": "🕐 В любое время"
        }
    }
}

# ============================================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ВОПРОСАМИ
# ============================================================================

def get_question_keys() -> list:
    """Получить список ключей вопросов в правильном порядке"""
    return list(PROFILE_QUESTIONS.keys())

def get_question(key: str) -> Dict[str, Any]:
    """Получить данные вопроса по ключу"""
    return PROFILE_QUESTIONS.get(key, {})

def validate_answer(question_key: str, answer: str) -> tuple[bool, str]:
    """
    Валидация ответа на вопрос
    Возвращает (успех, сообщение об ошибке)
    """
    question = get_question(question_key)
    
    if not question:
        return False, "❌ Неизвестный вопрос"
    
    validation_func = question.get('validation')
    if validation_func and not validation_func(answer):
        return False, question.get('error', '❌ Некорректный ответ')
    
    return True, ""

def process_answer(question_key: str, answer: str) -> Any:
    """Обработка ответа (например, преобразование типов)"""
    question = get_question(question_key)
    process_func = question.get('process')
    
    if process_func:
        return process_func(answer)
    
    return answer

def is_keyboard_question(question_key: str) -> bool:
    """Проверяет, использует ли вопрос клавиатуру"""
    question = get_question(question_key)
    return question.get('type') == 'keyboard'

def get_keyboard_options(question_key: str) -> Dict[str, str]:
    """Получить опции для клавиатуры"""
    question = get_question(question_key)
    return question.get('options', {})

# ============================================================================
# ПРИМЕРЫ НОВЫХ ВОПРОСОВ (РАСКОММЕНТИРУЙТЕ И ДОБАВЬТЕ В PROFILE_QUESTIONS)
# ============================================================================

# Примеры дополнительных вопросов, которые можно добавить:

EXAMPLE_QUESTIONS = {
    # Вопрос с валидацией Steam ID
    "steam_id": {
        "text": "🔗 Ваш Steam ID (опционально, для верификации)",
        "validation": lambda x: len(x) == 0 or (len(x) >= 5 and x.isdigit()),
        "error": "❌ Steam ID должен содержать только цифры",
        "optional": True  # Опциональный вопрос
    },
    
    # Вопрос о предпочитаемой роли
    "preferred_role": {
        "text": "🎯 Какую роль предпочитаете?",
        "type": "keyboard",
        "options": {
            "support": "🛡️ Support",
            "carry": "⚔️ Carry",
            "mid": "🔥 Mid", 
            "offlane": "🌲 Offlane",
            "flex": "🎮 Любую"
        }
    },
    
    # Вопрос о целях знакомства
    "looking_for": {
        "text": "🎯 Что ищете?",
        "type": "keyboard",
        "options": {
            "teammate": "👥 Тиммейта",
            "friend": "🤝 Друга",
            "coach": "📚 Тренера",
            "student": "🎓 Ученика",
            "relationship": "💕 Отношения"
        }
    },
    
    # Вопрос о языках
    "languages": {
        "text": "🗣️ На каких языках общаетесь?",
        "type": "keyboard", 
        "options": {
            "ru": "🇷🇺 Русский",
            "en": "🇺🇸 English",
            "both": "🌍 Русский + English",
            "other": "🗺️ Другие"
        }
    }
}