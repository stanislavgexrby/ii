# utils/texts.py
"""
Тексты для бота поиска сокомандников
"""

from typing import Dict, Any, List
from config.settings import Settings

def format_profile_text(user: Dict[str, Any], show_contact: bool = False) -> str:
    """Форматирование профиля пользователя"""
    settings = Settings()
    
    text = f"👤 {user['name']}\n"
    text += f"🎮 {user['nickname']}\n"
    text += f"🎂 {user['age']} лет\n"
    
    # Рейтинг
    rating_options = settings.get_rating_options(user['game'])
    rating_text = rating_options.get(user['rating'], user['rating'])
    text += f"🏆 {rating_text}\n"
    
    # Позиции
    if user['positions']:
        position_options = settings.get_position_options(user['game'])
        positions_text = []
        for pos in user['positions']:
            pos_text = position_options.get(pos, pos)
            positions_text.append(pos_text)
        text += f"⚔️ {', '.join(positions_text)}\n"
    
    # Дополнительная информация
    if user['additional_info']:
        text += f"\n📝 {user['additional_info']}\n"
    
    # Контакт
    if show_contact and user.get('username'):
        text += f"\n💬 @{user['username']}"
    
    return text

def format_search_filters(rating_filter: str = None, position_filter: str = None, game: str = "dota") -> str:
    """Форматирование текущих фильтров поиска"""
    settings = Settings()
    
    text = "🔍 Фильтры поиска:\n\n"
    
    # Рейтинг
    if rating_filter:
        rating_options = settings.get_rating_options(game)
        rating_text = rating_options.get(rating_filter, rating_filter)
        text += f"🏆 Рейтинг: {rating_text}\n"
    else:
        text += "🏆 Рейтинг: любой\n"
    
    # Позиция
    if position_filter:
        position_options = settings.get_position_options(game)
        position_text = position_options.get(position_filter, position_filter)
        text += f"⚔️ Позиция: {position_text}\n"
    else:
        text += "⚔️ Позиция: любая\n"
    
    text += "\nВыберите фильтры или начните поиск:"
    
    return text

# Константы сообщений
WELCOME_MESSAGE = """
🎮 Добро пожаловать в TeammateBot!

Этот бот поможет вам найти сокомандников для Dota 2 и CS2.

Выберите игру, для которой хотите найти команду:
"""

SUBSCRIPTION_REQUIRED = """
📢 Для использования бота необходимо подписаться на канал {channel}

После подписки нажмите кнопку "Я подписался"
"""

SUBSCRIPTION_SUCCESS = """
✅ Отлично! Подписка подтверждена.

Теперь вы можете пользоваться ботом.
"""

CREATE_PROFILE_MESSAGE = """
📝 Давайте создадим вашу анкету!

Это поможет другим игрокам узнать о вас больше и найти подходящего сокомандника.

Начнем с первого вопроса...
"""

PROFILE_CREATED = """
✅ Анкета успешно создана!

Теперь вы можете искать сокомандников и другие игроки смогут найти вас.
"""

PROFILE_UPDATED = """
✅ Анкета успешно обновлена!

Изменения сохранены.
"""

PROFILE_DELETED = """
🗑️ Анкета успешно удалена!

Другие игроки больше не смогут вас найти. Вы можете создать новую анкету в любое время.
"""

LIKE_SENT = """
❤️ Лайк отправлен!

Если игрок лайкнет вас в ответ, вы сможете увидеть его контакты и начать общение.
"""

MATCH_CREATED = """
🎉 Это матч! 💖

Вы понравились друг другу! Теперь вы можете связаться и начать играть вместе.
"""

NO_MORE_PROFILES = """
😔 Больше анкет с такими фильтрами не найдено.

Попробуйте изменить фильтры поиска или зайти позже.
"""

NEW_LIKE_NOTIFICATION = """
❤️ Кто-то лайкнул вашу анкету!

Зайдите в "Твои лайки", чтобы посмотреть кто это и ответить взаимностью.
"""

HELP_MESSAGE = """
🎮 TeammateBot - Помощь

🔍 Основные функции:
• Создание анкеты игрока
• Поиск сокомандников с фильтрами
• Система лайков и матчей
• Обмен контактами при взаимном лайке

📝 Как пользоваться:
1. Создайте анкету с информацией о себе
2. Используйте поиск с нужными фильтрами
3. Лайкайте понравившихся игроков
4. При взаимном лайке получите контакт для связи

⚙️ Команды:
/start - Начать работу с ботом
/help - Показать эту справку

💬 По вопросам обращайтесь к администратору
"""

# Вопросы для анкеты
QUESTIONS = {
    "name": "👤 Введите ваше имя и фамилию:",
    "nickname": "🎮 Введите ваш игровой никнейм:",
    "age": "🎂 Сколько вам лет? (16-50)",
    "additional_info": "📝 Расскажите немного о себе (необязательно):",
    "photo": "📸 Отправьте ваше фото (или нажмите 'Пропустить'):"
}