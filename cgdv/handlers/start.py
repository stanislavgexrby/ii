import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database.database import Database
from keyboards.keyboards import Keyboards
from utils.texts import WELCOME_MESSAGE, WELCOME_BACK_MESSAGE, USE_BUTTONS_MESSAGE

logger = logging.getLogger(__name__)
router = Router()

# Инициализация компонентов
db = Database()
kb = Keyboards()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    Обработчик команды /start
    """
    user_id = message.from_user.id
    username = message.from_user.username
    
    logger.info(f"👤 Пользователь {user_id} ({username}) запустил бота")
    
    # Получаем или создаем пользователя
    user = db.get_user(user_id)
    
    if not user:
        # Новый пользователь
        success = db.create_user(user_id, username)
        if not success:
            await message.answer("❌ Ошибка при создании профиля. Попробуйте позже.")
            return
        
        # Приветственное сообщение для нового пользователя
        await message.answer(
            WELCOME_MESSAGE,
            reply_markup=kb.create_profile()
        )
    
    elif not user.get('profile_data') or not user['profile_data']:
        # Пользователь есть, но анкета не заполнена
        await message.answer(
            WELCOME_MESSAGE,
            reply_markup=kb.create_profile()
        )
    
    else:
        # Существующий пользователь с анкетой
        name = user['profile_data'].get('name', 'геймер')
        welcome_text = WELCOME_BACK_MESSAGE.format(name=name)
        
        await message.answer(
            welcome_text,
            reply_markup=kb.main_menu()
        )
    
    # Обновляем время последней активности
    db.update_user(user_id, username=username)

@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery):
    """
    Показать главное меню
    """
    try:
        await callback.message.edit_text(
            "🎮 GameMatch - Главное меню\n\n"
            "Выберите действие:",
            reply_markup=kb.main_menu()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка показа главного меню: {e}")
        await callback.answer("❌ Ошибка обновления меню")

@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery):
    """
    Показать меню настроек
    """
    settings_text = (
        "⚙️ Настройки\n\n"
        "Здесь вы можете настроить уведомления, "
        "приватность и посмотреть статистику.\n\n"
        "🚧 Некоторые функции в разработке..."
    )
    
    try:
        await callback.message.edit_text(
            settings_text,
            reply_markup=kb.settings_menu()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка показа настроек: {e}")
        await callback.answer("❌ Ошибка загрузки настроек")

@router.callback_query(F.data.startswith("settings_"))
async def handle_settings(callback: CallbackQuery):
    """
    Обработка настроек
    """
    setting_type = callback.data.split("_")[1]
    
    if setting_type == "notifications":
        text = (
            "🔔 Уведомления\n\n"
            "• О новых матчах: ✅ Включено\n"
            "• О новых лайках: ✅ Включено\n"
            "• Напоминания: ✅ Включено\n\n"
            "🚧 Настройка уведомлений в разработке"
        )
    
    elif setting_type == "privacy":
        text = (
            "🔒 Приватность\n\n"
            "• Показывать онлайн: ✅ Да\n"
            "• Показывать возраст: ✅ Да\n"
            "• Видимость профиля: 👁️ Всем\n\n"
            "🚧 Настройки приватности в разработке"
        )
    
    elif setting_type == "stats":
        # Получаем статистику пользователя
        user_id = callback.from_user.id
        user = db.get_user(user_id)
        
        # Простая статистика
        likes_given = len(db._execute_query(
            "SELECT id FROM likes WHERE from_user_id = ?", 
            (user_id,)
        ))
        
        matches_count = len(db.get_user_matches(user_id))
        
        text = (
            f"📊 Ваша статистика\n\n"
            f"👍 Лайков отправлено: {likes_given}\n"
            f"💖 Матчей: {matches_count}\n"
            f"📅 В боте с: {user['created_at'][:10] if user else 'неизвестно'}\n"
        )
    
    else:
        text = "🚧 Раздел в разработке"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=kb.back_to_main()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка обработки настроек: {e}")
        await callback.answer("❌ Ошибка загрузки настроек")

@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Команда помощи
    """
    help_text = (
        "🎮 GameMatch Bot - Помощь\n\n"
        "📝 Команды:\n"
        "/start - Запуск бота\n"
        "/help - Эта справка\n"
        "/stats - Статистика (только для админа)\n\n"
        "🎯 Как пользоваться:\n"
        "1. Создайте анкету\n"
        "2. Просматривайте анкеты других\n"
        "3. Ставьте лайки\n"
        "4. При взаимном лайке создается матч\n\n"
        "💬 Поддержка: обратитесь к администратору"
    )
    
    await message.answer(help_text, reply_markup=kb.main_menu())

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """
    Статистика для администратора
    """
    from config.settings import Settings
    settings = Settings()
    
    if message.from_user.id != settings.ADMIN_ID:
        await message.answer("❌ Команда доступна только администратору")
        return
    
    try:
        stats = db.get_stats()
        stats_text = (
            f"📊 Статистика бота:\n\n"
            f"👥 Всего пользователей: {stats.get('total_users', 0)}\n"
            f"🔥 Активных за неделю: {stats.get('active_users', 0)}\n"
            f"💖 Всего матчей: {stats.get('total_matches', 0)}\n"
            f"👍 Лайков сегодня: {stats.get('today_likes', 0)}\n\n"
            f"📈 Конверсия в матчи: "
            f"{(stats.get('total_matches', 0) / max(stats.get('total_users', 1), 1) * 100):.1f}%"
        )
        
        await message.answer(stats_text, reply_markup=kb.admin_menu())
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        await message.answer("❌ Ошибка получения статистики")

