# handlers/common.py
"""
Общие обработчики: неизвестные команды, ошибки
Этот роутер должен подключаться последним!
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ErrorEvent
from aiogram.fsm.context import FSMContext

from keyboards.keyboards import Keyboards
from utils.texts import UNKNOWN_COMMAND_MESSAGE, USE_BUTTONS_MESSAGE

logger = logging.getLogger(__name__)
router = Router()

# Инициализация компонентов
kb = Keyboards()

@router.callback_query()
async def handle_unknown_callback(callback: CallbackQuery):
    """
    Обработчик неизвестных callback запросов
    """
    logger.warning(f"Неизвестный callback: {callback.data} от пользователя {callback.from_user.id}")
    
    await callback.answer(
        UNKNOWN_COMMAND_MESSAGE,
        show_alert=True
    )
    
    # Показываем главное меню
    try:
        await callback.message.edit_text(
            "🎮 Вернулись в главное меню",
            reply_markup=kb.main_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка при показе главного меню после неизвестного callback: {e}")

@router.message()
async def handle_unknown_message(message: Message, state: FSMContext):
    """
    Обработчик неизвестных текстовых сообщений
    Срабатывает только если сообщение не обработано другими хендлерами
    """
    # Проверяем, находится ли пользователь в каком-то состоянии FSM
    current_state = await state.get_state()
    
    if current_state:
        # Пользователь в процессе заполнения анкеты или другом диалоге
        # Не мешаем процессу
        logger.info(f"Пользователь {message.from_user.id} в состоянии {current_state}, пропускаем обработку")
        return
    
    # Обычное сообщение вне состояний
    logger.info(f"Неизвестное сообщение от {message.from_user.id}: {message.text}")
    
    await message.answer(
        USE_BUTTONS_MESSAGE,
        reply_markup=kb.main_menu()
    )

@router.error()
async def error_handler(event: ErrorEvent):
    """
    Глобальный обработчик ошибок
    """
    logger.error(f"Критическая ошибка: {event.exception}", exc_info=True)
    
    # Пытаемся отправить сообщение пользователю об ошибке
    try:
        if event.update.message:
            await event.update.message.answer(
                "❌ Произошла ошибка. Попробуйте еще раз.",
                reply_markup=kb.main_menu()
            )
        elif event.update.callback_query:
            await event.update.callback_query.message.answer(
                "❌ Произошла ошибка. Попробуйте еще раз.",
                reply_markup=kb.main_menu()
            )
            await event.update.callback_query.answer()
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение об ошибке: {e}")
    
    return True  # Помечаем ошибку как обработанную

# Дополнительные служебные обработчики

@router.callback_query(F.data == "cancel")
async def handle_cancel(callback: CallbackQuery, state: FSMContext):
    """
    Универсальная отмена текущего действия
    """
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Действие отменено",
        reply_markup=kb.main_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "back")
async def handle_back(callback: CallbackQuery):
    """
    Универсальная кнопка "Назад"
    """
    await callback.message.edit_text(
        "🎮 GameMatch - Главное меню",
        reply_markup=kb.main_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "reload")
async def handle_reload(callback: CallbackQuery):
    """
    Перезагрузка текущего экрана
    """
    await callback.answer("🔄 Обновляем...")
    
    # Показываем главное меню
    await callback.message.edit_text(
        "🎮 GameMatch - Главное меню\n\nВыберите действие:",
        reply_markup=kb.main_menu()
    )

# Обработчики для дебага (только в режиме разработки)

@router.message(F.text == "/debug")
async def debug_info(message: Message):
    """
    Отладочная информация (только для админа)
    """
    from config.settings import Settings
    settings = Settings()
    
    if message.from_user.id != settings.ADMIN_ID:
        return
    
    # Получаем информацию о пользователе
    from database.database import Database
    db = Database()
    
    user = db.get_user(message.from_user.id)
    stats = db.get_stats()
    
    debug_text = (
        f"🔧 Debug Info\n\n"
        f"User ID: {message.from_user.id}\n"
        f"Username: @{message.from_user.username}\n"
        f"Profile exists: {bool(user and user.get('profile_data'))}\n"
        f"Total users: {stats.get('total_users', 0)}\n"
        f"Active users: {stats.get('active_users', 0)}\n"
        f"Bot version: 1.0\n"
        f"Database: {db.db_path}"
    )
    
    await message.answer(debug_text)

@router.message(F.text.startswith("/admin"))
async def admin_commands(message: Message):
    """
    Админские команды
    """
    from config.settings import Settings
    settings = Settings()
    
    if message.from_user.id != settings.ADMIN_ID:
        await message.answer("❌ Доступ запрещен")
        return
    
    command_parts = message.text.split()
    
    if len(command_parts) < 2:
        await message.answer(
            "🔧 Админские команды:\n\n"
            "/admin stats - статистика\n"
            "/admin cleanup - очистка неактивных\n"
            "/admin broadcast <message> - рассылка"
        )
        return
    
    action = command_parts[1].lower()
    
    if action == "stats":
        from utils.texts import format_stats_message
        from database.database import Database
        
        db = Database()
        stats = db.get_stats()
        stats_text = format_stats_message(stats)
        
        await message.answer(stats_text)
    
    elif action == "cleanup":
        from database.database import Database
        
        db = Database()
        cleaned = db.cleanup_inactive_users(30)
        
        await message.answer(f"🧹 Очищено {cleaned} неактивных пользователей")
    
    elif action == "broadcast":
        if len(command_parts) < 3:
            await message.answer("❌ Укажите текст сообщения")
            return
        
        broadcast_text = " ".join(command_parts[2:])
        await message.answer(f"📢 Рассылка: {broadcast_text}\n\n🚧 Функция в разработке")
    
    else:
        await message.answer("❌ Неизвестная админская команда")

# Middleware для логирования активности пользователей

async def log_user_activity(handler, event, data):
    """
    Middleware для логирования активности пользователей
    """
    user_id = None
    
    if hasattr(event, 'from_user') and event.from_user:
        user_id = event.from_user.id
    
    if user_id:
        # Обновляем время последней активности
        from database.database import Database
        db = Database()
        db.update_user(user_id)
    
    return await handler(event, data)

# Экспортируем middleware
router.message.middleware(log_user_activity)
router.callback_query.middleware(log_user_activity)