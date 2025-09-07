# handlers/matching.py
"""
Обработчики системы матчинга: просмотр анкет, лайки, матчи
"""

import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from database.database import Database
from keyboards.keyboards import Keyboards
from utils.texts import (
    format_profile_text, format_matches_list, format_match_notification,
    CREATE_PROFILE_FIRST_MESSAGE, NO_MATCHES_MESSAGE, 
    LIKE_SENT_MESSAGE, MATCH_CREATED_MESSAGE
)

logger = logging.getLogger(__name__)
router = Router()

# Инициализация компонентов
db = Database()
kb = Keyboards()

@router.callback_query(F.data == "browse")
async def browse_profiles(callback: CallbackQuery):
    """
    Начать просмотр анкет других пользователей
    """
    user_id = callback.from_user.id
    
    # Проверяем, есть ли у пользователя анкета
    user = db.get_user(user_id)
    
    if not user or not user.get('profile_data') or not user['profile_data']:
        await callback.message.edit_text(
            CREATE_PROFILE_FIRST_MESSAGE,
            reply_markup=kb.create_profile()
        )
        await callback.answer()
        return
    
    # Получаем потенциальные совпадения
    matches = db.get_potential_matches(user_id, limit=1)
    
    if not matches:
        await callback.message.edit_text(
            NO_MATCHES_MESSAGE,
            reply_markup=kb.no_matches()
        )
        await callback.answer()
        return
    
    # Показываем первую найденную анкету
    await show_profile_for_browsing(callback, matches[0])

