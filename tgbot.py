import os
import logging
import gspread
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler
)
from google.oauth2.service_account import Credentials
from typing import Dict, Any
from config import BOT_TOKEN, SCOPES, SERVICE_ACCOUNT_FILE, SPREADSHEET_ID, CHANNEL_USERNAME, CHANNEL_ID

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

MOOD, REASON = range(2)

(
    MOOD_GOOD, MOOD_NORMAL, MOOD_BAD, 
    TELL_REASON, NEED_HUG, CANCEL
) = (
    'mood_good', 'mood_normal', 'mood_bad', 
    'tell_reason', 'need_hug', 'cancel'
)

# Глобальная переменная для хранения временных данных
user_data: Dict[int, Dict[str, Any]] = {}

# def init_google_sheets():
#     try:
#         creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
#         client = gspread.authorize(creds)
#         spreadsheet = client.open_by_key(SPREADSHEET_ID)

#         try:
#             worksheet = spreadsheet.worksheet("Данные бота")
#         except gspread.WorksheetNotFound:
#             worksheet = spreadsheet.add_worksheet(title="Данные бота", rows="100", cols="8")

#         if not worksheet.get_all_values():
#             headers = [
#                 'Timestamp', 'User ID', 'First Name', 'Last Name', 
#                 'Username', 'Mood', 'Reason', 'Message'
#             ]
#             worksheet.update('A1:H1', [headers])

#             worksheet.format('A1:H1', {
#                 'textFormat': {'bold': True},
#                 # 'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
#             })

