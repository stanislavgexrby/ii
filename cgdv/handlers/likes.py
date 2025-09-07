# handlers/likes.py
"""
Обработчики лайков и матчей
"""

import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from database.database import Database
from keyboards.keyboards import Keyboards
from utils.texts import (
    format_profile_text, MATCH_CREATED, NEW_LIKE_NOTIFICATION
)

logger = logging.getLogger(__name__)
router = Router()

# Инициализация компонентов
db = Database()
kb = Keyboards()

@router.callback_query(F.data == "my_likes")
async def show_my_likes(callback: CallbackQuery):
    """Показать лайки от других пользователей"""
    user_id = callback.from_user.id
    
    # Проверяем что у пользователя есть анкета
    user = db.get_user(user_id)
    if not user or not user['name']:
        await callback.answer("❌ Сначала создайте анкету", show_alert=True)
        return
    
    # Получаем пользователей, которые лайкнули меня
    liked_by = db.get_users_who_liked_me(user_id)
    
    if not liked_by:
        text = (
            "❤️ Пока никто не лайкнул вашу анкету\n\n"
            "Попробуйте:\n"
            "• Улучшить свою анкету\n"
            "• Добавить фото\n"
            "• Быть активнее в поиске"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=kb.back_to_main()
        )
        await callback.answer()
        return
    
    # Показываем первого пользователя
    await show_like_profile(callback, liked_by, 0)

