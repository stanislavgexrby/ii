from google.oauth2.service_account import Credentials
import gspread
from telegram import (
    Update,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
)

from .keyboards import create_subscription_keyboard, create_main_menu_keyboard, create_agreement_keyboard, create_main_menu_admin_keyboard
from .config import SCOPES, SERVICE_ACCOUNT_FILE, SPREADSHEET_ID, CHANNEL_USERNAME, CHANNEL_ID, ADMIN_ID
from .logger_setup import logger
from .global_states import (
    user_data,
    MAIN_MENU,
    MAIN_MENU_ADMIN,
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

def init_google_sheets():
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.sheet1

        return worksheet
    except Exception as e:
        logger.error(f"Ошибка инициализации Google Sheets: {e}")
        return None

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data:
        del user_data[user_id]

    await update.message.reply_text(
        "Операция отменена.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "Добро пожаловать в админ-панель! Выберите действие:",
            reply_markup=create_main_menu_admin_keyboard()
        )
        return MAIN_MENU_ADMIN
    else:
        if not await check_subscription(update, context):
            await update.message.reply_text(
                'Для использования бота необходимо подписаться на наш канал!\n\n'
                f'Подпишитесь на канал {CHANNEL_USERNAME} и нажмите кнопку "Я подписался"',
                reply_markup=create_subscription_keyboard()
            )
            return CHECK_SUBSCRIPTION

    await update.message.reply_text(
        "Добро пожаловать! Выберите действие:",
        reply_markup = create_main_menu_keyboard()
    )
    return MAIN_MENU

async def single_poll_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Введите Фамилию:")
    return SINGLE_POLL_LAST_NAME

async def single_poll_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['last_name'] = update.message.text
    await update.message.reply_text("Введите ник игрока:")
    return SINGLE_POLL_NICK

async def single_poll_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nick'] = update.message.text
    await update.message.reply_text("Введите MMR:")
    return SINGLE_POLL_MMR

async def single_poll_mmr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mmr'] = update.message.text
    await update.message.reply_text("Введите роли игрока цифрами:") # тут еще клавитуру мб
    return SINGLE_POLL_ROLES

async def single_poll_roles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['roles'] = update.message.text
    await update.message.reply_text("Введите ссылку на профиль в dotabuff:")
    return SINGLE_POLL_DOTABUFF

async def single_poll_dotabuff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['dotabuff'] = update.message.text
    await update.message.reply_text("Введите tg игрока через @:")
    return SINGLE_POLL_TG

async def single_poll_tg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tg'] = update.message.text
    await update.message.reply_text(
        "Солгласны ли Вы на обработку персональных данных?:",
        reply_markup = create_agreement_keyboard()
    )
    return SINGLE_POLL_AGREEMENT

async def single_poll_agreement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # context.user_data['tg'] = update.message.text
    await update.message.reply_text(
        "Солгласны ли Вы на обработку персональных данных?:",
        reply_markup = create_agreement_keyboard()
    )
    return SINGLE_POLL_AGREEMENT

async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sheet = init_google_sheets()
        sheet.append_row([
            context.user_data.get('name', ''),
            context.user_data.get('last_name', ''),
            context.user_data.get('nick', ''),
            context.user_data.get('mmr', ''),
            context.user_data.get('roles', ''),
            context.user_data.get('dotabuff', ''),
            context.user_data.get('tg', ''),
        ])
    except Exception as e:
        logger.error(f"Ошибка сохранения в Google Sheets: {e}")
        await update.message.reply_text("Ошибка при сохранении данных.")

async def multi_poll_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_data = user_data[user_id]
    current_data['current_name'] = update.message.text
    await update.message.reply_text("Введите возраст:")
    return MULTI_POLL_CURRENT_AGE

async def multi_poll_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_data = user_data[user_id]
    current_data['current_age'] = update.message.text

    current_data['responses'].append({
        'name': current_data['current_name'],
        'age': current_data['current_age']
    })

    current_data['current'] += 1

    if current_data['current'] >= 5:
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

        del user_data[user_id]

        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=create_main_menu_keyboard()
        )
        return MAIN_MENU
    else:
        await update.message.reply_text(
            f"Введите имя человека {current_data['current'] + 1}:"
        )
        return MULTI_POLL_CURRENT_NAME