#         return worksheet
#     except Exception as e:
#         logger.error(f"Ошибка инициализации Google Sheets: {e}")
#         return None

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, подписан ли пользователь на необходимый канал"""
    try:
        user_id = update.effective_user.id

        # Пытаемся получить информацию о статусе пользователя в канале
        chat_member = await context.bot.get_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id
        )

        # Проверяем, что статус пользователя является одним из разрешенных
        # (creator, administrator, member - это те, кто подписан на канал)
        if chat_member.status in ['creator', 'administrator', 'member']:
            return True
        else:
            return False

    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        return True

# def create_mood_keyboard() -> InlineKeyboardMarkup:
#     keyboard = [
#         [InlineKeyboardButton("Отлично! 😊", callback_data=MOOD_GOOD)],
#         [InlineKeyboardButton("Нормально 🙂", callback_data=MOOD_NORMAL)],
#         [InlineKeyboardButton("Плохо 😔", callback_data=MOOD_BAD)]
#     ]
#     return InlineKeyboardMarkup(keyboard)

# def create_bad_mood_keyboard() -> InlineKeyboardMarkup:
#     keyboard = [
#         [InlineKeyboardButton("Рассказать причину", callback_data=TELL_REASON)],
#         [InlineKeyboardButton("Просто обнять 🤗", callback_data=NEED_HUG)]
#     ]
#     return InlineKeyboardMarkup(keyboard)

def create_subscription_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton("Я подписался ✅", callback_data="check_subscription")]
    ]
    return InlineKeyboardMarkup(keyboard)

# async def save_to_google_sheets(update: Update, mood: str, reason: str = "") -> None:
#     """Сохраняет данные о пользователе и его настроении в Google Таблицу"""
#     try:
#         worksheet = init_google_sheets()
#         if not worksheet:
#             logger.error("Не удалось подключиться к Google Таблицам")
#             return
        
#         user = update.effective_user
#         user_id = user.id
        
#         # Получаем временные данные пользователя
#         user_info = user_data.get(user_id, {})
        
#         # Получаем текст сообщения (если есть)
#         message_text = ""
#         if update.message:
#             message_text = update.message.text
#         elif update.callback_query:
#             message_text = update.callback_query.data
        
#         # Форматируем данные для записи
#         timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         first_name = user.first_name or ""
#         last_name = user.last_name or ""
#         username = f"@{user.username}" if user.username else ""
        
#         # Очищаем текст от лишних пробелов и переносов строк
#         def clean_text(text):
#             if not text:
#                 return ""
#             return " ".join(str(text).split())
        
#         # Подготавливаем данные для записи
#         row_data = [
#             clean_text(timestamp),
#             clean_text(user_id),
#             clean_text(first_name),
#             clean_text(last_name),
#             clean_text(username),
#             clean_text(mood),
#             clean_text(reason),
#             clean_text(message_text)
#         ]
        
#         # Добавляем строку в таблицу
#         worksheet.append_row(row_data)
        
#         # Настраиваем форматирование новой строки
#         last_row = len(worksheet.get_all_values())
#         worksheet.format(f'A{last_row}:H{last_row}', {
#             'textFormat': {'fontSize': 10},
#             'borders': {
#                 'top': {'style': 'SOLID'},
#                 'bottom': {'style': 'SOLID'},
#                 'left': {'style': 'SOLID'},
#                 'right': {'style': 'SOLID'}
#             }
#         })
        
#         # Автоматически调整宽度 столбцов
#         try:
#             worksheet.columns_auto_resize(0, 7)  # A-H columns
#         except:
#             pass  # Игнорируем ошибки авто-调整宽度
        
#         logger.info(f"Данные пользователя {user_id} сохранены в таблицу")
        
#         # Очищаем временные данные пользователя
#         if user_id in user_data:
#             del user_data[user_id]
        
#     except Exception as e:
#         logger.error(f"Ошибка при сохранении в Google Таблицу: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    is_subscribed = await check_subscription(update, context)

    if not is_subscribed:
        await update.message.reply_text(
            'Для использования бота необходимо подписаться на наш канал!\n\n'
            f'Подпишитесь на канал {CHANNEL_USERNAME} и нажмите кнопку "Я подписался"',
            reply_markup=create_subscription_keyboard()
        )
        return

    user_data[user_id] = {}

    await update.message.reply_text(
        'Привет! Я бот, который интересуется твоим настроением.\n'
        'Как у тебя дела?',
        reply_markup=create_mood_keyboard()
    )

# async def check_subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()

#     is_subscribed = await check_subscription(update, context)

#     if is_subscribed:
#         user_id = update.effective_user.id
#         user_data[user_id] = {}

#         await query.edit_message_text(
#             'Спасибо за подписку! Теперь вы можете пользоваться ботом.\n'
#             'Как у вас дела?',
#             reply_markup=create_mood_keyboard()
#         )
#     else:
#         await query.edit_message_text(
#             'Вы еще не подписались на канал!\n\n'
#             f'Пожалуйста, подпишитесь на канал {CHANNEL_USERNAME} и нажмите кнопку "Я подписался"',
#             reply_markup=create_subscription_keyboard()
#         )

# async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()
#     user_id = update.effective_user.id

#     is_subscribed = await check_subscription(update, context)

#     if user_id not in user_data:
#         user_data[user_id] = {}

#     if query.data == MOOD_GOOD:
#         user_data[user_id]['mood'] = "Хорошее"
#         await save_to_google_sheets(update, "Хорошее")
#         await query.edit_message_text(text="Круто! Рад за тебя! 😊\nЧто планируешь делать сегодня?")
#     elif query.data == MOOD_NORMAL:
#         user_data[user_id]['mood'] = "Нормальное"
#         await save_to_google_sheets(update, "Нормальное")
#         await query.edit_message_text(text="Бывает и лучше, но главное - не унывать! 🙂")
#     elif query.data == MOOD_BAD:
#         user_data[user_id]['mood'] = "Плохое"
#         # НЕ сохраняем сразу, ждем выбора дополнительной опции
#         await query.edit_message_text(
#             text="Мне жаль, что у тебя плохое настроение. Хочешь рассказать, что случилось?",
#             reply_markup=create_bad_mood_keyboard()
#         )
#     elif query.data == TELL_REASON:
#         await query.edit_message_text(text="Я готов выслушать. Расскажи, что произошло?")
#         return MOOD  # Переходим в состояние ожидания причины
#     elif query.data == NEED_HUG:
#         user_data[user_id]['mood'] = "Плохое"
#         await save_to_google_sheets(update, "Плохое", "Нужна поддержка")
#         await query.edit_message_text(text="Крепко-крепко обнимаю! 🤗\nВсё обязательно наладится!")
#     elif query.data == "check_subscription":
#         # Обработка кнопки "Я подписался"
#         await check_subscription_handler(update, context)

# async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Обрабатывает текстовые сообщения"""
#     # Проверяем подписку на канал
#     is_subscribed = await check_subscription(update, context)
    
#     if not is_subscribed:
#         # Если пользователь не подписан, просим подписаться
#         await update.message.reply_text(
#             'Для использования бота необходимо подписаться на наш канал!\n\n'
#             f'Подпишитесь на канал {CHANNEL_USERNAME} и нажмите кнопку "Я подписался"',
#             reply_markup=create_subscription_keyboard()
#         )
#         return
    
#     # Если подписан, продолжаем работу
#     text = update.message.text.lower()
#     user_id = update.effective_user.id
    
