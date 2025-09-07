# handlers/search.py
"""
Обработчики поиска сокомандников
"""

import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.database import Database
from keyboards.keyboards import Keyboards
from utils.texts import (
    format_search_filters, format_profile_text, 
    NO_MORE_PROFILES, LIKE_SENT, MATCH_CREATED,
    NEW_LIKE_NOTIFICATION
)
from config.settings import Settings

logger = logging.getLogger(__name__)
router = Router()

# FSM состояния для поиска
class SearchStates(StatesGroup):
    setting_filters = State()
    browsing_profiles = State()

# Инициализация компонентов
db = Database()
kb = Keyboards()
settings = Settings()

@router.callback_query(F.data == "search_teammates")
async def start_search(callback: CallbackQuery, state: FSMContext):
    """Начать поиск сокомандников"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user or not user['name']:
        await callback.answer("❌ Сначала создайте анкету", show_alert=True)
        return
    
    # Инициализируем фильтры
    await state.set_state(SearchStates.setting_filters)
    await state.update_data(
        user_game=user['game'],
        rating_filter=None,
        position_filter=None,
        current_profiles=[],
        current_index=0
    )
    
    # Показываем экран фильтров
    await show_search_filters(callback, state)

async def show_search_filters(callback: CallbackQuery, state: FSMContext):
    """Показать экран настройки фильтров"""
    data = await state.get_data()
    game = data['user_game']
    rating_filter = data.get('rating_filter')
    position_filter = data.get('position_filter')
    
    text = format_search_filters(rating_filter, position_filter, game)
    
    try:
        await safe_edit_message(
            callback.message,
            text,
            kb.search_filters(game)
        )
    except Exception as e:
        logger.error(f"Ошибка показа фильтров поиска: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "filter_rating", SearchStates.setting_filters)
async def set_rating_filter(callback: CallbackQuery, state: FSMContext):
    """Установить фильтр по рейтингу"""
    data = await state.get_data()
    game = data['user_game']
    
    text = "🏆 Выберите нужный рейтинг:"
    
    try:
        await safe_edit_message(
            callback.message,
            text,
            kb.rating_options(game)
        )
    except Exception as e:
        logger.error(f"Ошибка показа фильтра рейтинга: {e}")
    
    await callback.answer()

@router.callback_query(F.data.startswith("rating_"), SearchStates.setting_filters)
async def save_rating_filter(callback: CallbackQuery, state: FSMContext):
    """Сохранить фильтр по рейтингу"""
    rating = callback.data.split("_")[1]
    
    await state.update_data(rating_filter=rating)
    
    # Возвращаемся к фильтрам
    await show_search_filters(callback, state)

@router.callback_query(F.data == "filter_position", SearchStates.setting_filters)
async def set_position_filter(callback: CallbackQuery, state: FSMContext):
    """Установить фильтр по позиции"""
    data = await state.get_data()
    game = data['user_game']
    
    text = "⚔️ Выберите нужную позицию:"
    
    try:
        await safe_edit_message(
            callback.message,
            text,
            kb.position_options(game, multiselect=False)
        )
    except Exception as e:
        logger.error(f"Ошибка показа фильтра позиции: {e}")
    
    await callback.answer()

@router.callback_query(F.data.startswith("pos_"), SearchStates.setting_filters)
async def save_position_filter(callback: CallbackQuery, state: FSMContext):
    """Сохранить фильтр по позиции"""
    position = callback.data.split("_")[1]
    
    await state.update_data(position_filter=position)
    
    # Возвращаемся к фильтрам
    await show_search_filters(callback, state)

@router.callback_query(F.data == "start_search", SearchStates.setting_filters)
async def begin_browsing(callback: CallbackQuery, state: FSMContext):
    """Начать просмотр анкет"""
    user_id = callback.from_user.id
    data = await state.get_data()
    
    # Получаем анкеты с учетом фильтров
    profiles = db.get_potential_matches(
        user_id=user_id,
        rating_filter=data.get('rating_filter'),
        position_filter=data.get('position_filter'),
        limit=20
    )
    
    if not profiles:
        try:
            await safe_edit_message(
                callback.message,
                NO_MORE_PROFILES,
                kb.no_results()
            )
        except Exception as e:
            logger.error(f"Ошибка показа 'нет профилей': {e}")
        
        await callback.answer()
        return
    
    # Переходим в режим просмотра
    await state.set_state(SearchStates.browsing_profiles)
    await state.update_data(
        current_profiles=profiles,
        current_index=0
    )
    
    # Показываем первую анкету
    await show_current_profile(callback, state)

@router.callback_query(F.data == "continue_search", SearchStates.browsing_profiles)
async def continue_search(callback: CallbackQuery, state: FSMContext):
    """Продолжить поиск (показать следующую анкету)"""
    await show_next_profile(callback, state)

async def show_current_profile(callback: CallbackQuery, state: FSMContext):
    """Показать текущую анкету"""
    data = await state.get_data()
    profiles = data['current_profiles']
    index = data['current_index']
    
    if index >= len(profiles):
        # Анкеты закончились
        await callback.message.edit_text(
            NO_MORE_PROFILES,
            reply_markup=kb.no_results()
        )
        await callback.answer()
        return
    
    profile = profiles[index]
    profile_text = format_profile_text(profile)
    
    # Показываем анкету
    try:
        if profile.get('photo_id'):
            # С фото
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=profile['photo_id'],
                caption=profile_text,
                reply_markup=kb.search_actions(profile['telegram_id'])
            )
        else:
            # Без фото
            await callback.message.edit_text(
                profile_text,
                reply_markup=kb.search_actions(profile['telegram_id'])
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка показа анкеты: {e}")
        await show_next_profile(callback, state)

async def show_next_profile(callback: CallbackQuery, state: FSMContext):
    """Показать следующую анкету"""
    data = await state.get_data()
    current_index = data['current_index']
    
    # Увеличиваем индекс
    await state.update_data(current_index=current_index + 1)
    
    # Показываем следующую анкету
    await show_current_profile(callback, state)

@router.callback_query(F.data.startswith("skip_"))
async def skip_profile(callback: CallbackQuery, state: FSMContext):
    """Пропустить анкету"""
    await show_next_profile(callback, state)

@router.callback_query(F.data.startswith("like_") & ~F.data.startswith("like_back_"))
async def like_profile(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Лайкнуть анкету"""
    try:
        target_user_id = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        logger.error(f"Ошибка парсинга callback_data: {callback.data}")
        await callback.answer("❌ Ошибка обработки лайка")
        return
    
    from_user_id = callback.from_user.id
    
    # Проверяем что не лайкаем сами себя
    if target_user_id == from_user_id:
        await callback.answer("❌ Нельзя лайкнуть самого себя", show_alert=True)
        return
    
    # Добавляем лайк
    is_match = db.add_like(from_user_id, target_user_id)
    
    if is_match:
        # Взаимный лайк - матч!
        await callback.message.edit_text(
            MATCH_CREATED,
            reply_markup=kb.after_match()
        )
        
        # Уведомляем другого пользователя
        await notify_about_match(bot, target_user_id, from_user_id)
        
        logger.info(f"💖 Матч создан: {from_user_id} <-> {target_user_id}")
    else:
        # Обычный лайк
        await callback.message.edit_text(
            LIKE_SENT,
            reply_markup=kb.after_like()
        )
        
        # Уведомляем о лайке
        await notify_about_like(bot, target_user_id)
        
        logger.info(f"👍 Лайк: {from_user_id} -> {target_user_id}")
    
    await callback.answer()

