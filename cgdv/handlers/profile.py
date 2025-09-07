# handlers/profile.py
"""
Обработчики создания и редактирования профиля
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.database import Database
from keyboards.keyboards import Keyboards
from utils.texts import (
    CREATE_PROFILE_MESSAGE, PROFILE_CREATED, PROFILE_UPDATED,
    PROFILE_DELETED, QUESTIONS, format_profile_text
)
from utils.validators import Validators
from config.settings import Settings

logger = logging.getLogger(__name__)
router = Router()

# FSM состояния
class ProfileStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_nickname = State()
    waiting_for_age = State()
    waiting_for_rating = State()
    waiting_for_positions = State()
    waiting_for_additional_info = State()
    waiting_for_photo = State()

# Инициализация компонентов
db = Database()
kb = Keyboards()
validators = Validators()
settings = Settings()

@router.callback_query(F.data.in_(["create_profile", "edit_profile"]))
async def start_profile_creation(callback: CallbackQuery, state: FSMContext):
    """Начать создание/редактирование профиля"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return
    
    is_editing = callback.data == "edit_profile"
    
    # Сохраняем данные в FSM
    await state.update_data(
        user_game=user['game'],
        is_editing=is_editing,
        positions_selected=[]
    )
    
    if is_editing:
        # При редактировании предзаполняем данные
        await state.update_data(
            current_name=user.get('name'),
            current_nickname=user.get('nickname'),
            current_age=user.get('age'),
            current_rating=user.get('rating'),
            current_positions=user.get('positions', []),
            current_additional_info=user.get('additional_info'),
            current_photo_id=user.get('photo_id')
        )
    
    # Начинаем с имени
    await state.set_state(ProfileStates.waiting_for_name)
    
    text = CREATE_PROFILE_MESSAGE if not is_editing else "✏️ Редактирование анкеты\n\n"
    text += QUESTIONS["name"]
    
    await callback.message.edit_text(text)
    await callback.answer()