@router.callback_query(F.data.startswith("admin_"))
async def handle_admin_actions(callback: CallbackQuery):
    """
    Обработка админ действий
    """
    from config.settings import Settings
    settings = Settings()
    
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    action = callback.data.split("_")[1]
    
    if action == "stats":
        # Детальная статистика
        stats = db.get_stats()
        
        # Дополнительные метрики
        total_likes = len(db._execute_query("SELECT id FROM likes"))
        avg_age_result = db._execute_query(
            "SELECT AVG(CAST(JSON_EXTRACT(profile_data, '$.age') AS INTEGER)) as avg_age "
            "FROM users WHERE profile_data IS NOT NULL"
        )
        avg_age = avg_age_result[0]['avg_age'] if avg_age_result and avg_age_result[0]['avg_age'] else 0
        
        detailed_stats = (
            f"📊 Детальная статистика:\n\n"
            f"👥 Всего пользователей: {stats.get('total_users', 0)}\n"
            f"🔥 Активных за неделю: {stats.get('active_users', 0)}\n"
            f"💖 Всего матчей: {stats.get('total_matches', 0)}\n"
            f"👍 Всего лайков: {total_likes}\n"
            f"👍 Лайков сегодня: {stats.get('today_likes', 0)}\n"
            f"🎂 Средний возраст: {avg_age:.1f} лет\n\n"
            f"📈 Метрики:\n"
            f"• Конверсия в матчи: {(stats.get('total_matches', 0) / max(total_likes, 1) * 100):.1f}%\n"
            f"• Активность: {(stats.get('active_users', 0) / max(stats.get('total_users', 1), 1) * 100):.1f}%"
        )
        
        await callback.message.edit_text(detailed_stats, reply_markup=kb.back_to_main())
    
    elif action == "cleanup":
        # Очистка неактивных пользователей
        cleaned = db.cleanup_inactive_users(30)
        
        await callback.message.edit_text(
            f"🧹 Очистка завершена\n\n"
            f"Деактивировано пользователей: {cleaned}\n"
            f"(неактивных более 30 дней)",
            reply_markup=kb.back_to_main()
        )
    
    elif action == "broadcast":
        # Рассылка (заготовка)
        await callback.message.edit_text(
            "📢 Рассылка\n\n"
            "🚧 Функция в разработке\n\n"
            "Планируется:\n"
            "• Рассылка всем пользователям\n"
            "• Рассылка активным пользователям\n"
            "• Рассылка по критериям",
            reply_markup=kb.back_to_main()
        )
    
    await callback.answer()

@router.message()
async def handle_unknown_text(message: Message):
    """
    Обработка неизвестных текстовых сообщений
    """
    # Проверяем, не находится ли пользователь в процессе создания анкеты
    # Если да, то этот обработчик не сработает, так как у других роутеров выше приоритет
    
    await message.answer(
        USE_BUTTONS_MESSAGE,
        reply_markup=kb.main_menu()
    )