@router.callback_query(F.data == "view_last_match")
async def view_last_match(callback: CallbackQuery):
    """Посмотреть контакт последнего матча"""
    user_id = callback.from_user.id
    
    # Получаем последний матч
    matches = db.get_matches(user_id)
    
    if not matches:
        await callback.answer("❌ Матчи не найдены", show_alert=True)
        return
    
    last_match = matches[0]  # Первый в списке = последний по времени
    
    profile_text = format_profile_text(last_match, show_contact=True)
    
    await callback.message.edit_text(
        f"💖 Ваш матч:\n\n{profile_text}",
        reply_markup=kb.contact_user(last_match.get('username'))
    )
    await callback.answer()

async def notify_about_like(bot: Bot, user_id: int):
    """Уведомить пользователя о лайке"""
    try:
        await bot.send_message(
            chat_id=user_id,
            text=NEW_LIKE_NOTIFICATION,
            reply_markup=kb.back_to_main()
        )
        logger.info(f"📨 Уведомление о лайке отправлено {user_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления о лайке: {e}")

async def notify_about_match(bot: Bot, user_id: int, match_user_id: int):
    """Уведомить пользователя о матче"""
    try:
        match_user = db.get_user(match_user_id)
        
        if match_user:
            text = f"🎉 У вас новый матч!\n\n{match_user['name']} лайкнул вас взаимно!"
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

# Обработчики для состояния просмотра профилей
@router.callback_query(F.data == "main_menu", SearchStates.browsing_profiles)
async def exit_search(callback: CallbackQuery, state: FSMContext):
    """Выйти из поиска в главное меню"""
    await state.clear()
    
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    has_profile = (user and user['name'] is not None)
    
    text = "🏠 Главное меню\n\nВыберите действие:"
    
    await callback.message.edit_text(
        text,
        reply_markup=kb.main_menu(has_profile)
    )
    await callback.answer()

@router.callback_query(F.data == "main_menu", SearchStates.setting_filters)
async def exit_filters(callback: CallbackQuery, state: FSMContext):
    """Выйти из настройки фильтров в главное меню"""
    await exit_search(callback, state)