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

def init_google_sheets(sheet_name=None):
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.sheet1
        if sheet_name:
            worksheet = spreadsheet.worksheet(sheet_name)
        else:
            worksheet = spreadsheet.sheet1
        return worksheet
    except Exception as e:
        logger.error(f"Ошибка инициализации Google Sheets: {e}")
        return None

def get_sheet_by_role(role_number):
    role_to_sheet = {
        1: "carry(1)",
        2: "mid(2)",
        3: "offlane(3)",
        4: "soft(4)",
        5: "hard(5)"
    }
    return role_to_sheet.get(role_number, "Other Players")

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
    mmr_text = update.message.text
    mmr = int(mmr_text)

    context.user_data['mmr'] = mmr

    await update.message.reply_text(
        "Выберите роли, которые вы играете (введите номера через запятую, например: 1, 3, 5):\n"
        "1 - Керри\n"
        "2 - Мидер\n"
        "3 - Оффлейн\n"
        "4 - Саппорт\n"
        "5 - Хард саппорт"
    )
    return SINGLE_POLL_ROLES

async def wrong_mmr_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Пожалуйста, введите MMR числом (например: 4500)"
    )
    return SINGLE_POLL_MMR

def format_roles(role_numbers):
    role_mapping = {
        1: "Carry",
        2: "Mid",
        3: "Offlane",
        4: "Support",
        5: "Hard Support"
    }

    role_names = [role_mapping.get(num, f"Unknown({num})") for num in role_numbers]

    return ", ".join(role_names)

async def single_poll_roles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    numbers = [num.strip() for num in text.split(',')]

    try:
        numbers = [int(num) for num in numbers]
    except ValueError:
        await update.message.reply_text(
            "Пожалуйста, введите только числа, разделенные запятыми (например: 1, 2, 3)"
        )
        return SINGLE_POLL_ROLES

    if any(num < 1 or num > 5 for num in numbers):
        await update.message.reply_text(
            "Пожалуйста, введите только числа от 1 до 5\n"
            "Доступные роли:\n"
            "1 - Керри\n"
            "2 - Мидер\n"
            "3 - Хардлейнер\n"
            "4 - Саппорт\n"
            "5 - Фуллсаппорт"
        )
        return SINGLE_POLL_ROLES

    context.user_data['roles_numbers'] = numbers

    formatted_roles = format_roles(numbers)
    context.user_data['roles'] = formatted_roles

    await update.message.reply_text("Введите ссылку на dotabuff:")
    return SINGLE_POLL_DOTABUFF

async def wrong_roles_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Пожалуйста, введите номера ролей через запятую (например: 1, 3, 5)\n"
        "Доступные роли:\n"
        "1 - Керри\n"
        "2 - Мидер\n"
        "3 - Хардлейнер\n"
        "4 - Саппорт\n"
        "5 - Фуллсаппорт"
    )
    return SINGLE_POLL_ROLES

async def single_poll_dotabuff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['dotabuff'] = update.message.text
    await update.message.reply_text("Введите tg игрока через @:")
    return SINGLE_POLL_TG

async def single_poll_tg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tg'] = update.message.text
    if not await check_subscription(update, context):
        await update.message.reply_text(
                'Данный телеграмм аккаунт не подписан на канал {CHANNEL_USERNAME}.\n\n'
                f'Если в момент окончания регистрации на турнир данный аккаунт не будет подписан, к участию игрок не будет допущен'
        )
    await update.message.reply_text(
        "Солгласны ли Вы на обработку персональных данных?:",
        reply_markup = create_agreement_keyboard()
    )
    return SINGLE_POLL_AGREEMENT

async def wrong_tg_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Пожалуйста, введите корректный Telegram тег.\n"
        "Тег должен:\n"
        "- Начинаться с @\n"
        "- Содержать только буквы, цифры и подчеркивания\n"
        "- Иметь длину от 5 до 32 символов (после @)\n"
        "Пример: @my_username"
    )
    return SINGLE_POLL_TG

async def single_poll_agreement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Солгласны ли Вы на обработку персональных данных?:",
        reply_markup = create_agreement_keyboard()
    )
    return SINGLE_POLL_AGREEMENT

async def save(update: Update, context: ContextTypes.DEFAULT_TYPE, single: bool):
    try:
        user_data = [
            context.user_data.get('name', ''),
            context.user_data.get('last_name', ''),
            context.user_data.get('nick', ''),
            context.user_data.get('mmr', ''),
            context.user_data.get('roles', ''),
            context.user_data.get('dotabuff', ''),
            context.user_data.get('tg', ''),
        ]
        general_sheet = init_google_sheets()
        general_sheet.append_row(user_data)

        if single:
            solo_sheet = init_google_sheets("solo")
            solo_sheet.append_row(user_data)
        else:
            teams_sheet = init_google_sheets("teams")
            teams_sheet.append_row(user_data)

        if 'roles_numbers' in context.user_data:
            for role_num in context.user_data['roles_numbers']:
                sheet_name = get_sheet_by_role(role_num)
                role_sheet = init_google_sheets(sheet_name)  # Лист для конкретной роли
                role_sheet.append_row(user_data)

        context.user_data.clear()

        await update.message.reply_text(
            "Данные успешно сохранены!",
            reply_markup=create_main_menu_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка сохранения в Google Sheets: {e}")
        await update.message.reply_text(
            "Ошибка при сохранении данных.",
            reply_markup=create_main_menu_keyboard()
        )
    return MAIN_MENU

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