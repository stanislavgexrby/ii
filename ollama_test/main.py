import sys

try:
    import requests
    import os
    import gspread
    from google.oauth2.service_account import Credentials
    import smtplib
    from email.mime.text import MIMEText
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError as e:
    print("Ошибка: Не установлены необходимые зависимости.")
    print("Установите их командой: pip install -r requirements.txt")
    print(f"Отсутствующая библиотека: {e.name}")
    sys.exit(1)

def ask_ollama(prompt, model="mistral:7b"):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7}
    }

    try:
        response = requests.post(url, json=payload)
        return response.json().get("response", "Ошибка: пустой ответ")
    except Exception as e:
        return f"Ошибка запроса: {str(e)}"

# if __name__ == "__main__":
#     while True:
#         user_input = input("\nВы: ")
#         if user_input.lower() in ['exit', 'выход']:
#             break
#
#         response = ask_ollama(user_input)
#         print("\n Mistral:", response)

def send_email_with_ollama(subject, recipient, body_prompt):
    email_body = ask_ollama(
        f"Напиши профессиональное письмо на русском языке по следующему описанию: {body_prompt}"
    )

    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")

    msg = MIMEText(email_body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        print(f"Письмо отправлено на {recipient}")
        return True
    except Exception as e:
        print(f"Ошибка отправки: {str(e)}")
        return False

# send_email_with_ollama(
#     "Коммерческое предложение",
#     "email",
#     "Предложить сотрудничество по разработке ИИ-решений"
# )

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_google_sheet(sheet_name):
    creds = Credentials.from_service_account_file(
        'service-account.json',
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

def read_sheet(sheet):
    """Чтение данных из таблицы"""
    return sheet.get_all_records()  # Возвращает список словарей

def write_to_sheet(sheet, data):
    """Запись данных в таблицу"""
    # data должен быть списком списков
    sheet.append_rows(data)

def update_cell(sheet, row, col, value):
    """Обновление конкретной ячейки"""
    sheet.update_cell(row, col, value)

# Пример использования
if __name__ == "__main__":
    # Получаем доступ к таблице
    sheet = get_google_sheet("table_name")

    # Чтение данных
    data = read_sheet(sheet)
    print("Данные из таблицы:")
    for row in data:
        print(row)

    # Запись новых данных
    new_data = [
        ["2023-07-11", "Новая запись", 42],
        ["2023-07-12", "Еще одна запись", 99]
    ]
    write_to_sheet(sheet, new_data)
    print("\nДанные успешно добавлены!")

    # Обновление ячейки
    update_cell(sheet, 2, 3, "Обновленное значение")