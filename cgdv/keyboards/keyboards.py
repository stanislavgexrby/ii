# keyboards/keyboards.py
"""
Клавиатуры для бота поиска сокомандников
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, List
from config.settings import Settings

class Keyboards:
    """Класс для создания клавиатур"""
    
    def __init__(self):
        self.settings = Settings()
    
    def game_selection(self) -> InlineKeyboardMarkup:
        """Выбор игры при старте"""
        buttons = [
            [InlineKeyboardButton(text="🎮 Dota 2", callback_data="game_dota")],
            [InlineKeyboardButton(text="🔫 CS2", callback_data="game_cs")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def main_menu(self, has_profile: bool = False) -> InlineKeyboardMarkup:
        """Главное меню"""
        buttons = []
        
        if has_profile:
            buttons.extend([
                [InlineKeyboardButton(text="✏️ Изменить анкету", callback_data="edit_profile")],
                [InlineKeyboardButton(text="🔍 Поиск сокомандника", callback_data="search_teammates")],
                [InlineKeyboardButton(text="❤️ Твои лайки", callback_data="my_likes")],
                [InlineKeyboardButton(text="🗑️ Удалить анкету", callback_data="delete_profile")]
            ])
        else:
            buttons.append([InlineKeyboardButton(text="📝 Создать анкету", callback_data="create_profile")])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def confirm_subscription(self) -> InlineKeyboardMarkup:
        """Подтверждение подписки"""
        buttons = [
            [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_subscription")],
            [InlineKeyboardButton(text="🔄 Проверить снова", callback_data="recheck_subscription")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def rating_options(self, game: str) -> InlineKeyboardMarkup:
        """Опции рейтинга для игры"""
        buttons = []
        options = self.settings.get_rating_options(game)
        
        for key, text in options.items():
            buttons.append([InlineKeyboardButton(text=text, callback_data=f"rating_{key}")])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def position_options(self, game: str, multiselect: bool = False, selected: List[str] = None) -> InlineKeyboardMarkup:
        """Опции позиций для игры"""
        if selected is None:
            selected = []
        
        buttons = []
        options = self.settings.get_position_options(game)
        
        for key, text in options.items():
            if multiselect:
                # Для множественного выбора
                if key in selected:
                    button_text = f"✅ {text}"
                    callback_data = f"pos_remove_{key}"
                else:
                    button_text = f"❌ {text}"
                    callback_data = f"pos_add_{key}"
                buttons.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
            else:
                # Для одиночного выбора
                buttons.append([InlineKeyboardButton(text=text, callback_data=f"pos_{key}")])
        
        if multiselect:
            # Кнопки управления для множественного выбора
            buttons.append([InlineKeyboardButton(text="──────────", callback_data="separator")])
            
            if len(selected) > 0:
                buttons.append([InlineKeyboardButton(text="✅ Готово", callback_data="pos_done")])
            else:
                buttons.append([InlineKeyboardButton(text="⚠️ Выберите позицию", callback_data="pos_need_select")])
            
            buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="pos_cancel")])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def profile_actions(self) -> InlineKeyboardMarkup:
        """Действия с профилем"""
        buttons = [
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def search_filters(self, game: str) -> InlineKeyboardMarkup:
        """Фильтры поиска"""
        buttons = [
            [InlineKeyboardButton(text="🏆 Выбрать рейтинг", callback_data="filter_rating")],
            [InlineKeyboardButton(text="⚔️ Выбрать позицию", callback_data="filter_position")],
            [InlineKeyboardButton(text="🔍 Начать поиск", callback_data="start_search")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def search_actions(self, target_user_id: int) -> InlineKeyboardMarkup:
        """Действия при просмотре анкеты в поиске"""
        buttons = [
            [
                InlineKeyboardButton(text="👎 Пропустить", callback_data=f"skip_{target_user_id}"),
                InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{target_user_id}")
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def like_actions(self, target_user_id: int) -> InlineKeyboardMarkup:
        """Действия с лайком"""
        buttons = [
            [
                InlineKeyboardButton(text="❤️ Лайк в ответ", callback_data=f"like_back_{target_user_id}"),
                InlineKeyboardButton(text="👎 Пропустить", callback_data=f"skip_like_{target_user_id}")
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def contact_user(self, username: str) -> InlineKeyboardMarkup:
        """Связаться с пользователем"""
        buttons = []
        
        if username:
            buttons.append([InlineKeyboardButton(text="💬 Написать", url=f"https://t.me/{username}")])
        
        buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def confirm_delete(self) -> InlineKeyboardMarkup:
        """Подтверждение удаления анкеты"""
        buttons = [
            [
                InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_delete"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def skip_photo(self) -> InlineKeyboardMarkup:
        """Пропустить фото"""
        buttons = [
            [InlineKeyboardButton(text="⏭️ Пропустить фото", callback_data="skip_photo")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_profile")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def after_like(self) -> InlineKeyboardMarkup:
        """После отправки лайка"""
        buttons = [
            [InlineKeyboardButton(text="🔍 Продолжить поиск", callback_data="continue_search")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def after_match(self) -> InlineKeyboardMarkup:
        """После создания матча"""
        buttons = [
            [InlineKeyboardButton(text="💖 Посмотреть контакт", callback_data="view_last_match")],
            [InlineKeyboardButton(text="🔍 Продолжить поиск", callback_data="continue_search")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def no_results(self) -> InlineKeyboardMarkup:
        """Нет результатов"""
        buttons = [
            [InlineKeyboardButton(text="🔍 Изменить фильтры", callback_data="search_teammates")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def admin_menu(self) -> InlineKeyboardMarkup:
        """Админ меню"""
        buttons = [
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
            [InlineKeyboardButton(text="🗑️ Очистка", callback_data="admin_cleanup")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def back_to_main(self) -> InlineKeyboardMarkup:
        """Кнопка назад в главное меню"""
        buttons = [
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def profile_actions(self) -> InlineKeyboardMarkup:
        """Действия с профилем после просмотра"""
        buttons = [
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_profile")],
            [InlineKeyboardButton(text="🔍 Искать игроков", callback_data="search_teammates")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)