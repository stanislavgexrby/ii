from tgbot_for_cg import init_google_sheets, handle_main_menu, check_subscription_handler
from tgbot_for_cg import start, cancel
from tgbot_for_cg import single_poll_age, single_poll_name, multi_poll_age, multi_poll_name
from tgbot_for_cg import BOT_TOKEN
from tgbot_for_cg import logger
from tgbot_for_cg import (
    user_data,
    MAIN_MENU,
    CHECK_SUBSCRIPTION,
    SINGLE_POLL_AGE,
    SINGLE_POLL_NAME,
    MULTI_POLL_COUNT,
    MULTI_POLL_CURRENT_AGE,
    MULTI_POLL_CURRENT_NAME
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)

def main():
    worksheet = init_google_sheets()
    if worksheet:
        logger.info("Подключение к Google Таблицам установлено")
    else:
        logger.warning("Не удалось подключиться к Google Таблицам. Данные не будут сохраняться.")
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Regex('^(Опрос 1 человека|Опрос 5 людей|Заглушка для улучшения|Отмена)$'), handle_main_menu)
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
        per_message=False,
        per_chat=True,
        per_user=True
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()