#     # Инициализируем временные данные, если их нет
#     if user_id not in user_data:
#         user_data[user_id] = {}
    
#     if any(word in text for word in ['привет', 'здравствуй', 'хай']):
#         await update.message.reply_text('И тебе привет! 👋')
#     elif any(phrase in text for phrase in ['как дела', 'как ты', 'настроение']):
#         await update.message.reply_text(
#             'Выбери вариант:',
#             reply_markup=create_mood_keyboard()
#         )
#     elif any(word in text for word in ['хорошо', 'отлично', 'прекрасно']):
#         user_data[user_id]['mood'] = "Хорошее"
#         await save_to_google_sheets(update, "Хорошее")
#         await update.message.reply_text('Это радует! 😊')
#     elif any(word in text for word in ['плохо', 'ужасно', 'грустно']):
#         user_data[user_id]['mood'] = "Плохое"
#         # НЕ сохраняем сразу, показываем кнопки
#         await update.message.reply_text(
#             'Не грусти! Всё наладится! 🌈',
#             reply_markup=create_bad_mood_keyboard()
#         )
#     else:
#         await update.message.reply_text('Пока я умею только спрашивать о настроении 🤖')

# async def reason_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     # Проверяем подписку на канал
#     is_subscribed = await check_subscription(update, context)
    
#     if not is_subscribed:
#         # Если пользователь не подписан, просим подписаться
#         await update.message.reply_text(
#             'Для использования бота необходимо подписаться на наш канал!\n\n'
#             f'Подпишитесь на канал {CHANNEL_USERNAME} и нажмите кнопку "Я подписался"',
#             reply_markup=create_subscription_keyboard()
#         )
#         return ConversationHandler.END
    
#     # Если подписан, продолжаем работу
#     user_id = update.effective_user.id
#     reason = update.message.text
    
#     # Используем сохраненное настроение или устанавливаем по умолчанию
#     mood = user_data.get(user_id, {}).get('mood', 'Плохое')
    
#     await save_to_google_sheets(update, mood, reason)
#     await update.message.reply_text(
#         f"Спасибо, что поделился. Я запомнил: {reason}\n"
#         "Надеюсь, тебе станет лучше! Если хочешь поговорить, я всегда здесь."
#     )
#     return ConversationHandler.END

# async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     user_id = update.effective_user.id
#     if user_id in user_data:
#         del user_data[user_id]

#     await update.message.reply_text('Диалог прерван. Если захочешь поговорить, я всегда здесь!')
#     return ConversationHandler.END

# def main() -> None:
#     worksheet = init_google_sheets()
#     if worksheet:
#         logger.info("Подключение к Google Таблицам установлено")
#     else:
#         logger.warning("Не удалось подключиться к Google Таблицам. Данные не будут сохраняться.")

#     application = Application.builder().token(BOT_TOKEN).build()

#     conv_handler = ConversationHandler(
#         entry_points=[CallbackQueryHandler(button_handler, pattern=f'^{TELL_REASON}$')],
#         states={
#             MOOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, reason_handler)],
#         },
#         fallbacks=[CommandHandler('cancel', cancel)],
#     )

#     application.add_handler(CommandHandler("start", start))
#     application.add_handler(conv_handler)
#     application.add_handler(CallbackQueryHandler(button_handler))
#     application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

#     print("Бот запущен...")
#     application.run_polling()

# if __name__ == "__main__":
#     main()

# Инициализация Google Sheets
def init_google_sheets():
    """Инициализирует подключение к Google Таблицам"""
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.sheet1  # Используем первый лист
        
        # Добавляем заголовки, если лист пустой
        if not worksheet.get_all_values():
            worksheet.append_row([
                'Timestamp', 'User ID', 'First Name', 'Last Name', 
                'Username', 'Mood', 'Reason', 'Message'
            ])
        
        return worksheet
    except Exception as e:
        logger.error(f"Ошибка инициализации Google Sheets: {e}")
        return None

# Функции для создания клавиатур
def create_mood_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с вариантами настроения"""
    keyboard = [
        [InlineKeyboardButton("Отлично! 😊", callback_data=MOOD_GOOD)],
        [InlineKeyboardButton("Нормально 🙂", callback_data=MOOD_NORMAL)],
        [InlineKeyboardButton("Плохо 😔", callback_data=MOOD_BAD)]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_bad_mood_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для плохого настроения"""
    keyboard = [
        [InlineKeyboardButton("Рассказать причину", callback_data=TELL_REASON)],
        [InlineKeyboardButton("Просто обнять 🤗", callback_data=NEED_HUG)]
    ]
    return InlineKeyboardMarkup(keyboard)