async def show_like_profile(callback: CallbackQuery, profiles: list, index: int):
    """Показать профиль пользователя, который лайкнул"""
    if index >= len(profiles):
        # Все лайки просмотрены
        text = (
            "✅ Все лайки просмотрены!\n\n"
            "Зайдите позже, возможно появятся новые."
        )
        
        try:
            await safe_edit_message(
                callback.message,
                text,
                kb.back_to_main()
            )
        except Exception as e:
            logger.error(f"Ошибка показа окончания лайков: {e}")
        
        await callback.answer()
        return
    
    profile = profiles[index]
    profile_text = format_profile_text(profile)
    
    # Добавляем информацию о том, что это лайк
    text = f"❤️ Этот игрок лайкнул вас:\n\n{profile_text}"
    
    # Сохраняем данные в callback_data для навигации
    target_user_id = profile['telegram_id']
    keyboard = kb.like_actions(target_user_id)
    
    try:
        if profile.get('photo_id'):
            # С фото - удаляем старое сообщение и отправляем новое
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=profile['photo_id'],
                caption=text,
                reply_markup=keyboard
            )
        else:
            # Без фото - безопасно редактируем
            await safe_edit_message(
                callback.message,
                text,
                keyboard
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка показа лайка: {e}")
        await callback.answer("❌ Ошибка загрузки анкеты")

@router.callback_query(F.data.startswith("like_back_"))
async def like_back(callback: CallbackQuery, bot: Bot):
    """Лайкнуть в ответ"""
    try:
        target_user_id = int(callback.data.split("_")[2])
    except (ValueError, IndexError):
        logger.error(f"Ошибка парсинга callback_data для like_back: {callback.data}")
        await callback.answer("❌ Ошибка обработки лайка")
        return
    
    from_user_id = callback.from_user.id
    
    # Проверяем не ставили ли мы уже лайк
    existing_like = db._execute_query(
        "SELECT id FROM likes WHERE from_user_id = ? AND to_user_id = ?",
        (from_user_id, target_user_id)
    )
    
    if existing_like:
        await callback.answer("❌ Вы уже лайкнули этого игрока", show_alert=True)
        return
    
    # Добавляем лайк (это точно будет матч, так как другой пользователь уже лайкнул)
    is_match = db.add_like(from_user_id, target_user_id)
    
    if is_match:
        # Получаем данные пользователя для показа контакта
        match_user = db.get_user(target_user_id)
        
        if match_user:
            profile_text = format_profile_text(match_user, show_contact=True)
            text = f"{MATCH_CREATED}\n\n{profile_text}"
        else:
            text = MATCH_CREATED
        
        keyboard = kb.contact_user(match_user.get('username') if match_user else None)
        
        try:
            await safe_edit_message(callback.message, text, keyboard)
        except Exception as e:
            logger.error(f"Ошибка показа матча: {e}")
            await callback.message.answer(text, reply_markup=keyboard)
        
        # Уведомляем другого пользователя
        await notify_about_match(bot, target_user_id, from_user_id)
        
        logger.info(f"💖 Взаимный лайк: {from_user_id} <-> {target_user_id}")
    else:
        # Такого не должно быть, но на всякий случай
        try:
            await safe_edit_message(
                callback.message,
                "❤️ Лайк отправлен!",
                kb.back_to_main()
            )
        except Exception as e:
            logger.error(f"Ошибка показа результата лайка: {e}")
            await callback.message.answer("❤️ Лайк отправлен!", reply_markup=kb.back_to_main())
    
    await callback.answer()

@router.callback_query(F.data.startswith("skip_like_"))
async def skip_like(callback: CallbackQuery):
    """Пропустить лайк"""
    # Получаем следующие лайки
    user_id = callback.from_user.id
    liked_by = db.get_users_who_liked_me(user_id)
    
    if len(liked_by) <= 1:
        # Это был последний лайк
        text = (
            "✅ Все лайки просмотрены!\n\n"
            "Зайдите позже, возможно появятся новые."
        )
        
        try:
            await safe_edit_message(
                callback.message,
                text,
                kb.back_to_main()
            )
        except Exception as e:
            logger.error(f"Ошибка показа окончания лайков: {e}")
    else:
        # Показываем следующий лайк (удаляем текущий из списка)
        await show_like_profile(callback, liked_by[1:], 0)
    
    await callback.answer()

async def safe_edit_message(message, text: str, keyboard=None):
    """Безопасное редактирование сообщения"""
    try:
        if message.photo:
            # Если есть фото - удаляем и отправляем новое
            await message.delete()
            await message.answer(text, reply_markup=keyboard)
        else:
            # Обычное текстовое сообщение
            await message.edit_text(text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка безопасного редактирования в likes: {e}")
        # Fallback - отправляем новое сообщение
        await message.answer(text, reply_markup=keyboard)

async def notify_about_match(bot: Bot, user_id: int, match_user_id: int):
    """Уведомить пользователя о матче"""
    try:
        match_user = db.get_user(match_user_id)
        
        if match_user:
            text = f"🎉 У вас новый матч!\n\n{match_user['name']} лайкнул вас в ответ!"
        else:
            text = "🎉 У вас новый матч!"
        
        await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=kb.back_to_main()
        )
        logger.info(f"📨 Уведомление о матче отправлено {user_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления о матче: {e}")

# Дополнительные функции для работы с матчами

@router.callback_query(F.data == "view_matches")
async def view_matches(callback: CallbackQuery):
    """Посмотреть все матчи"""
    user_id = callback.from_user.id
    
    matches = db.get_matches(user_id)
    
    if not matches:
        text = (
            "💔 У вас пока нет матчей\n\n"
            "Чтобы получить матчи:\n"
            "• Лайкайте анкеты в поиске\n"
            "• Отвечайте на лайки других игроков"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=kb.back_to_main()
        )
        await callback.answer()
        return
    
    # Формируем список матчей
    text = f"💖 Ваши матчи ({len(matches)}):\n\n"
    
    for i, match in enumerate(matches, 1):
        name = match['name']
        username = match.get('username', 'нет username')
        text += f"{i}. {name} (@{username})\n"
    
    text += "\n💬 Вы можете связаться с любым из них!"
    
    await callback.message.edit_text(
        text,
        reply_markup=kb.back_to_main()
    )
    await callback.answer()