@router.message(ProfileStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка имени"""
    name = message.text.strip()
    
    # Валидация
    is_valid, error = validators.validate_name(name)
    if not is_valid:
        await message.answer(error)
        return
    
    # Сохраняем и переходим к никнейму
    await state.update_data(name=name)
    await state.set_state(ProfileStates.waiting_for_nickname)
    
    await message.answer(QUESTIONS["nickname"])

@router.message(ProfileStates.waiting_for_nickname)
async def process_nickname(message: Message, state: FSMContext):
    """Обработка никнейма"""
    nickname = message.text.strip()
    
    # Валидация
    is_valid, error = validators.validate_nickname(nickname)
    if not is_valid:
        await message.answer(error)
        return
    
    # Сохраняем и переходим к возрасту
    await state.update_data(nickname=nickname)
    await state.set_state(ProfileStates.waiting_for_age)
    
    await message.answer(QUESTIONS["age"])

@router.message(ProfileStates.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    """Обработка возраста"""
    age_str = message.text.strip()
    
    # Валидация
    is_valid, error = validators.validate_age(age_str)
    if not is_valid:
        await message.answer(error)
        return
    
    age = int(age_str)
    
    # Сохраняем и переходим к рейтингу
    await state.update_data(age=age)
    await state.set_state(ProfileStates.waiting_for_rating)
    
    data = await state.get_data()
    game = data['user_game']
    
    rating_text = "🏆 Выберите ваш рейтинг:"
    if game == "dota":
        rating_text += " (MMR в Dota 2)"
    else:
        rating_text += " (уровень Faceit в CS2)"
    
    await message.answer(rating_text, reply_markup=kb.rating_options(game))

@router.callback_query(F.data.startswith("rating_"), ProfileStates.waiting_for_rating)
async def process_rating(callback: CallbackQuery, state: FSMContext):
    """Обработка рейтинга"""
    rating = callback.data.split("_")[1]
    
    # Сохраняем и переходим к позициям
    await state.update_data(rating=rating, positions_selected=[])
    await state.set_state(ProfileStates.waiting_for_positions)
    
    data = await state.get_data()
    game = data['user_game']
    
    position_text = "⚔️ Выберите ваши позиции/роли:\n\n"
    position_text += "💡 Можно выбрать несколько вариантов"
    
    await callback.message.edit_text(
        position_text,
        reply_markup=kb.position_options(game, multiselect=True, selected=[])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("pos_add_"), ProfileStates.waiting_for_positions)
async def add_position(callback: CallbackQuery, state: FSMContext):
    """Добавить позицию"""
    position = callback.data.split("_")[2]
    
    data = await state.get_data()
    positions_selected = data.get('positions_selected', [])
    game = data['user_game']
    
    # Добавляем позицию если её нет
    if position not in positions_selected:
        positions_selected.append(position)
        await state.update_data(positions_selected=positions_selected)
    
    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=kb.position_options(game, multiselect=True, selected=positions_selected)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("pos_remove_"), ProfileStates.waiting_for_positions)
async def remove_position(callback: CallbackQuery, state: FSMContext):
    """Удалить позицию"""
    position = callback.data.split("_")[2]
    
    data = await state.get_data()
    positions_selected = data.get('positions_selected', [])
    game = data['user_game']
    
    # Удаляем позицию если она есть
    if position in positions_selected:
        positions_selected.remove(position)
        await state.update_data(positions_selected=positions_selected)
    
    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=kb.position_options(game, multiselect=True, selected=positions_selected)
    )
    await callback.answer()

@router.callback_query(F.data == "pos_done", ProfileStates.waiting_for_positions)
async def positions_done(callback: CallbackQuery, state: FSMContext):
    """Завершение выбора позиций"""
    data = await state.get_data()
    positions_selected = data.get('positions_selected', [])
    
    if not positions_selected:
        await callback.answer("❌ Выберите хотя бы одну позицию", show_alert=True)
        return
    
    # Сохраняем и переходим к дополнительной информации
    await state.update_data(positions=positions_selected)
    await state.set_state(ProfileStates.waiting_for_additional_info)
    
    await callback.message.edit_text(QUESTIONS["additional_info"])
    await callback.answer()

@router.callback_query(F.data == "pos_need_select", ProfileStates.waiting_for_positions)
async def positions_need_select(callback: CallbackQuery):
    """Напоминание о выборе позиции"""
    await callback.answer("⚠️ Выберите хотя бы одну позицию", show_alert=True)

@router.callback_query(F.data == "pos_cancel", ProfileStates.waiting_for_positions)
async def cancel_positions(callback: CallbackQuery, state: FSMContext):
    """Отмена выбора позиций"""
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Создание анкеты отменено",
        reply_markup=kb.back_to_main()
    )
    await callback.answer()

@router.message(ProfileStates.waiting_for_additional_info)
async def process_additional_info(message: Message, state: FSMContext):
    """Обработка дополнительной информации"""
    additional_info = message.text.strip()
    
    # Валидация
    is_valid, error = validators.validate_additional_info(additional_info)
    if not is_valid:
        await message.answer(error)
        return
    
    # Сохраняем и переходим к фото
    await state.update_data(additional_info=additional_info)
    await state.set_state(ProfileStates.waiting_for_photo)
    
    await message.answer(
        QUESTIONS["photo"],
        reply_markup=kb.skip_photo()
    )

@router.message(ProfileStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    """Обработка фото"""
    photo_id = message.photo[-1].file_id
    
    # Сохраняем профиль
    await save_profile(message, state, photo_id)

@router.callback_query(F.data == "skip_photo", ProfileStates.waiting_for_photo)
async def skip_photo(callback: CallbackQuery, state: FSMContext):
    """Пропустить фото"""
    # Сохраняем профиль без фото
    await save_profile_callback(callback, state, None)

@router.callback_query(F.data == "cancel_profile", ProfileStates.waiting_for_photo)
async def cancel_profile(callback: CallbackQuery, state: FSMContext):
    """Отменить создание профиля"""
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Создание анкеты отменено",
        reply_markup=kb.back_to_main()
    )
    await callback.answer()

@router.message(ProfileStates.waiting_for_photo)
async def wrong_photo_format(message: Message):
    """Неправильный формат фото"""
    await message.answer(
        "❌ Пожалуйста, отправьте фотографию или нажмите 'Пропустить фото'",
        reply_markup=kb.skip_photo()
    )

async def save_profile(message: Message, state: FSMContext, photo_id: str):
    """Сохранение профиля"""
    data = await state.get_data()
    user_id = message.from_user.id
    
    # Сохраняем в базу данных
    success = db.update_user_profile(
        telegram_id=user_id,
        name=data['name'],
        nickname=data['nickname'],
        age=data['age'],
        rating=data['rating'],
        positions=data['positions'],
        additional_info=data['additional_info'],
        photo_id=photo_id
    )
    
    await state.clear()
    
    if success:
        is_editing = data.get('is_editing', False)
        success_text = PROFILE_UPDATED if is_editing else PROFILE_CREATED
        
        await message.answer(
            success_text,
            reply_markup=kb.back_to_main()
        )
        
        logger.info(f"✅ Профиль {'обновлен' if is_editing else 'создан'} для {user_id}")
    else:
        await message.answer(
            "❌ Ошибка сохранения анкеты. Попробуйте позже.",
            reply_markup=kb.back_to_main()
        )

async def save_profile_callback(callback: CallbackQuery, state: FSMContext, photo_id: str):
    """Сохранение профиля из callback"""
    data = await state.get_data()
    user_id = callback.from_user.id
    
    # Сохраняем в базу данных
    success = db.update_user_profile(
        telegram_id=user_id,
        name=data['name'],
        nickname=data['nickname'],
        age=data['age'],
        rating=data['rating'],
        positions=data['positions'],
        additional_info=data['additional_info'],
        photo_id=photo_id
    )
    
    await state.clear()
    
    if success:
        is_editing = data.get('is_editing', False)
        success_text = PROFILE_UPDATED if is_editing else PROFILE_CREATED
        
        await callback.message.edit_text(
            success_text,
            reply_markup=kb.back_to_main()
        )
        
        logger.info(f"✅ Профиль {'обновлен' if is_editing else 'создан'} для {user_id}")
    else:
        await callback.message.edit_text(
            "❌ Ошибка сохранения анкеты. Попробуйте позже.",
            reply_markup=kb.back_to_main()
        )
    
    await callback.answer()

@router.callback_query(F.data == "delete_profile")
async def confirm_delete_profile(callback: CallbackQuery):
    """Подтверждение удаления профиля"""
    text = (
        "🗑️ Удаление анкеты\n\n"
        "Вы уверены, что хотите удалить свою анкету?\n\n"
        "⚠️ Это действие нельзя отменить. Все ваши лайки и матчи будут удалены."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=kb.confirm_delete()
    )
    await callback.answer()

@router.callback_query(F.data == "confirm_delete")
async def delete_profile(callback: CallbackQuery):
    """Удаление профиля"""
    user_id = callback.from_user.id
    
    success = db.delete_user_profile(user_id)
    
    if success:
        await callback.message.edit_text(
            PROFILE_DELETED,
            reply_markup=kb.back_to_main()
        )
        
        logger.info(f"🗑️ Профиль удален для {user_id}")
    else:
        await callback.message.edit_text(
            "❌ Ошибка удаления анкеты. Попробуйте позже.",
            reply_markup=kb.back_to_main()
        )
    
    await callback.answer()