# Функция для записи данных в Google Таблицу
async def save_to_google_sheets(update: Update, mood: str, reason: str = "") -> None:
    """Сохраняет данные о пользователе и его настроении в Google Таблицу"""
    try:
        worksheet = init_google_sheets()
        if not worksheet:
            logger.error("Не удалось подключиться к Google Таблицам")
            return
        
        user = update.effective_user
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Получаем текст сообщения (если есть)
        message_text = ""
        if update.message:
            message_text = update.message.text
        elif update.callback_query:
            message_text = update.callback_query.data
        
        # Добавляем строку в таблицу
        worksheet.append_row([
            timestamp,
            user.id,
            user.first_name,
            user.last_name or "",
            f"@{user.username}" if user.username else "",
            mood,
            reason,
            message_text
        ])
        
        logger.info(f"Данные пользователя {user.id} сохранены в таблицу")
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении в Google Таблицу: {e}")

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение с кнопками"""
    await update.message.reply_text(
        'Привет! Я бот, который интересуется твоим настроением.\n'
        'Как у тебя дела?',
        reply_markup=create_mood_keyboard()
    )

# Обработчик нажатий на кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатия на инлайн-кнопки"""
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие кнопки
    
    # Обрабатываем разные варианты ответов
    if query.data == MOOD_GOOD:
        await save_to_google_sheets(update, "Хорошее")
        await query.edit_message_text(text="Круто! Рад за тебя! 😊\nЧто планируешь делать сегодня?")
    elif query.data == MOOD_NORMAL:
        await save_to_google_sheets(update, "Нормальное")
        await query.edit_message_text(text="Бывает и лучше, но главное - не унывать! 🙂")
    elif query.data == MOOD_BAD:
        await save_to_google_sheets(update, "Плохое")
        await query.edit_message_text(
            text="Мне жаль, что у тебя плохое настроение. Хочешь рассказать, что случилось?",
            reply_markup=create_bad_mood_keyboard()
        )
    elif query.data == TELL_REASON:
        await query.edit_message_text(text="Я готов выслушать. Расскажи, что произошло?")
        return MOOD  # Переходим в состояние ожидания причины
    elif query.data == NEED_HUG:
        await query.edit_message_text(text="Крепко-крепко обнимаю! 🤗\nВсё обязательно наладится!")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает текстовые сообщения"""
    text = update.message.text.lower()
    
    if any(word in text for word in ['привет', 'здравствуй', 'хай']):
        await update.message.reply_text('И тебе привет! 👋')
    elif any(phrase in text for phrase in ['как дела', 'как ты', 'настроение']):
        await update.message.reply_text(
            'Выбери вариант:',
            reply_markup=create_mood_keyboard()
        )
    elif any(word in text for word in ['хорошо', 'отлично', 'прекрасно']):
        await save_to_google_sheets(update, "Хорошее (текст)")
        await update.message.reply_text('Это радует! 😊')
    elif any(word in text for word in ['плохо', 'ужасно', 'грустно']):
        await save_to_google_sheets(update, "Плохое (текст)")
        await update.message.reply_text(
            'Не грусти! Всё наладится! 🌈',
            reply_markup=create_bad_mood_keyboard()
        )
    else:
        await update.message.reply_text('Пока я умею только спрашивать о настроении 🤖')

# Обработчик причины плохого настроения
async def reason_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает причину плохого настроения"""
    reason = update.message.text
    await save_to_google_sheets(update, "Плохое", reason)
    await update.message.reply_text(
        f"Спасибо, что поделился. Я запомнил: {reason}\n"
        "Надеюсь, тебе станет лучше! Если хочешь поговорить, я всегда здесь."
    )
    return ConversationHandler.END

# Обработчик отмены диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет текущий диалог"""
    await update.message.reply_text('Диалог прерван. Если захочешь поговорить, я всегда здесь!')
    return ConversationHandler.END

# Основная функция
def main() -> None:
    """Запуск бота"""
    # Инициализируем Google Sheets
    worksheet = init_google_sheets()
    if worksheet:
        logger.info("Подключение к Google Таблицам установлено")
    else:
        logger.warning("Не удалось подключиться к Google Таблицам. Данные не будут сохраняться.")
    
    # Создаем Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Создаем ConversationHandler для обработки диалога
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern=f'^{TELL_REASON}$')],
        states={
            MOOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, reason_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()