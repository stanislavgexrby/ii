from telegram import (
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from .config import CHANNEL_USERNAME

def create_subscription_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME}")],
        [InlineKeyboardButton("Я подписался ✅", callback_data="check_subscription")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        ["Опрос 1 человека", "Опрос 5 людей"],
        ["Заглушка для улучшения"],
        ["Отмена"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def create_agreement_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        ["Да"],
        ["Нет"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def create_main_menu_admin_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        ["Проверка подписки"],
        ["Удалить польователей"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)