# handlers/profile.py
"""
Обработчики создания и редактирования профилей
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.database import Database
from keyboards.keyboards import Keyboards
from utils.questions import (
    get_question_keys, get_question, validate_answer, 
    process_answer, is_keyboard_question
)
from utils.texts import (
    format_profile_text, PROFILE_CREATED_MESSAGE, 
    PROFILE_UPDATED_MESSAGE, PHOTO_REQUIRED_MESSAGE,
    CREATE_PROFILE_FIRST_MESSAGE
)

logger = logging.getLogger(__name__)
router = Router()

# FSM состояния
class ProfileStates(StatesGroup):
    waiting_for_input = State()
    waiting_for_photo = State()

# Инициализация компонентов
db = Database()
kb = Keyboards()

@router.callback_query(F.data == "profile")
async def show_user_profile(callback: CallbackQuery):
    """
    Показать профиль пользователя
    """
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user or not user.get('profile_data') or not user['profile_data']:
        # Анкета не создана
        await callback.message.edit_text(
            CREATE_PROFILE_FIRST_MESSAGE,
            reply_markup=kb.create_profile()
        )
        await callback.answer()
        return
    
    # Форматируем профиль
    profile_text = format_profile_text(user)
    
    try:
        if user.get("photo_id"):
            # Если есть фото, удаляем старое сообщение и отправляем новое с фото
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=user["photo_id"],
                caption=profile_text,
                reply_markup=kb.profile_actions()
            )
        else:
            # Если фото нет, просто редактируем текст
            await callback.message.edit_text(
                profile_text,
                reply_markup=kb.profile_actions()
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка показа профиля: {e}")
        await callback.answer("❌ Ошибка загрузки профиля")

@router.callback_query(F.data.in_(["create_profile", "edit_profile"]))
async def start_profile_creation(callback: CallbackQuery, state: FSMContext):
    """
    Начать создание или редактирование профиля
    """
    is_editing = callback.data == "edit_profile"
    
    # Получаем список вопросов
    question_keys = get_question_keys()
    
    if not question_keys:
        await callback.message.edit_text(
            "❌ Ошибка конфигурации вопросов",
            reply_markup=kb.back_to_main()
        )
        return
    
    # Сохраняем состояние
    await state.update_data(
        current_question_index=0,
        question_keys=question_keys,
        answers={},
        is_editing=is_editing
    )
    
    # Задаем первый вопрос
    await ask_current_question(callback.message, state)
    await callback.answer()

async def ask_current_question(message: Message, state: FSMContext):
    """
    Задать текущий вопрос из анкеты
    """
    data = await state.get_data()
    question_keys = data["question_keys"]
    current_index = data["current_question_index"]
    
    if current_index >= len(question_keys):
        # Все вопросы заданы, переходим к фото
        await state.set_state(ProfileStates.waiting_for_photo)
        
        try:
            if hasattr(message, 'edit_text'):
                await message.edit_text("📸 Теперь отправьте ваше фото")
            else:
                await message.answer("📸 Теперь отправьте ваше фото")
        except Exception as e:
            logger.error(f"Ошибка запроса фото: {e}")
            await message.answer("📸 Теперь отправьте ваше фото")
        return
    
    # Получаем текущий вопрос
    question_key = question_keys[current_index]
    question = get_question(question_key)
    
    if not question:
        logger.error(f"Вопрос {question_key} не найден")
        await message.answer("❌ Ошибка в конфигурации вопросов")
        return
    
    # Устанавливаем состояние ожидания ввода
    await state.set_state(ProfileStates.waiting_for_input)
    
    # Проверяем тип вопроса
    if is_keyboard_question(question_key):
        # Вопрос с клавиатурой
        keyboard = kb.question_keyboard(question_key)
        try:
            if hasattr(message, 'edit_text'):
                await message.edit_text(question["text"], reply_markup=keyboard)
            else:
                await message.answer(question["text"], reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Ошибка отправки вопроса с клавиатурой: {e}")
            await message.answer(question["text"], reply_markup=keyboard)
    else:
        # Текстовый вопрос
        try:
            if hasattr(message, 'edit_text'):
                await message.edit_text(question["text"])
            else:
                await message.answer(question["text"])
        except Exception as e:
            logger.error(f"Ошибка отправки текстового вопроса: {e}")
            await message.answer(question["text"])

@router.callback_query(F.data.startswith("answer_"), ProfileStates.waiting_for_input)
async def process_keyboard_answer(callback: CallbackQuery, state: FSMContext):
    """
    Обработка ответа через клавиатуру
    """
    try:
        # Парсим callback_data: answer_question_key_answer_value
        parts = callback.data.split("_", 2)
        if len(parts) != 3:
            await callback.answer("❌ Ошибка обработки ответа")
            return
        
        _, question_key, answer_value = parts
        
        await save_answer_and_continue(callback.message, state, question_key, answer_value)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка обработки ответа клавиатуры: {e}")
        await callback.answer("❌ Ошибка обработки ответа")

@router.message(ProfileStates.waiting_for_input)
async def process_text_answer(message: Message, state: FSMContext):
    """
    Обработка текстового ответа
    """
    data = await state.get_data()
    question_keys = data["question_keys"]
    current_index = data["current_question_index"]
    
    if current_index >= len(question_keys):
        await message.answer("❌ Ошибка: неизвестное состояние")
        await state.clear()
        return
    
    question_key = question_keys[current_index]
    await save_answer_and_continue(message, state, question_key, message.text)

async def save_answer_and_continue(message: Message, state: FSMContext, question_key: str, answer: str):
    """
    Сохранить ответ и перейти к следующему вопросу
    """
    # Валидация ответа
    is_valid, error_message = validate_answer(question_key, answer)
    
    if not is_valid:
        await message.answer(error_message)
        return
    
    # Обработка ответа
    processed_answer = process_answer(question_key, answer)
    
    # Сохраняем ответ
    data = await state.get_data()
    answers = data["answers"]
    answers[question_key] = processed_answer
    
    # Переходим к следующему вопросу
    current_index = data["current_question_index"]
    next_index = current_index + 1
    
    await state.update_data(
        answers=answers,
        current_question_index=next_index
    )
    
    # Задаем следующий вопрос
    await ask_current_question(message, state)

@router.message(ProfileStates.waiting_for_photo, F.photo)
async def process_profile_photo(message: Message, state: FSMContext):
    """
    Обработка фото профиля и завершение создания анкеты
    """
    try:
        data = await state.get_data()
        answers = data["answers"]
        is_editing = data.get("is_editing", False)
        
        # Получаем file_id самого большого фото
        photo_id = message.photo[-1].file_id
        
        # Сохраняем профиль в базу данных
        user_id = message.from_user.id
        username = message.from_user.username
        
        success = db.update_user(
            telegram_id=user_id,
            username=username,
            profile_data=answers,
            photo_id=photo_id
        )
        
        if success:
            # Очищаем состояние
            await state.clear()
            
            # Отправляем сообщение об успехе
            success_message = PROFILE_UPDATED_MESSAGE if is_editing else PROFILE_CREATED_MESSAGE
            
            await message.answer(
                success_message,
                reply_markup=kb.main_menu()
            )
            
            logger.info(f"📝 Профиль {'обновлен' if is_editing else 'создан'} для пользователя {user_id}")
            
        else:
            await message.answer(
                "❌ Ошибка сохранения профиля. Попробуйте позже.",
                reply_markup=kb.main_menu()
            )
            await state.clear()
    
    except Exception as e:
        logger.error(f"Ошибка обработки фото профиля: {e}")
        await message.answer(
            "❌ Ошибка обработки фото. Попробуйте еще раз.",
            reply_markup=kb.main_menu()
        )
        await state.clear()

@router.message(ProfileStates.waiting_for_photo)
async def wrong_photo_format(message: Message):
    """
    Обработка неправильного формата вместо фото
    """
    await message.answer(PHOTO_REQUIRED_MESSAGE)

@router.callback_query(F.data == "skip_photo")
async def skip_photo(callback: CallbackQuery, state: FSMContext):
    """
    Пропустить добавление фото (если функция включена)
    """
    try:
        data = await state.get_data()
        answers = data["answers"]
        is_editing = data.get("is_editing", False)
        
        # Сохраняем профиль без фото
        user_id = callback.from_user.id
        username = callback.from_user.username
        
        success = db.update_user(
            telegram_id=user_id,
            username=username,
            profile_data=answers
            # photo_id не передаем
        )
        
        if success:
            await state.clear()
            
            success_message = PROFILE_UPDATED_MESSAGE if is_editing else PROFILE_CREATED_MESSAGE
            
            await callback.message.edit_text(
                success_message + "\n\n⚠️ Анкеты с фото получают больше внимания!",
                reply_markup=kb.main_menu()
            )
            
        else:
            await callback.message.edit_text(
                "❌ Ошибка сохранения профиля. Попробуйте позже.",
                reply_markup=kb.main_menu()
            )
            await state.clear()
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка пропуска фото: {e}")
        await callback.answer("❌ Ошибка сохранения")

# Обработчик отмены создания профиля
@router.callback_query(F.data == "cancel_profile")
async def cancel_profile_creation(callback: CallbackQuery, state: FSMContext):
    """
    Отмена создания/редактирования профиля
    """
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Создание профиля отменено",
        reply_markup=kb.main_menu()
    )
    await callback.answer()