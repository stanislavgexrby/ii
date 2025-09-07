# utils/texts.py
"""
Форматирование текстов и сообщений
"""

from typing import Dict, Any, Optional
from utils.questions import get_keyboard_options

def format_profile_text(user_data: Dict[str, Any], include_contact: bool = False) -> str:
    """
    Форматирование анкеты пользователя
    
    Args:
        user_data: Данные пользователя из БД
        include_contact: Включать ли контактную информацию
    """
    if not user_data.get('profile_data'):
        return "❌ Анкета не заполнена"
    
    profile = user_data['profile_data']
    
    # Основная информация
    text = f"👤 {profile.get('name', 'Без имени')}"
    
    if profile.get('age'):
        text += f", {profile['age']} лет"
    
    text += "\n\n"
    
    # Описание
    if profile.get('bio'):
        text += f"📝 {profile['bio']}\n\n"
    
    # Игры
    if profile.get('games'):
        games_text = _format_games(profile['games'])
        text += f"🎮 Игры: {games_text}\n"
    
    # Уровень игры
    if profile.get('skill_level'):
        skill_text = _format_skill_level(profile['skill_level'])
        text += f"🏆 Уровень: {skill_text}\n"
    
    # Время игры
    if profile.get('play_time'):
        time_text = _format_play_time(profile['play_time'])
        text += f"⏰ Играет: {time_text}\n"
    
    # Контактная информация
    if include_contact and user_data.get('username'):
        text += f"\n💬 Telegram: @{user_data['username']}"
    
    return text

def _format_games(games_value: str) -> str:
    """Форматирование игр"""
    games_map = {
        "dota2": "🎮 Dota 2",
        "cs2": "🔫 CS2",
        "both": "🎮 Dota 2, 🔫 CS2",
        "other": "🎲 Другие игры"
    }
    return games_map.get(games_value, games_value)

def _format_skill_level(skill: str) -> str:
    """Форматирование уровня игры"""
    skill_map = {
        "beginner": "🟢 Новичок",
        "casual": "🟡 Любитель",
        "advanced": "🟠 Продвинутый", 
        "pro": "🔴 Профессиональный"
    }
    return skill_map.get(skill, skill)

def _format_play_time(time: str) -> str:
    """Форматирование времени игры"""
    time_map = {
        "morning": "🌅 Утром",
        "day": "☀️ Днем",
        "evening": "🌆 Вечером",
        "night": "🌙 Ночью",
        "flexible": "🕐 В любое время"
    }
    return time_map.get(time, time)

def format_match_notification(user_data: Dict[str, Any]) -> str:
    """Форматирование уведомления о матче"""
    name = "Кто-то"
    if user_data.get('profile_data') and user_data['profile_data'].get('name'):
        name = user_data['profile_data']['name']
    
    return (
        f"🎉 У вас новый матч!\n\n"
        f"Пользователь {name} лайкнул вас взаимно!\n"
        f"Теперь вы можете общаться."
    )

def format_matches_list(matches: list) -> str:
    """Форматирование списка матчей"""
    if not matches:
        return (
            "💔 У вас пока нет матчей.\n\n"
            "Продолжайте лайкать анкеты!"
        )
    
    text = "💖 Ваши матчи:\n\n"
    
    for i, match in enumerate(matches, 1):
        profile = match.get('profile_data', {})
        name = profile.get('name', 'Без имени')
        age = profile.get('age', '?')
        
        # Добавляем основную информацию
        text += f"{i}. {name}, {age} лет"
        
        # Добавляем игры если есть
        if profile.get('games'):
            games = _format_games(profile['games'])
            text += f" • {games}"
        
        text += "\n"
        
        # Добавляем username если есть
        if match.get('username'):
            text += f"   💬 @{match['username']}\n"
        
        text += "\n"
    
    text += "💬 Вы можете написать им напрямую в Telegram!"
    return text

def format_stats_message(stats: Dict[str, int]) -> str:
    """Форматирование статистики для админа"""
    return (
        f"📊 Статистика бота:\n\n"
        f"👥 Всего пользователей: {stats.get('total_users', 0)}\n"
        f"🔥 Активных за неделю: {stats.get('active_users', 0)}\n"
        f"💖 Всего матчей: {stats.get('total_matches', 0)}\n"
        f"👍 Лайков сегодня: {stats.get('today_likes', 0)}"
    )

# Константы для сообщений
WELCOME_MESSAGE = (
    "🎮 Добро пожаловать в GameMatch!\n\n"
    "Бот для знакомств геймеров Dota 2 и CS2.\n"
    "Создайте анкету и найдите единомышленников!"
)

WELCOME_BACK_MESSAGE = "🎮 С возвращением, {name}!"

PROFILE_CREATED_MESSAGE = (
    "✅ Отлично! Ваша анкета создана.\n"
    "Теперь вы можете искать единомышленников!"
)

PROFILE_UPDATED_MESSAGE = (
    "✅ Ваша анкета обновлена!\n"
    "Изменения сохранены."
)

NO_MATCHES_MESSAGE = (
    "😔 Пока нет новых анкет для просмотра.\n"
    "Попробуйте позже!"
)

LIKE_SENT_MESSAGE = (
    "💖 Лайк отправлен!\n\n"
    "Если человек лайкнет вас в ответ - это будет матч!"
)

MATCH_CREATED_MESSAGE = (
    "🎉 ЭТО МАТЧ! 💖\n\n"
    "Вы понравились друг другу!\n"
    "Теперь вы можете общаться."
)

CREATE_PROFILE_FIRST_MESSAGE = (
    "❌ Сначала создайте свою анкету!"
)

PHOTO_REQUIRED_MESSAGE = "❌ Пожалуйста, отправьте фотографию"

UNKNOWN_COMMAND_MESSAGE = "❌ Неизвестная команда"

USE_BUTTONS_MESSAGE = "🎮 Используйте кнопки для навигации"