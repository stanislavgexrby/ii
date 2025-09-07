# keyboards/__init__.py
"""Пакет клавиатур"""

# keyboards/keyboards.py
"""
Все inline клавиатуры бота
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, List
from utils.questions import get_keyboard_options, is_keyboard_question

class Keyboards:
    """Класс для создания клавиатур"""
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Главное меню бота"""
        buttons = [
            [InlineKeyboardButton(text="👤 Моя анкета", callback_data="profile")],
            [InlineKeyboardButton(text="🔍 Смотреть анкеты", callback_data="browse")],
            [InlineKeyboardButton(text="💖 Мои матчи", callback_data="matches")],
            [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def create_profile() -> InlineKeyboardMarkup:
        """Кнопка создания анкеты"""
        buttons = [
            [InlineKeyboardButton(text="🚀 Создать анкету", callback_data="create_profile")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def profile_actions() -> InlineKeyboardMarkup:
        """Действия с собственной анкетой"""
        buttons = [
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_profile")],
            [InlineKeyboardButton(text="🔍 Смотреть анкеты", callback_data="browse")],
            [InlineKeyboardButton(text="🏠 Главная", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def browse_actions(target_user_id: int) -> InlineKeyboardMarkup:
        """Действия при просмотре чужой анкеты"""
        buttons = [
            [
                InlineKeyboardButton(text="👎 Пропустить", callback_data=f"skip_{target_user_id}"),
                InlineKeyboardButton(text="💖 Лайк", callback_data=f"like_{target_user_id}")
            ],
            [InlineKeyboardButton(text="🏠 Главная", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def after_like() -> InlineKeyboardMarkup:
        """Действия после отправки лайка"""
        buttons = [
            [InlineKeyboardButton(text="🔍 Продолжить поиск", callback_data="browse")],
            [InlineKeyboardButton(text="🏠 Главная", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def after_match() -> InlineKeyboardMarkup:
        """Действия после создания матча"""
        buttons = [
            [InlineKeyboardButton(text="💖 Мои матчи", callback_data="matches")],
            [InlineKeyboardButton(text="🔍 Продолжить поиск", callback_data="browse")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def no_matches() -> InlineKeyboardMarkup:
        """Когда нет матчей"""
        buttons = [
            [InlineKeyboardButton(text="🔍 Смотреть анкеты", callback_data="browse")],
            [InlineKeyboardButton(text="🏠 Главная", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def view_matches() -> InlineKeyboardMarkup:
        """Просмотр матчей"""
        buttons = [
            [InlineKeyboardButton(text="🔍 Продолжить поиск", callback_data="browse")],
            [InlineKeyboardButton(text="🏠 Главная", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def settings_menu() -> InlineKeyboardMarkup:
        """Меню настроек"""
        buttons = [
            [InlineKeyboardButton(text="🔕 Уведомления", callback_data="settings_notifications")],
            [InlineKeyboardButton(text="🔒 Приватность", callback_data="settings_privacy")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="settings_stats")],
            [InlineKeyboardButton(text="🏠 Главная", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def admin_menu() -> InlineKeyboardMarkup:
        """Админ меню"""
        buttons = [
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="🧹 Очистка", callback_data="admin_cleanup")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def question_keyboard(question_key: str) -> InlineKeyboardMarkup:
        """
        Создание клавиатуры для вопроса с опциями
        
        Args:
            question_key: Ключ вопроса из PROFILE_QUESTIONS
        """
        if not is_keyboard_question(question_key):
            return None
        
        options = get_keyboard_options(question_key)
        buttons = []
        
        for key, text in options.items():
            button = InlineKeyboardButton(
                text=text, 
                callback_data=f"answer_{question_key}_{key}"
            )
            buttons.append([button])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def back_to_main() -> InlineKeyboardMarkup:
        """Кнопка возврата в главное меню"""
        buttons = [
            [InlineKeyboardButton(text="🏠 Главная", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def confirm_action(action: str, confirm_data: str, cancel_data: str = "main_menu") -> InlineKeyboardMarkup:
        """
        Клавиатура подтверждения действия
        
        Args:
            action: Описание действия
            confirm_data: callback_data для подтверждения
            cancel_data: callback_data для отмены
        """
        buttons = [
            [
                InlineKeyboardButton(text="✅ Да", callback_data=confirm_data),
                InlineKeyboardButton(text="❌ Нет", callback_data=cancel_data)
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

# Вспомогательные функции для быстрого создания клавиатур

def create_keyboard_from_dict(options: Dict[str, str], callback_prefix: str = "") -> InlineKeyboardMarkup:
    """
    Создание клавиатуры из словаря опций
    
    Args:
        options: Словарь {callback_data: text}
        callback_prefix: Префикс для callback_data
    """
    buttons = []
    for callback_data, text in options.items():
        full_callback = f"{callback_prefix}{callback_data}" if callback_prefix else callback_data
        button = InlineKeyboardButton(text=text, callback_data=full_callback)
        buttons.append([button])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def create_keyboard_grid(options: Dict[str, str], columns: int = 2) -> InlineKeyboardMarkup:
    """
    Создание клавиатуры в виде сетки
    
    Args:
        options: Словарь {callback_data: text}
        columns: Количество колонок
    """
    buttons = []
    row = []
    
    for callback_data, text in options.items():
        button = InlineKeyboardButton(text=text, callback_data=callback_data)
        row.append(button)
        
        if len(row) == columns:
            buttons.append(row)
            row = []
    
    # Добавляем оставшиеся кнопки
    if row:
        buttons.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def add_back_button(keyboard: InlineKeyboardMarkup, back_callback: str = "main_menu") -> InlineKeyboardMarkup:
    """
    Добавление кнопки назад к существующей клавиатуре
    
    Args:
        keyboard: Существующая клавиатура
        back_callback: callback_data для кнопки назад
    """
    buttons = keyboard.inline_keyboard.copy()
    back_button = [InlineKeyboardButton(text="🔙 Назад", callback_data=back_callback)]
    buttons.append(back_button)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)