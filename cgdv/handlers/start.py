# handlers/start.py
"""
Обработчики команд старта и выбора игры
"""

import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database.database import Database
from keyboards.keyboards import Keyboards
from utils.texts import (
    WELCOME_MESSAGE, SUBSCRIPTION_REQUIRED, SUBSCRIPTION_SUCCESS,
    HELP_MESSAGE
)
from config.settings import Settings

logger = logging.getLogger(__name__)
router = Router()

# Инициализация компонентов
db = Database()
kb = Keyboards()
settings = Settings()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    
    logger.info(f"👤 Пользователь {user_id} ({username}) запустил бота")
    
    # Показываем приветствие и выбор игры
    await message.answer(
        WELCOME_MESSAGE,
        reply_markup=kb.game_selection()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help"""
    await message.answer(HELP_MESSAGE)

@router.callback_query(F.data.startswith("game_"))
async def select_game(callback: CallbackQuery, bot: Bot):
    """Выбор игры"""
    game = callback.data.split("_")[1]  # dota или cs
    user_id = callback.from_user.id
    username = callback.from_user.username
    
    logger.info(f"🎮 Пользователь {user_id} выбрал игру: {game}")
    
    # Проверяем подписку на канал
    channel_id = settings.get_channel_id(game)
    
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        
        # Проверяем статус подписки
        if member.status in ['member', 'administrator', 'creator']:
            # Пользователь подписан
            await handle_subscription_success(callback, game)
        else:
            # Пользователь не подписан
            await request_subscription(callback, game, channel_id)
    
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        # Если не можем проверить подписку, пропускаем проверку
        await handle_subscription_success(callback, game)

async def request_subscription(callback: CallbackQuery, game: str, channel_id: str):
    """Запрос подписки на канал"""
    game_name = "Dota 2" if game == "dota" else "CS2"
    
    text = SUBSCRIPTION_REQUIRED.format(channel=channel_id)
    text += f"\n\n🎮 Игра: {game_name}"
    
    # Сохраняем выбранную игру в callback_data
    keyboard = kb.confirm_subscription()
    # Модифицируем callback_data чтобы передать игру
    new_keyboard = []
    for row in keyboard.inline_keyboard:
        new_row = []
        for button in row:
            if button.callback_data == "check_subscription":
                new_button = button.model_copy()
                new_button.callback_data = f"check_subscription_{game}"
                new_row.append(new_button)
            elif button.callback_data == "recheck_subscription":
                new_button = button.model_copy()
                new_button.callback_data = f"recheck_subscription_{game}"
                new_row.append(new_button)
            else:
                new_row.append(button)
        new_keyboard.append(new_row)
    
    from aiogram.types import InlineKeyboardMarkup
    modified_keyboard = InlineKeyboardMarkup(inline_keyboard=new_keyboard)
    
    await callback.message.edit_text(text, reply_markup=modified_keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("check_subscription_"))
async def check_subscription(callback: CallbackQuery, bot: Bot):
    """Проверка подписки"""
    game = callback.data.split("_")[2]  # dota или cs
    user_id = callback.from_user.id
    channel_id = settings.get_channel_id(game)
    
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        
        if member.status in ['member', 'administrator', 'creator']:
            await handle_subscription_success(callback, game)
        else:
            await callback.answer("❌ Вы еще не подписались на канал", show_alert=True)
    
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        await callback.answer("❌ Ошибка проверки подписки", show_alert=True)

@router.callback_query(F.data.startswith("recheck_subscription_"))
async def recheck_subscription(callback: CallbackQuery, bot: Bot):
    """Повторная проверка подписки"""
    await check_subscription(callback, bot)

async def handle_subscription_success(callback: CallbackQuery, game: str):
    """Обработка успешной подписки"""
    user_id = callback.from_user.id
    username = callback.from_user.username
    
    # Создаем или обновляем пользователя в БД
    user = db.get_user(user_id)
    
    if not user:
        success = db.create_user(user_id, username, game)
        if not success:
            await callback.answer("❌ Ошибка создания профиля", show_alert=True)
            return
        user = db.get_user(user_id)
    
    # Обновляем активность
    db.update_last_activity(user_id)
    
    # Проверяем есть ли заполненная анкета
    has_profile = (user and user['name'] is not None)
    
    # Показываем главное меню
    await show_main_menu(callback, has_profile)

@router.callback_query(F.data == "main_menu")
async def show_main_menu_callback(callback: CallbackQuery):
    """Показать главное меню из callback"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        # Если пользователя нет, возвращаем к выбору игры
        await callback.message.edit_text(
            WELCOME_MESSAGE,
            reply_markup=kb.game_selection()
        )
        await callback.answer()
        return
    
    has_profile = (user['name'] is not None)
    await show_main_menu(callback, has_profile)

async def show_main_menu(callback: CallbackQuery, has_profile: bool):
    """Показать главное меню"""
    text = "🏠 Главное меню\n\n"
    
    if has_profile:
        text += "Выберите действие:"
    else:
        text += "Для начала работы создайте анкету:"
    
    await callback.message.edit_text(
        text,
        reply_markup=kb.main_menu(has_profile)
    )
    await callback.answer()

# Команды для админа
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Админ панель"""
    if message.from_user.id != settings.ADMIN_ID:
        await message.answer("❌ У вас нет прав администратора")
        return
    
    stats = db.get_stats()
    
    text = (
        "👑 Админ панель\n\n"
        f"📊 Статистика:\n"
        f"• Всего пользователей: {stats['total_users']}\n"
        f"• Dota 2: {stats['dota_users']}\n"
        f"• CS2: {stats['cs_users']}\n"
        f"• Активных за неделю: {stats['active_users']}\n"
        f"• Матчей: {stats['total_matches']}\n"
        f"• Лайков сегодня: {stats['today_likes']}"
    )
    
    await message.answer(text, reply_markup=kb.admin_menu())

@router.callback_query(F.data.startswith("admin_"))
async def handle_admin_actions(callback: CallbackQuery):
    """Обработка админ действий"""
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    action = callback.data.split("_")[1]
    
    if action == "stats":
        stats = db.get_stats()
        
        text = (
            "📊 Детальная статистика:\n\n"
            f"👥 Всего пользователей: {stats['total_users']}\n"
            f"🎮 Dota 2: {stats['dota_users']}\n"
            f"🔫 CS2: {stats['cs_users']}\n"
            f"🔥 Активных за неделю: {stats['active_users']}\n"
            f"💖 Матчей: {stats['total_matches']}\n"
            f"👍 Лайков сегодня: {stats['today_likes']}\n\n"
            f"📈 Активность: {(stats['active_users'] / max(stats['total_users'], 1) * 100):.1f}%"
        )
        
        await callback.message.edit_text(text, reply_markup=kb.back_to_main())
    
    elif action == "users":
        # Показать последних пользователей
        users = db._execute_query(
            "SELECT telegram_id, username, game, name, created_at FROM users ORDER BY created_at DESC LIMIT 10"
        )
        
        text = "👥 Последние 10 пользователей:\n\n"
        
        for user in users:
            name = user['name'] if user['name'] else "Без анкеты"
            text += f"• {name} (@{user['username'] or 'без username'}) - {user['game']}\n"
        
        await callback.message.edit_text(text, reply_markup=kb.back_to_main())
    
    elif action == "cleanup":
        # Очистка неактивных пользователей (пример)
        from datetime import datetime, timedelta
        
        month_ago = (datetime.now() - timedelta(days=30)).isoformat()
        inactive_count = len(db._execute_query(
            "SELECT id FROM users WHERE last_activity < ?", 
            (month_ago,)
        ))
        
        text = (
            f"🧹 Очистка базы данных\n\n"
            f"Найдено неактивных пользователей (более 30 дней): {inactive_count}\n\n"
            f"🚧 Функция автоочистки в разработке"
        )
        
        await callback.message.edit_text(text, reply_markup=kb.back_to_main())
    
    await callback.answer()