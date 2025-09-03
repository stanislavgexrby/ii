import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
import gspread
from google.oauth2.service_account import Credentials
from config import BOT_TOKEN, SCOPES, SERVICE_ACCOUNT_FILE, SPREADSHEET_ID, CHANNEL_USERNAME, CHANNEL_ID

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
(
    MAIN_MENU,
    SINGLE_POLL_NAME,
    SINGLE_POLL_AGE,
    MULTI_POLL_COUNT,
    MULTI_POLL_CURRENT_NAME,
    MULTI_POLL_CURRENT_AGE,
    CHECK_SUBSCRIPTION
) = range(7)

# Глобальные переменные для хранения данных
user_data = {}

def create_subscription_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME}")],
        [InlineKeyboardButton("Я подписался ✅", callback_data="check_subscription")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Инициализация Google Sheets
# def init_google_sheets():
#     creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
#     client = gspread.authorize(creds)
#     return client.open_by_key(SPREADSHEET_ID).sheet1

def init_google_sheets():
    """Инициализирует подключение к Google Таблицам"""
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.sheet1  # Используем первый лист
        
        # # Добавляем заголовки, если лист пустой
        # if not worksheet.get_all_values():
        #     worksheet.append_row([
        #         'Timestamp', 'User ID', 'First Name', 'Last Name', 
        #         'Username', 'Mood', 'Reason', 'Message'
        #     ])
        
        return worksheet
    except Exception as e:
        logger.error(f"Ошибка инициализации Google Sheets: {e}")
        return None

# Проверка подписки на канал
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False


async def check_subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    """Обрабатывает нажатие кнопки проверки подписки"""
    query = update.callback_query
    await query.answer()

    # Проверяем подписку
    is_subscribed = await check_subscription(update, context)
    if is_subscribed:
        # Если подписан, обновляем сообщение и показываем основное меню
        user_id = update.effective_user.id
        user_data[user_id] = {}
        keyboard = [
            ["Опрос 1 человека", "Опрос 5 людей"],
            ["Заглушка для улучшения"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        # await context.bot.send_message(
        #     chat_id=query.message.chat_id,
        #     text="Спасибо за подписку! Теперь вы можете пользоваться ботом.\n Добро пожаловать! Выберите действие:",
        #     reply_markup=reply_markup
        # )
        # return MAIN_MENU
        # await query.edit_message_text(
        #     text="Спасибо за подписку! Теперь вы можете пользоваться ботом.\nДобро пожаловать!"
        # )
        
        # await context.bot.send_message(
        #     chat_id=query.message.chat_id,
        #     text="Выберите действие:",
        #     reply_markup=reply_markup
        # )
        
        # # Устанавливаем состояние через context
        # context.user_data['state'] = MAIN_MENU
        
        await query.delete_message()
        
        # Отправляем новое сообщение с главным меню
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Спасибо за подписку! Теперь вы можете пользоваться ботом.\nДобро пожаловать!",
            reply_markup=reply_markup
        )

        return MAIN_MENU
    else:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text='Вы еще не подписались на канал!\n\n'
                 f'Пожалуйста, подпишитесь на канал {CHANNEL_USERNAME} и нажмите кнопку "Я подписался"',
            reply_markup=create_subscription_keyboard()
        )
        return CHECK_SUBSCRIPTION

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_subscription(update, context):
        await update.message.reply_text(
            'Для использования бота необходимо подписаться на наш канал!\n\n'
            f'Подпишитесь на канал {CHANNEL_USERNAME} и нажмите кнопку "Я подписался"',
            reply_markup=create_subscription_keyboard()
        )
        return CHECK_SUBSCRIPTION
    
    keyboard = [
        ["Опрос 1 человека", "Опрос 5 людей"],
        ["Заглушка для улучшения"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Добро пожаловать! Выберите действие:",
        reply_markup=reply_markup
    )
    return MAIN_MENU

# Обработка выбора в главном меню
async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Опрос 1 человека":
        await update.message.reply_text(
            "Начинаем опрос 1 человека. Введите имя:",
            reply_markup=ReplyKeyboardRemove()
        )
        return SINGLE_POLL_NAME
        
    elif text == "Опрос 5 людей":
        user_data[update.effective_user.id] = {"responses": [], "current": 0}
        await update.message.reply_text(
            "Начинаем опрос 5 людей. Введите имя человека 1:",
            reply_markup=ReplyKeyboardRemove()
        )
        return MULTI_POLL_CURRENT_NAME
        
    elif text == "Заглушка для улучшения":
        await update.message.reply_text(
            "Этот функционал в разработке. "
            "Для добавления новой логики修改ите функцию 'handle_placeholder'",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
        
    else:
        await update.message.reply_text("Пожалуйста, выберите вариант из меню.")
        return MAIN_MENU

# Одиночный опрос - имя
async def single_poll_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Введите возраст:")
    return SINGLE_POLL_AGE

# Одиночный опрос - возраст
async def single_poll_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['age'] = update.message.text
    
    # Сохранение в Google Sheets
    try:
        sheet = init_google_sheets()
        sheet.append_row([
            update.effective_user.id,
            context.user_data['name'],
            context.user_data['age']
        ])
        await update.message.reply_text("Данные сохранены в таблицу!")
    except Exception as e:
        logger.error(f"Ошибка сохранения в Google Sheets: {e}")
        await update.message.reply_text("Ошибка при сохранении данных.")
    
    # Возврат в главное меню
    keyboard = [["Опрос 1 человека", "Опрос 5 людей"], ["Заглушка для улучшения"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=reply_markup
    )
    return MAIN_MENU

# Многопользовательский опрос - имя
async def multi_poll_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_data = user_data[user_id]
    current_data['current_name'] = update.message.text
    await update.message.reply_text("Введите возраст:")
    return MULTI_POLL_CURRENT_AGE

# Многопользовательский опрос - возраст
async def multi_poll_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_data = user_data[user_id]
    current_data['current_age'] = update.message.text
    
    # Добавляем ответ в список
    current_data['responses'].append({
        'name': current_data['current_name'],
        'age': current_data['current_age']
    })
    
    # Увеличиваем счетчик
    current_data['current'] += 1
    
    # Проверяем, собрали ли все 5 ответов
    if current_data['current'] >= 5:
        # Сохраняем все ответы в Google Sheets
        try:
            sheet = init_google_sheets()
            for response in current_data['responses']:
                sheet.append_row([
                    user_id,
                    response['name'],
                    response['age'],
                    "Многопользовательский опрос"
                ])
            await update.message.reply_text("Все данные сохранены в таблицу!")
        except Exception as e:
            logger.error(f"Ошибка сохранения в Google Sheets: {e}")
            await update.message.reply_text("Ошибка при сохранении данных.")
        
        # Очищаем временные данные
        del user_data[user_id]
        
        # Возврат в главное меню
        keyboard = [["Опрос 1 человека", "Опрос 5 людей"], ["Заглушка для улучшения"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=reply_markup
        )
        return MAIN_MENU
    else:
        # Запрашиваем данные следующего человека
        await update.message.reply_text(
            f"Введите имя человека {current_data['current'] + 1}:"
        )
        return MULTI_POLL_CURRENT_NAME

# Заглушка для будущего улучшения
async def handle_placeholder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # МЕСТО ДЛЯ БУДУЩЕГО РАСШИРЕНИЯ ФУНКЦИОНАЛА
    # Добавьте сюда новую логику при расширении бота
    
    await update.message.reply_text(
        "Этот функционал еще в разработке. "
    )
    
    # Возврат в главное меню
    keyboard = [["Опрос 1 человека", "Опрос 5 людей"], ["Заглушка для улучшения"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=reply_markup
    )
    return MAIN_MENU

# Отмена операции
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data:
        del user_data[user_id]
    
    await update.message.reply_text(
        "Операция отменена.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# Основная функция
def main():
    worksheet = init_google_sheets()
    if worksheet:
        logger.info("Подключение к Google Таблицам установлено")
    else:
        logger.warning("Не удалось подключиться к Google Таблицам. Данные не будут сохраняться.")
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Regex('^(Опрос 1 человека|Опрос 5 людей|Заглушка для улучшения)$'), handle_main_menu)
            ],
            SINGLE_POLL_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, single_poll_name)
            ],
            SINGLE_POLL_AGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, single_poll_age)
            ],
            MULTI_POLL_CURRENT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, multi_poll_name)
            ],
            MULTI_POLL_CURRENT_AGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, multi_poll_age)
            ],
            CHECK_SUBSCRIPTION: [
                CallbackQueryHandler(check_subscription_handler)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=False,  # Добавьте эту строку
        per_chat=True,
        per_user=True
    )
    
    # Добавляем обработчики
    application.add_handler(conv_handler)
    
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()