# utils/questions.py - ВЕРСИЯ С МНОЖЕСТВЕННЫМ ВЫБОРОМ
"""
Конфигурация вопросов для анкеты
ПОДДЕРЖКА МНОЖЕСТВЕННОГО ВЫБОРА ДЛЯ ИГР И ВРЕМЕНИ
"""

import logging
from typing import Dict, Any, Callable, List

logger = logging.getLogger(__name__)

# ============================================================================
# НАСТРОЙКА ВОПРОСОВ АНКЕТЫ - ПОДДЕРЖКА МНОЖЕСТВЕННОГО ВЫБОРА
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
        "process": lambda x: int(x)
    },
    
    "bio": {
        "text": "📝 Расскажите немного о себе (что любите в играх, как проводите время)",
        "validation": lambda x: len(x.strip()) >= 10 and len(x.strip()) <= 500,
        "error": "❌ Расскажите о себе подробнее (от 10 до 500 символов)"
    },
    
    "games": {
        "text": "🎮 В какие игры вы готовы играть?\n\n💡 Можно выбрать несколько вариантов",
        "type": "multiselect",  # НОВЫЙ ТИП!
        "options": {
            "dota2": "🎮 Dota 2",
            "cs2": "🔫 CS2/CS:GO", 
            "valorant": "🎯 Valorant",
            "lol": "⚔️ League of Legends",
            "apex": "🔺 Apex Legends",
            "overwatch": "🦾 Overwatch 2",
            "pubg": "🪂 PUBG",
            "fortnite": "🏗️ Fortnite",
            "other": "🎲 Другие игры"
        },
        "min_selections": 1,  # Минимум выборов
        "max_selections": 5   # Максимум выборов
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
        "text": "⏰ Когда вы обычно готовы играть?\n\n💡 Можно выбрать несколько вариантов",
        "type": "multiselect",  # НОВЫЙ ТИП!
        "options": {
            "early_morning": "🌅 Раннее утро (6-9)",
            "morning": "☀️ Утром (9-12)",
            "afternoon": "🌤️ Днем (12-18)",
            "evening": "🌆 Вечером (18-22)", 
            "night": "🌙 Ночью (22-2)",
            "late_night": "🌌 Поздно ночью (2-6)",
            "flexible": "🕐 В любое время"
        },
        "min_selections": 1,
        "max_selections": 4
    },
    
    "looking_for": {
        "text": "🎯 Что вы ищете?\n\n💡 Можно выбрать несколько целей",
        "type": "multiselect",
        "options": {
            "teammate": "👥 Тиммейта для игр",
            "friend": "🤝 Друга для общения",
            "coach": "📚 Тренера",
            "student": "🎓 Ученика",
            "team": "🏆 Команду",
            "relationship": "💕 Отношения"
        },
        "min_selections": 1,
        "max_selections": 3
    }
}

# ============================================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ВОПРОСАМИ
# ============================================================================

def get_question_keys() -> List[str]:
    """Получить список ключей вопросов в правильном порядке"""
    keys = list(PROFILE_QUESTIONS.keys())
    logger.info(f"📋 Список вопросов: {keys}")
    return keys

def get_question(key: str) -> Dict[str, Any]:
    """Получить данные вопроса по ключу"""
    question = PROFILE_QUESTIONS.get(key, {})
    
    if not question:
        logger.error(f"❌ Вопрос '{key}' не найден в PROFILE_QUESTIONS!")
        logger.error(f"📋 Доступные вопросы: {list(PROFILE_QUESTIONS.keys())}")
        return {}
    
    logger.info(f"✅ Получен вопрос '{key}': {question.get('text', 'Нет текста')[:50]}...")
    return question

def validate_answer(question_key: str, answer: str) -> tuple[bool, str]:
    """
    Валидация ответа на вопрос
    Возвращает (успех, сообщение об ошибке)
    """
    question = get_question(question_key)
    
    if not question:
        error_msg = f"❌ Неизвестный вопрос: {question_key}"
        logger.error(error_msg)
        return False, error_msg
    
    # Для multiselect вопросов пропускаем валидацию на этом этапе
    # Валидация происходит при завершении выбора
    if question.get('type') == 'multiselect':
        logger.info(f"✅ Пропускаем валидацию для multiselect вопроса '{question_key}'")
        return True, ""
    
    validation_func = question.get('validation')
    if validation_func:
        try:
            if not validation_func(answer):
                error_msg = question.get('error', '❌ Некорректный ответ')
                logger.warning(f"⚠️ Валидация не прошла для '{question_key}': {answer}")
                return False, error_msg
        except Exception as e:
            logger.error(f"❌ Ошибка валидации для '{question_key}': {e}")
            return False, "❌ Ошибка проверки ответа"
    
    logger.info(f"✅ Валидация прошла для '{question_key}': {answer}")
    return True, ""

def validate_multiselect_complete(question_key: str, selected_items: List[str]) -> tuple[bool, str]:
    """
    Валидация завершенного множественного выбора
    """
    question = get_question(question_key)
    
    if not question:
        return False, f"❌ Неизвестный вопрос: {question_key}"
    
    min_selections = question.get('min_selections', 1)
    max_selections = question.get('max_selections', 10)
    
    if len(selected_items) < min_selections:
        return False, f"❌ Выберите минимум {min_selections} вариант(ов)"
    
    if len(selected_items) > max_selections:
        return False, f"❌ Максимум {max_selections} вариант(ов)"
    
    logger.info(f"✅ Множественный выбор для '{question_key}' валиден: {selected_items}")
    return True, ""

