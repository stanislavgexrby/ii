# keyboards/keyboards.py - ВЕРСИЯ С МНОЖЕСТВЕННЫМ ВЫБОРОМ
"""
Все inline клавиатуры бота
ПОДДЕРЖКА МНОЖЕСТВЕННОГО ВЫБОРА
"""

import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, List
from utils.questions import (
    get_keyboard_options, is_keyboard_question, is_multiselect_question,
    get_multiselect_limits, get_selection_status_text
)

logger = logging.getLogger(__name__)

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
        Создание клавиатуры для вопроса с опциями (обычный выбор)
        
        Args:
            question_key: Ключ вопроса из PROFILE_QUESTIONS
        """
        logger.info(f"🔘 Создание обычной клавиатуры для вопроса: {question_key}")
        
        if not is_keyboard_question(question_key):
            logger.warning(f"⚠️ Вопрос '{question_key}' не является обычным клавиатурным!")
            return None
        
        options = get_keyboard_options(question_key)
        
        if not options:
            logger.error(f"❌ Нет опций для клавиатуры вопроса '{question_key}'!")
            return None
        
        buttons = []
        
        for key, text in options.items():
            callback_data = f"answer_{question_key}_{key}"
            button = InlineKeyboardButton(
                text=text, 
                callback_data=callback_data
            )
            buttons.append([button])
            logger.info(f"  ➕ Добавлена кнопка: {text} → {callback_data}")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        logger.info(f"✅ Обычная клавиатура для '{question_key}' создана с {len(buttons)} кнопками")
        
        return keyboard
    
    @staticmethod
    def multiselect_keyboard(question_key: str, selected_items: List[str] = None) -> InlineKeyboardMarkup:
        """
        Создание клавиатуры для множественного выбора
        
        Args:
            question_key: Ключ вопроса из PROFILE_QUESTIONS
            selected_items: Список уже выбранных элементов
        """
        if selected_items is None:
            selected_items = []
        
        logger.info(f"🔘 Создание multiselect клавиатуры для '{question_key}', выбрано: {selected_items}")
        
        if not is_multiselect_question(question_key):
            logger.warning(f"⚠️ Вопрос '{question_key}' не является multiselect!")
            return None
        
        options = get_keyboard_options(question_key)
        min_sel, max_sel = get_multiselect_limits(question_key)
        
        if not options:
            logger.error(f"❌ Нет опций для multiselect вопроса '{question_key}'!")
            return None
        
        buttons = []
        
        # Кнопки выбора опций
        for key, text in options.items():
            is_selected = key in selected_items
            
            # Определяем можно ли выбрать/отменить
            can_select = len(selected_items) < max_sel
            can_deselect = len(selected_items) > 0
            
            if is_selected:
                # Выбранная опция - зеленая галочка
                button_text = f"✅ {text}"
                callback_data = f"multiselect_{question_key}_remove_{key}" if can_deselect else f"multiselect_{question_key}_noop_{key}"
            else:
                # Невыбранная опция
                if can_select:
                    button_text = f"❌ {text}"
                    callback_data = f"multiselect_{question_key}_add_{key}"
                else:
                    # Достигнут максимум - серая кнопка
                    button_text = f"⚫ {text}"
                    callback_data = f"multiselect_{question_key}_noop_{key}"
            
            button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
            buttons.append([button])
            
            logger.info(f"  ➕ Опция: {text} → {'выбрана' if is_selected else 'не выбрана'}")
        
        # Разделитель
        buttons.append([InlineKeyboardButton(text="──────────", callback_data=f"multiselect_{question_key}_noop_separator")])
        
        # Кнопка "Готово" (активна только если выбрано достаточно элементов)
        can_finish = len(selected_items) >= min_sel
        
        if can_finish:
            done_button = InlineKeyboardButton(
                text=f"✅ Готово ({len(selected_items)}/{max_sel})",
                callback_data=f"multiselect_{question_key}_done"
            )
        else:
            need_more = min_sel - len(selected_items)
            done_button = InlineKeyboardButton(
                text=f"⚠️ Выберите ещё {need_more}",
                callback_data=f"multiselect_{question_key}_noop_needmore"
            )
        
        buttons.append([done_button])
        
        # Кнопка отмены
        cancel_button = InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=f"multiselect_{question_key}_cancel"
        )
        buttons.append([cancel_button])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        logger.info(f"✅ Multiselect клавиатура для '{question_key}' создана: {len(selected_items)}/{max_sel} выбрано")
        
        return keyboard
    
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

# Функции для обработки multiselect callback данных

def parse_multiselect_callback(callback_data: str) -> tuple[str, str, str]:
    """
    Парсинг callback_data для multiselect
    
    Returns:
        (question_key, action, item_key)
    """
    # Формат: multiselect_question_key_action_item_key
    parts = callback_data.split("_", 3)
    
    if len(parts) < 3:
        logger.error(f"❌ Неверный формат multiselect callback: {callback_data}")
        return "", "", ""
    
    if len(parts) == 3:
        # multiselect_question_key_action (без item_key)
        _, question_key, action = parts
        return question_key, action, ""
    else:
        # multiselect_question_key_action_item_key
        _, question_key, action, item_key = parts
        return question_key, action, item_key

def is_multiselect_callback(callback_data: str) -> bool:
    """Проверка является ли callback multiselect"""
    return callback_data.startswith("multiselect_")

# Функции для отображения статуса выбора

def format_multiselect_message(question_key: str, selected_items: List[str]) -> str:
    """
    Форматирование сообщения с текущим статусом множественного выбора
    """
    from utils.questions import get_question, get_selection_status_text
    
    question = get_question(question_key)
    question_text = question.get('text', 'Выберите опции')
    
    status_text = get_selection_status_text(question_key, selected_items)
    
    return f"{question_text}\n\n{status_text}"