import logging
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

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота (получите у @BotFather)
BOT_TOKEN = "8495792418:AAFNWoOWEiC14yckH4vacJZkV561FcOaOsk"

# Состояния для ConversationHandler
MOOD, REASON = range(2)

# Константы для callback_data (избегаем магических строк)
(
    MOOD_GOOD, MOOD_NORMAL, MOOD_BAD, 
    TELL_REASON, NEED_HUG, CANCEL
) = (
    'mood_good', 'mood_normal', 'mood_bad', 
    'tell_reason', 'need_hug', 'cancel'
)

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
        await query.edit_message_text(text="Круто! Рад за тебя! 😊\nЧто планируешь делать сегодня?")
    elif query.data == MOOD_NORMAL:
        await query.edit_message_text(text="Бывает и лучше, но главное - не унывать! 🙂")
    elif query.data == MOOD_BAD:
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
        await update.message.reply_text('Это радует! 😊')
    elif any(word in text for word in ['плохо', 'ужасно', 'грустно']):
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