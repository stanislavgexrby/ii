# utils/texts.py - ВЕРСИЯ С МНОЖЕСТВЕННЫМ ВЫБОРОМ
"""
Форматирование текстов и сообщений
ПОДДЕРЖКА МНОЖЕСТВЕННОГО ВЫБОРА
"""

from typing import Dict, Any, Optional, List

def format_profile_text(user_data: Dict[str, Any], include_contact: bool = False) -> str:
    """
    Форматирование анкеты пользователя с поддержкой множественного выбора
    
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
    
    # Игры (поддержка множественного выбора)
    if profile.get('games'):
        games_text = _format_games_multiselect(profile['games'])
        text += f"🎮 Игры: {games_text}\n"
    
    # Уровень игры
    if profile.get('skill_level'):
        skill_text = _format_skill_level(profile['skill_level'])
        text += f"🏆 Уровень: {skill_text}\n"
    
    # Время игры (поддержка множественного выбора)
    if profile.get('play_time'):
        time_text = _format_play_time_multiselect(profile['play_time'])
        text += f"⏰ Играет: {time_text}\n"
    
    # Цели знакомства (если есть)
    if profile.get('looking_for'):
        goals_text = _format_looking_for_multiselect(profile['looking_for'])
        text += f"🎯 Ищет: {goals_text}\n"
    
    # Контактная информация
    if include_contact and user_data.get('username'):
        text += f"\n💬 Telegram: @{user_data['username']}"
    
    return text

def _format_games_multiselect(games_value) -> str:
    """Форматирование игр с поддержкой множественного выбора"""
    games_map = {
        "dota2": "🎮 Dota 2",
        "cs2": "🔫 CS2/CS:GO",
        "valorant": "🎯 Valorant",
        "lol": "⚔️ League of Legends",
        "apex": "🔺 Apex Legends",
        "overwatch": "🦾 Overwatch 2",
        "pubg": "🪂 PUBG",
        "fortnite": "🏗️ Fortnite",
        "other": "🎲 Другие игры"
    }
    
    # Если это список (множественный выбор)
    if isinstance(games_value, list):
        if not games_value:
            return "Не указано"
        
        formatted_games = []
        for game_key in games_value:
            game_text = games_map.get(game_key, game_key)
            formatted_games.append(game_text)
        
        return _join_list_naturally(formatted_games)
    
    # Если это строка (старый формат, обратная совместимость)
    return games_map.get(games_value, games_value)

def _format_play_time_multiselect(time_value) -> str:
    """Форматирование времени игры с поддержкой множественного выбора"""
    time_map = {
        "early_morning": "🌅 Раннее утро",
        "morning": "☀️ Утром",
        "afternoon": "🌤️ Днем",
        "evening": "🌆 Вечером",
        "night": "🌙 Ночью",
        "late_night": "🌌 Поздно ночью",
        "flexible": "🕐 В любое время"
    }
    
    # Если это список (множественный выбор)
    if isinstance(time_value, list):
        if not time_value:
            return "Не указано"
        
        # Особая обработка для "flexible"
        if "flexible" in time_value:
            return "🕐 В любое время"
        
        formatted_times = []
        for time_key in time_value:
            time_text = time_map.get(time_key, time_key)
            formatted_times.append(time_text)
        
        return _join_list_naturally(formatted_times)
    
    # Если это строка (старый формат, обратная совместимость)
    return time_map.get(time_value, time_value)

def _format_looking_for_multiselect(looking_for_value) -> str:
    """Форматирование целей знакомства"""
    goals_map = {
        "teammate": "👥 Тиммейта",
        "friend": "🤝 Друга",
        "coach": "📚 Тренера",
        "student": "🎓 Ученика",
        "team": "🏆 Команду",
        "relationship": "💕 Отношения"
    }
    
    # Если это список (множественный выбор)
    if isinstance(looking_for_value, list):
        if not looking_for_value:
            return "Не указано"
        
        formatted_goals = []
        for goal_key in looking_for_value:
            goal_text = goals_map.get(goal_key, goal_key)
            formatted_goals.append(goal_text)
        
        return _join_list_naturally(formatted_goals)
    
    # Если это строка (старый формат)
    return goals_map.get(looking_for_value, looking_for_value)

def _format_skill_level(skill: str) -> str:
    """Форматирование уровня игры"""
    skill_map = {
        "beginner": "🟢 Новичок",
        "casual": "🟡 Любитель",
        "advanced": "🟠 Продвинутый", 
        "pro": "🔴 Профессиональный"
    }
    return skill_map.get(skill, skill)

def _join_list_naturally(items: List[str]) -> str:
    """Естественное соединение списка элементов"""
    if len(items) == 0:
        return ""
    elif len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return f"{items[0]} и {items[1]}"
    else:
        return f"{', '.join(items[:-1])} и {items[-1]}"

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
        
        # Добавляем игры если есть (с поддержкой множественного выбора)
        if profile.get('games'):
            games = _format_games_multiselect(profile['games'])
            # Убираем эмодзи для компактности
            games_clean = games.replace('🎮 ', '').replace('🔫 ', '').replace('🎯 ', '').replace('⚔️ ', '').replace('🔺 ', '').replace('🦾 ', '').replace('🪂 ', '').replace('🏗️ ', '').replace('🎲 ', '')
            text += f" • {games_clean}"
        
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
    "Бот для знакомств геймеров Dota 2, CS2 и других игр.\n"
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

# Дополнительные сообщения для множественного выбора
MULTISELECT_INSTRUCTIONS = {
    "games": "💡 Выберите все игры, в которые вы готовы играть",
    "play_time": "💡 Выберите все удобные для вас времена",
    "looking_for": "💡 Выберите все ваши цели знакомства"
}

def get_multiselect_instruction(question_key: str) -> str:
    """Получить инструкцию для множественного выбора"""
    return MULTISELECT_INSTRUCTIONS.get(question_key, "💡 Выберите подходящие варианты")