def process_answer(question_key: str, answer: str) -> Any:
    """Обработка ответа (например, преобразование типов)"""
    question = get_question(question_key)
    process_func = question.get('process')
    
    if process_func:
        try:
            processed = process_func(answer)
            logger.info(f"🔄 Обработка '{question_key}': {answer} → {processed}")
            return processed
        except Exception as e:
            logger.error(f"❌ Ошибка обработки '{question_key}': {e}")
            return answer
    
    return answer

def is_keyboard_question(question_key: str) -> bool:
    """Проверяет, использует ли вопрос обычную клавиатуру"""
    question = get_question(question_key)
    is_keyboard = question.get('type') == 'keyboard'
    logger.info(f"🔘 Вопрос '{question_key}' {'использует' if is_keyboard else 'не использует'} обычную клавиатуру")
    return is_keyboard

def is_multiselect_question(question_key: str) -> bool:
    """Проверяет, использует ли вопрос множественный выбор"""
    question = get_question(question_key)
    is_multiselect = question.get('type') == 'multiselect'
    logger.info(f"🔘 Вопрос '{question_key}' {'использует' if is_multiselect else 'не использует'} множественный выбор")
    return is_multiselect

def get_keyboard_options(question_key: str) -> Dict[str, str]:
    """Получить опции для клавиатуры"""
    question = get_question(question_key)
    options = question.get('options', {})
    
    if not options and question.get('type') in ['keyboard', 'multiselect']:
        logger.warning(f"⚠️ Вопрос '{question_key}' с клавиатурой не имеет опций!")
    
    logger.info(f"🔘 Опции для '{question_key}': {list(options.keys())}")
    return options

def get_multiselect_limits(question_key: str) -> tuple[int, int]:
    """Получить лимиты множественного выбора"""
    question = get_question(question_key)
    min_sel = question.get('min_selections', 1)
    max_sel = question.get('max_selections', 10)
    
    logger.info(f"📊 Лимиты для '{question_key}': мин={min_sel}, макс={max_sel}")
    return min_sel, max_sel

# ============================================================================
# ПРОВЕРКА КОНФИГУРАЦИИ ПРИ ИМПОРТЕ
# ============================================================================

def validate_questions_config():
    """Проверка конфигурации вопросов при импорте модуля"""
    errors = []
    
    for key, question in PROFILE_QUESTIONS.items():
        # Проверяем обязательные поля
        if 'text' not in question:
            errors.append(f"Вопрос '{key}' не имеет текста")
        
        # Проверяем клавиатурные вопросы
        if question.get('type') in ['keyboard', 'multiselect']:
            if 'options' not in question or not question['options']:
                errors.append(f"Вопрос с клавиатурой '{key}' не имеет опций")
        
        # Проверяем множественный выбор
        if question.get('type') == 'multiselect':
            min_sel = question.get('min_selections', 1)
            max_sel = question.get('max_selections', 10)
            
            if min_sel < 1:
                errors.append(f"Вопрос '{key}': min_selections должно быть >= 1")
            
            if max_sel < min_sel:
                errors.append(f"Вопрос '{key}': max_selections должно быть >= min_selections")
        
        # Проверяем валидацию
        if 'validation' in question and 'error' not in question:
            errors.append(f"Вопрос '{key}' имеет валидацию без сообщения об ошибке")
    
    if errors:
        logger.error("❌ Ошибки в конфигурации вопросов:")
        for error in errors:
            logger.error(f"  - {error}")
    else:
        logger.info("✅ Конфигурация вопросов валидна")
    
    return len(errors) == 0

# Проверяем конфигурацию при импорте
validate_questions_config()

# ============================================================================
# ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С МНОЖЕСТВЕННЫМ ВЫБОРОМ
# ============================================================================

def format_selected_items(question_key: str, selected_keys: List[str]) -> str:
    """Форматирование выбранных элементов для отображения"""
    question = get_question(question_key)
    options = question.get('options', {})
    
    selected_texts = []
    for key in selected_keys:
        text = options.get(key, key)
        selected_texts.append(text)
    
    if len(selected_texts) == 0:
        return "Ничего не выбрано"
    elif len(selected_texts) == 1:
        return selected_texts[0]
    elif len(selected_texts) == 2:
        return f"{selected_texts[0]} и {selected_texts[1]}"
    else:
        return f"{', '.join(selected_texts[:-1])} и {selected_texts[-1]}"

def get_selection_status_text(question_key: str, selected_keys: List[str]) -> str:
    """Получить текст статуса выбора"""
    min_sel, max_sel = get_multiselect_limits(question_key)
    selected_count = len(selected_keys)
    
    status_parts = []
    
    if selected_count == 0:
        status_parts.append("Ничего не выбрано")
    else:
        formatted = format_selected_items(question_key, selected_keys)
        status_parts.append(f"Выбрано: {formatted}")
    
    if selected_count < min_sel:
        need_more = min_sel - selected_count
        status_parts.append(f"⚠️ Выберите ещё {need_more}")
    elif selected_count >= max_sel:
        status_parts.append(f"✅ Максимум достигнут ({max_sel})")
    else:
        can_select = max_sel - selected_count
        status_parts.append(f"✅ Можно выбрать ещё {can_select}")
    
    return "\n".join(status_parts)