# handlers/profile.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
Обработчики создания и редактирования профилей
ИСПРАВЛЕНА ФУНКЦИЯ send_safe_message
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from database.database import Database
from keyboards.keyboards import Keyboards, is_multiselect_callback, parse_multiselect_callback, format_multiselect_message
from utils.questions import (
    get_question_keys, get_question, validate_answer, 
    process_answer, is_keyboard_question, is_multiselect_question,
    validate_multiselect_complete, format_selected_items
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
    waiting_for_multiselect = State()
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
    
    logger.info(f"📝 Начало {'редактирования' if is_editing else 'создания'} профиля для {callback.from_user.id}")
    logger.info(f"📋 Вопросы: {question_keys}")
    
    # Сохраняем состояние
    await state.update_data(
        current_question_index=0,
        question_keys=question_keys,
        answers={},
        is_editing=is_editing,
        multiselect_selections={},
        last_message_id=None  # НОВОЕ ПОЛЕ для отслеживания сообщений
    )
    
    # Задаем первый вопрос
    await ask_current_question(callback.message, state, from_callback=True)
    await callback.answer()

async def ask_current_question(message: Message, state: FSMContext, from_callback: bool = False):
    """
    Задать текущий вопрос из анкеты
    """
    data = await state.get_data()
    question_keys = data["question_keys"]
    current_index = data["current_question_index"]
    
    logger.info(f"📋 Задаем вопрос {current_index + 1}/{len(question_keys)}")
    
    if current_index >= len(question_keys):
        # Все вопросы заданы, переходим к фото
        await state.set_state(ProfileStates.waiting_for_photo)
        
        await send_safe_message(
            message, 
            "📸 Теперь отправьте ваше фото",
            from_callback=from_callback
        )
        return
    
    # Получаем текущий вопрос
    question_key = question_keys[current_index]
    question = get_question(question_key)
    
    logger.info(f"🎯 Текущий вопрос: {question_key}")
    
    if not question:
        logger.error(f"❌ Вопрос {question_key} не найден в конфигурации!")
        await send_safe_message(
            message,
            f"❌ Ошибка: вопрос '{question_key}' не найден в конфигурации",
            from_callback=from_callback
        )
        return
    
    # Определяем тип вопроса и устанавливаем соответствующее состояние
    if is_multiselect_question(question_key):
        # Множественный выбор
        await state.set_state(ProfileStates.waiting_for_multiselect)
        
        # Инициализируем пустой выбор
        data = await state.get_data()
        multiselect_selections = data.get("multiselect_selections", {})
        if question_key not in multiselect_selections:
            multiselect_selections[question_key] = []
            await state.update_data(multiselect_selections=multiselect_selections)
        
        # Показываем multiselect клавиатуру
        keyboard = kb.multiselect_keyboard(question_key, multiselect_selections[question_key])
        message_text = format_multiselect_message(question_key, multiselect_selections[question_key])
        
        await send_safe_message(
            message,
            message_text,
            keyboard,
            from_callback=from_callback
        )
        
    elif is_keyboard_question(question_key):
        # Обычная клавиатура с одним выбором
        await state.set_state(ProfileStates.waiting_for_input)
        keyboard = kb.question_keyboard(question_key)
        await send_safe_message(
            message,
            question["text"],
            keyboard,
            from_callback=from_callback
        )
    else:
        # Текстовый вопрос
        await state.set_state(ProfileStates.waiting_for_input)
        await send_safe_message(
            message,
            question["text"],
            from_callback=from_callback
        )

async def send_safe_message(message: Message, text: str, keyboard=None, from_callback: bool = False):
    """
    ИСПРАВЛЕННАЯ функция безопасной отправки сообщения
    """
    logger.info(f"📤 Отправляем сообщение: {text[:50]}...")
    
    try:
        if from_callback:
            # Если вызвано из callback - пытаемся редактировать
            logger.info("🔄 Попытка редактирования сообщения из callback")
            try:
                await message.edit_text(text, reply_markup=keyboard)
                logger.info("✅ Сообщение успешно отредактировано")
                return
            except TelegramBadRequest as e:
                logger.warning(f"⚠️ Не удалось отредактировать сообщение: {e}")
                # Если не получилось редактировать - отправляем новое
                pass
        
        # Отправляем новое сообщение
        logger.info("📤 Отправляем новое сообщение")
        new_message = await message.answer(text, reply_markup=keyboard)
        logger.info(f"✅ Новое сообщение отправлено: ID {new_message.message_id}")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка отправки сообщения: {e}")
        # В крайнем случае отправляем простое сообщение без клавиатуры
        try:
            await message.answer(f"❌ Ошибка отображения. {text}")
        except Exception as fallback_error:
            logger.error(f"❌ Даже fallback не сработал: {fallback_error}")

# НОВЫЙ ОБРАБОТЧИК для множественного выбора
@router.callback_query(F.data.func(is_multiselect_callback), ProfileStates.waiting_for_multiselect)
async def process_multiselect_callback(callback: CallbackQuery, state: FSMContext):
    """
    Обработка callback'ов для множественного выбора
    """
    try:
        question_key, action, item_key = parse_multiselect_callback(callback.data)
        
        logger.info(f"🔘 Multiselect action: {question_key} → {action} → {item_key}")
        
        data = await state.get_data()
        multiselect_selections = data.get("multiselect_selections", {})
        current_selection = multiselect_selections.get(question_key, [])
        
        if action == "add":
            # Добавляем элемент в выбор
            if item_key not in current_selection:
                current_selection.append(item_key)
                logger.info(f"➕ Добавлен элемент: {item_key}")
            
        elif action == "remove":
            # Удаляем элемент из выбора
            if item_key in current_selection:
                current_selection.remove(item_key)
                logger.info(f"➖ Удален элемент: {item_key}")
        
        elif action == "done":
            # Завершение выбора
            is_valid, error_message = validate_multiselect_complete(question_key, current_selection)
            
            if not is_valid:
                await callback.answer(error_message, show_alert=True)
                return
            
            # Сохраняем выбор как ответ
            logger.info(f"✅ Завершен выбор для '{question_key}': {current_selection}")
            await save_answer_and_continue(
                callback.message, 
                state, 
                question_key, 
                current_selection,  # Передаем список выбранных элементов
                from_callback=True
            )
            await callback.answer("✅ Выбор сохранен!")
            return
        
        elif action == "cancel":
            # Отмена выбора
            await callback.answer("❌ Выбор отменен")
            await state.clear()
            await callback.message.edit_text(
                "❌ Создание профиля отменено",
                reply_markup=kb.main_menu()
            )
            return
        
        elif action == "noop":
            # Неактивная кнопка
            if item_key == "needmore":
                await callback.answer("⚠️ Выберите больше элементов", show_alert=True)
            elif item_key == "separator":
                await callback.answer()
            else:
                await callback.answer("Максимум выборов достигнут", show_alert=True)
            return
        
        # Обновляем выбор в состоянии
        multiselect_selections[question_key] = current_selection
        await state.update_data(multiselect_selections=multiselect_selections)
        
        # Обновляем клавиатуру
        keyboard = kb.multiselect_keyboard(question_key, current_selection)
        message_text = format_multiselect_message(question_key, current_selection)
        
        try:
            await callback.message.edit_text(message_text, reply_markup=keyboard)
            logger.info("✅ Multiselect клавиатура обновлена")
        except TelegramBadRequest as e:
            logger.warning(f"⚠️ Не удалось обновить multiselect клавиатуру: {e}")
            # Отправляем новое сообщение
            await callback.message.answer(message_text, reply_markup=keyboard)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки multiselect callback: {e}")
        await callback.answer("❌ Ошибка обработки выбора")

# ЗАМЕНИТЕ ФУНКЦИЮ process_keyboard_answer в handlers/profile.py:

@router.callback_query(F.data.startswith("answer_"), ProfileStates.waiting_for_input)
async def process_keyboard_answer(callback: CallbackQuery, state: FSMContext):
    """
    Обработка ответа через обычную клавиатуру (одиночный выбор)
    ИСПРАВЛЕН ПАРСИНГ CALLBACK_DATA
    """
    try:
        # ИСПРАВЛЕННЫЙ ПАРСИНГ callback_data
        callback_text = callback.data
        logger.info(f"🔍 Парсим callback: {callback_text}")
        
        # Убираем префикс "answer_"
        if not callback_text.startswith("answer_"):
            logger.error(f"❌ Неверный префикс callback_data: {callback_text}")
            await callback.answer("❌ Ошибка обработки ответа")
            return
        
        # Получаем "question_key_answer_value"
        remaining = callback_text[7:]  # убираем "answer_"
        logger.info(f"🔍 После удаления префикса: {remaining}")
        
        # Находим ПОСЛЕДНИЙ "_" чтобы правильно разделить
        last_underscore = remaining.rfind("_")
        
        if last_underscore == -1:
            logger.error(f"❌ Не найден разделитель '_' в: {remaining}")
            await callback.answer("❌ Ошибка формата ответа")
            return
        
        question_key = remaining[:last_underscore]
        answer_value = remaining[last_underscore + 1:]
        
        logger.info(f"✅ ИСПРАВЛЕННЫЙ парсинг:")
        logger.info(f"   📋 question_key: '{question_key}'")
        logger.info(f"   💬 answer_value: '{answer_value}'")
        
        # Проверяем что question_key существует
        from utils.questions import get_question
        question = get_question(question_key)
        if not question:
            logger.error(f"❌ Вопрос '{question_key}' не найден после парсинга!")
            await callback.answer(f"❌ Ошибка: неизвестный вопрос '{question_key}'", show_alert=True)
            return
        
        logger.info(f"🔘 Получен ответ через кнопку: {question_key} = {answer_value}")
        
        await save_answer_and_continue(callback.message, state, question_key, answer_value, from_callback=True)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки ответа клавиатуры: {e}")
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
    
    logger.info(f"✏️ Получен текстовый ответ: {question_key} = {message.text}")
    
    await save_answer_and_continue(message, state, question_key, message.text, from_callback=False)

async def save_answer_and_continue(message: Message, state: FSMContext, question_key: str, answer, from_callback: bool = False):
    """
    Сохранить ответ и перейти к следующему вопросу
    """
    logger.info(f"💾 Сохраняем ответ: {question_key} = {answer}")
    
    # Для множественного выбора answer уже список, для остальных - строка
    if isinstance(answer, list):
        # Множественный выбор уже валидирован
        processed_answer = answer
        logger.info(f"✅ Множественный выбор принят: {question_key} = {processed_answer}")
    else:
        # Обычная валидация
        is_valid, error_message = validate_answer(question_key, answer)
        
        if not is_valid:
            logger.warning(f"⚠️ Невалидный ответ: {error_message}")
            await send_safe_message(message, error_message, from_callback=from_callback)
            return
        
        # Обработка ответа
        processed_answer = process_answer(question_key, answer)
        logger.info(f"✅ Ответ обработан: {question_key} = {processed_answer}")
    
    # Сохраняем ответ
    data = await state.get_data()
    answers = data["answers"]
    answers[question_key] = processed_answer
    
    # Переходим к следующему вопросу
    current_index = data["current_question_index"]
    next_index = current_index + 1
    
    logger.info(f"➡️ Переход к вопросу {next_index + 1}")
    
    await state.update_data(
        answers=answers,
        current_question_index=next_index
    )
    
    # Задаем следующий вопрос
    await ask_current_question(message, state, from_callback=from_callback)

@router.message(ProfileStates.waiting_for_photo, F.photo)
async def process_profile_photo(message: Message, state: FSMContext):
    """
    Обработка фото профиля и завершение создания анкеты
    """
    try:
        data = await state.get_data()
        answers = data["answers"]
        is_editing = data.get("is_editing", False)
        
        logger.info(f"📸 Получено фото от пользователя {message.from_user.id}")
        logger.info(f"📋 Финальные ответы: {answers}")
        
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
            
            logger.info(f"✅ Профиль {'обновлен' if is_editing else 'создан'} для пользователя {user_id}")
            
        else:
            await message.answer(
                "❌ Ошибка сохранения профиля. Попробуйте позже.",
                reply_markup=kb.main_menu()
            )
            await state.clear()
    
    except Exception as e:
        logger.error(f"❌ Ошибка обработки фото профиля: {e}")
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
        logger.error(f"❌ Ошибка пропуска фото: {e}")
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