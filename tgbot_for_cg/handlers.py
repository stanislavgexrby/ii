from telegram import (
    Update,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
)

from .config import CHANNEL_USERNAME
from .keyboards import create_main_menu_keyboard, create_subscription_keyboard
from .logger_setup import logger
from .global_states import user_data, MAIN_MENU, MAIN_MENU_ADMIN, CHECK_SUBSCRIPTION, SINGLE_POLL_NAME, MULTI_POLL_CURRENT_NAME, SINGLE_POLL_AGREEMENT
from .core import check_subscription, save

async def check_subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    query = update.callback_query
    await query.answer()

    is_subscribed = await check_subscription(update, context)
    if is_subscribed:
        user_id = update.effective_user.id
        user_data[user_id] = {}

        await query.delete_message()

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Спасибо за подписку! Теперь вы можете пользоваться ботом.\nДобро пожаловать!",
            reply_markup=create_main_menu_keyboard()
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

async def handle_agreement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Да":
        await save(update, context)
        await update.message.reply_text(
            "Спасибо за участие, ваши данные сохранены\nВыберите действие:",
            reply_markup=create_main_menu_keyboard()
        )
        return MAIN_MENU

    elif text == "Нет":
        await update.message.reply_text(
            "Спасибо за использование бота!\nВыберите действие:",
            reply_markup=create_main_menu_keyboard()
        )
        return MAIN_MENU

    else:
        await update.message.reply_text("Пожалуйста, выберите вариант из меню.")
        return SINGLE_POLL_AGREEMENT

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
            "Этот функционал в разработке.\n",
        )

        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=create_main_menu_keyboard()
        )
        return MAIN_MENU

    elif text == "Отмена":
        await update.message.reply_text(
            "Спасибо за использование бота!",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    else:
        await update.message.reply_text("Пожалуйста, выберите вариант из меню.")
        return MAIN_MENU

async def handle_main_menu_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Опрос 1 человека":
        await update.message.reply_text(
            "Начинаем опрос 1 человека для админа. Введите имя:",
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
            "Этот функционал в разработке.\n",
        )

        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=create_main_menu_keyboard()
        )
        return MAIN_MENU_ADMIN

    elif text == "Отмена":
        await update.message.reply_text(
            "Спасибо за использование бота!",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    else:
        await update.message.reply_text("Пожалуйста, выберите вариант из меню.")
        return MAIN_MENU_ADMIN

async def handle_placeholder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TO DO
    await update.message.reply_text(
        "Этот функционал еще в разработке. "
    )

    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=create_main_menu_keyboard()
    )
    return MAIN_MENU