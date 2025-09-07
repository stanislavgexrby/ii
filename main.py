from tgbot_for_cg import (
    init_google_sheets,
    handle_main_menu,
    handle_main_menu_admin,
    handle_agreement,
    check_subscription_handler,
    start,
    cancel,
    single_poll_last_name,
    single_poll_name,
    single_poll_nick,
    single_poll_mmr,
    wrong_mmr_input,
    single_poll_roles,
    wrong_roles_input,
    single_poll_dotabuff,
    single_poll_tg,
    wrong_tg_input,
    multi_poll_age,
    multi_poll_name,
    BOT_TOKEN,
    logger,
    MAIN_MENU,
    MAIN_MENU_ADMIN,
    SINGLE_POLL_NAME,
    SINGLE_POLL_LAST_NAME,
    SINGLE_POLL_NICK,
    SINGLE_POLL_MMR,
    SINGLE_POLL_ROLES,
    SINGLE_POLL_DOTABUFF,
    SINGLE_POLL_TG,
    SINGLE_POLL_AGREEMENT,
    MULTI_POLL_CURRENT_NAME,
    MULTI_POLL_CURRENT_AGE,
    CHECK_SUBSCRIPTION
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
            MAIN_MENU_ADMIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu_admin)
            ],
            SINGLE_POLL_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, single_poll_name)
            ],
            SINGLE_POLL_LAST_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, single_poll_last_name)
            ],
            SINGLE_POLL_NICK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, single_poll_nick)
            ],
            SINGLE_POLL_MMR: [
                MessageHandler(filters.Regex(r'^\d+$') & ~filters.COMMAND, single_poll_mmr),
                MessageHandler(filters.TEXT & ~filters.COMMAND, wrong_mmr_input)
            ],
            SINGLE_POLL_ROLES: [
                MessageHandler(filters.Regex(r'^\d+(\s*,\s*\d+)*$') & ~filters.COMMAND, single_poll_roles),
                MessageHandler(filters.TEXT & ~filters.COMMAND, wrong_roles_input)
            ],
            SINGLE_POLL_DOTABUFF: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, single_poll_dotabuff)
            ],
            SINGLE_POLL_TG: [
                MessageHandler(filters.Regex(r'^@[a-zA-Z0-9_]{5,32}$') & ~filters.COMMAND, single_poll_tg),
                MessageHandler(filters.TEXT & ~filters.COMMAND, wrong_tg_input)
            ],
            SINGLE_POLL_AGREEMENT: [
                MessageHandler(filters.Regex('^(Да|Нет)$'), handle_agreement)
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