async def show_profile_for_browsing(callback: CallbackQuery, target_user: dict):
    """
    Показать анкету для просмотра с кнопками лайк/пропустить
    """
    profile_text = format_profile_text(target_user)
    target_user_id = target_user["telegram_id"]
    
    try:
        if target_user.get("photo_id"):
            # Если есть фото, удаляем старое сообщение и отправляем новое
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=target_user["photo_id"],
                caption=profile_text,
                reply_markup=kb.browse_actions(target_user_id)
            )
        else:
            # Без фото
            await callback.message.edit_text(
                profile_text,
                reply_markup=kb.browse_actions(target_user_id)
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка показа анкеты для просмотра: {e}")
        await callback.answer("❌ Ошибка загрузки анкеты")

@router.callback_query(F.data.startswith("like_"))
async def process_like(callback: CallbackQuery):
    """
    Обработка лайка
    """
    try:
        target_user_id = int(callback.data.split("_")[1])
        from_user_id = callback.from_user.id
        
        # Проверяем, что пользователь не лайкает сам себя
        if target_user_id == from_user_id:
            await callback.answer("❌ Нельзя лайкнуть самого себя", show_alert=True)
            return
        
        # Добавляем лайк в базу данных
        is_mutual_like = db.add_like(from_user_id, target_user_id)
        
        if is_mutual_like:
            # Взаимный лайк - создан матч!
            await callback.message.edit_text(
                MATCH_CREATED_MESSAGE,
                reply_markup=kb.after_match()
            )
            
            # Уведомляем другого пользователя о матче
            await notify_about_match(target_user_id, from_user_id, callback.bot)
            
            logger.info(f"💖 Создан матч между {from_user_id} и {target_user_id}")
            
        else:
            # Обычный лайк
            await callback.message.edit_text(
                LIKE_SENT_MESSAGE,
                reply_markup=kb.after_like()
            )
            
            logger.info(f"👍 Лайк от {from_user_id} к {target_user_id}")
        
        await callback.answer()
        
    except ValueError:
        logger.error(f"Ошибка парсинга target_user_id из callback_data: {callback.data}")
        await callback.answer("❌ Ошибка обработки лайка")
    except Exception as e:
        logger.error(f"Ошибка обработки лайка: {e}")
        await callback.answer("❌ Ошибка обработки лайка")

@router.callback_query(F.data.startswith("skip_"))
async def process_skip(callback: CallbackQuery):
    """
    Пропустить анкету - показать следующую
    """
    # Просто вызываем browse_profiles для показа следующей анкеты
    await browse_profiles(callback)

@router.callback_query(F.data == "matches")
async def show_user_matches(callback: CallbackQuery):
    """
    Показать список матчей пользователя
    """
    user_id = callback.from_user.id
    
    # Проверяем, есть ли у пользователя анкета
    user = db.get_user(user_id)
    
    if not user or not user.get('profile_data') or not user['profile_data']:
        await callback.message.edit_text(
            CREATE_PROFILE_FIRST_MESSAGE,
            reply_markup=kb.create_profile()
        )
        await callback.answer()
        return
    
    # Получаем матчи пользователя
    matches = db.get_user_matches(user_id)
    
    # Форматируем список матчей
    matches_text = format_matches_list(matches)
    
    try:
        await callback.message.edit_text(
            matches_text,
            reply_markup=kb.view_matches()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка показа матчей: {e}")
        await callback.answer("❌ Ошибка загрузки матчей")

async def notify_about_match(target_user_id: int, from_user_id: int, bot: Bot):
    """
    Уведомить пользователя о новом матче
    """
    try:
        # Получаем данные пользователя, который поставил лайк
        from_user = db.get_user(from_user_id)
        
        if not from_user:
            logger.warning(f"Пользователь {from_user_id} не найден для уведомления о матче")
            return
        
        # Формируем уведомление
        notification_text = format_match_notification(from_user)
        
        # Отправляем уведомление
        await bot.send_message(
            chat_id=target_user_id,
            text=notification_text,
            reply_markup=kb.view_matches()
        )
        
        logger.info(f"📨 Отправлено уведомление о матче пользователю {target_user_id}")
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления о матче: {e}")
        # Не критичная ошибка, продолжаем работу

@router.callback_query(F.data.startswith("view_match_"))
async def view_specific_match(callback: CallbackQuery):
    """
    Просмотр конкретного матча (детальная информация)
    """
    try:
        match_user_id = int(callback.data.split("_")[2])
        current_user_id = callback.from_user.id
        
        # Получаем данные пользователя-матча
        match_user = db.get_user(match_user_id)
        
        if not match_user:
            await callback.answer("❌ Пользователь не найден")
            return
        
        # Проверяем, что это действительно матч
        user_matches = db.get_user_matches(current_user_id)
        is_match = any(match['telegram_id'] == match_user_id for match in user_matches)
        
        if not is_match:
            await callback.answer("❌ Это не ваш матч")
            return
        
        # Показываем профиль с контактной информацией
        profile_text = format_profile_text(match_user, include_contact=True)
        
        # Кнопки для взаимодействия с матчем
        match_actions = [
            [InlineKeyboardButton(text="💬 Написать", url=f"tg://user?id={match_user_id}")],
            [InlineKeyboardButton(text="🔙 К списку матчей", callback_data="matches")]
        ]
        
        match_keyboard = InlineKeyboardMarkup(inline_keyboard=match_actions)
        
        if match_user.get("photo_id"):
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=match_user["photo_id"],
                caption=profile_text,
                reply_markup=match_keyboard
            )
        else:
            await callback.message.edit_text(
                profile_text,
                reply_markup=match_keyboard
            )
        
        await callback.answer()
        
    except ValueError:
        await callback.answer("❌ Ошибка обработки запроса")
    except Exception as e:
        logger.error(f"Ошибка просмотра матча: {e}")
        await callback.answer("❌ Ошибка загрузки информации о матче")

@router.callback_query(F.data == "who_liked_me")
async def show_who_liked_me(callback: CallbackQuery):
    """
    Показать кто лайкнул пользователя (премиум функция в будущем)
    """
    user_id = callback.from_user.id
    
    # Получаем список тех, кто лайкнул пользователя, но он их еще нет
    liked_by = db._execute_query("""
        SELECT u.* FROM users u
        JOIN likes l ON u.telegram_id = l.from_user_id
        WHERE l.to_user_id = ?
        AND NOT EXISTS (
            SELECT 1 FROM likes l2 
            WHERE l2.from_user_id = ? AND l2.to_user_id = u.telegram_id
        )
        ORDER BY l.created_at DESC
        LIMIT 10
    """, (user_id, user_id))
    
    if not liked_by:
        text = "❤️ Пока никто не лайкнул вашу анкету.\n\nПродолжайте быть активными!"
    else:
        text = f"❤️ Вас лайкнули {len(liked_by)} человек(а):\n\n"
        
        for i, user in enumerate(liked_by, 1):
            # Безопасно получаем данные профиля
            try:
                if user['profile_data']:
                    import json
                    profile_data = json.loads(user['profile_data'])
                    name = profile_data.get('name', 'Аноним')
                    age = profile_data.get('age', '?')
                else:
                    name = 'Аноним'
                    age = '?'
            except:
                name = 'Аноним'
                age = '?'
            
            text += f"{i}. {name}, {age} лет\n"
        
        text += "\n💡 Лайкните их в ответ, чтобы создать матч!"
    
    await callback.message.edit_text(
        text,
        reply_markup=kb.back_to_main()
    )
    await callback.answer()