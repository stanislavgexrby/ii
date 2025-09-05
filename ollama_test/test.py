import os

if __name__ == "__main__":
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASS")

    if not email_user or not email_pass:
        print("ОШИБКА: Переменные окружения не найдены!")
        print("Убедитесь, что вы настроили .bashrc, .zshenv или .env файл")
    else:
        print("Переменные окружения успешно загружены!")
        print(f"Email: {email_user}")
        print(f"Пароль: {email_pass}")