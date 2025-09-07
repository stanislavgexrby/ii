# check_config.py
"""
Скрипт проверки настроек TeammateBot
"""

import os
import sys
from pathlib import Path

def check_python_version():
    """Проверка версии Python"""
    print("🐍 Проверка Python...")
    
    if sys.version_info < (3, 8):
        print(f"❌ Требуется Python 3.8+, установлена: {sys.version_info.major}.{sys.version_info.minor}")
        return False
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
        return True

def check_dependencies():
    """Проверка зависимостей"""
    print("\n📦 Проверка зависимостей...")
    
    required = ['aiogram', 'aiohttp', 'python-dotenv']
    missing = []
    
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n🔧 Установите недостающие пакеты:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

def check_env_file():
    """Проверка .env файла"""
    print("\n⚙️ Проверка .env файла...")
    
    env_path = Path(".env")
    
    if not env_path.exists():
        print("❌ Файл .env не найден")
        print("📝 Создайте файл .env из .env.example")
        return False
    
    print("✅ Файл .env найден")
    
    # Проверяем основные настройки
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = {
        'BOT_TOKEN': 'Токен бота от @BotFather',
        'ADMIN_ID': 'Ваш Telegram ID',
        'DOTA_CHANNEL_ID': 'Канал для Dota 2',
        'CS_CHANNEL_ID': 'Канал для CS2'
    }
    
    all_ok = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        
        if not value or value in ['your_bot_token_here', '123456789', '@your_dota_channel', '@your_cs_channel']:
            print(f"❌ {var}: {description}")
            all_ok = False
        else:
            # Скрываем токен для безопасности
            if var == 'BOT_TOKEN':
                display_value = value[:10] + "..." if len(value) > 10 else "установлен"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
    
    return all_ok

def check_bot_token():
    """Проверка токена бота"""
    print("\n🤖 Проверка токена бота...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv('BOT_TOKEN')
    
    if not token or token == 'your_bot_token_here':
        print("❌ Токен бота не установлен")
        return False
    
    if len(token) < 40:
        print("❌ Токен бота выглядит некорректно (слишком короткий)")
        return False
    
    if ':' not in token:
        print("❌ Токен бота выглядит некорректно (нет разделителя)")
        return False
    
    print("✅ Токен бота выглядит корректно")
    return True

def check_database():
    """Проверка базы данных"""
    print("\n🗄️ Проверка базы данных...")
    
    data_dir = Path("data")
    db_path = data_dir / "teammates.db"
    
    if not data_dir.exists():
        print("📁 Папка data не существует, будет создана при запуске")
        return True
    
    if not db_path.exists():
        print("📊 База данных не существует, будет создана при запуске")
        return True
    
    # Проверяем доступность БД
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        
        print(f"✅ База данных доступна ({len(tables)} таблиц)")
        return True
    except Exception as e:
        print(f"❌ Ошибка доступа к БД: {e}")
        return False

def check_file_structure():
    """Проверка структуры файлов"""
    print("\n📁 Проверка структуры файлов...")
    
    required_files = [
        'main.py',
        'requirements.txt',
        'config/settings.py',
        'database/database.py',
        'handlers/start.py',
        'handlers/profile.py',
        'handlers/search.py',
        'handlers/likes.py',
        'keyboards/keyboards.py',
        'utils/texts.py',
        'utils/validators.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n🚨 Отсутствуют файлы: {len(missing_files)}")
        return False
    
    print("\n✅ Все файлы на месте")
    return True

def main():
    """Основная функция проверки"""
    print("🔍 Проверка настроек TeammateBot")
    print("=" * 40)
    
    checks = [
        check_python_version,
        check_file_structure,
        check_dependencies,
        check_env_file,
        check_bot_token,
        check_database
    ]
    
    passed = 0
    total = len(checks)
    
    for check in checks:
        try:
            if check():
                passed += 1
        except Exception as e:
            print(f"❌ Ошибка проверки: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Результат: {passed}/{total} проверок пройдено")
    
    if passed == total:
        print("🎉 Все настройки корректны! Можно запускать бота.")
        print("🚀 Запуск: python main.py")
    else:
        print("⚠️  Есть проблемы с настройками. Исправьте их перед запуском.")
        
        if passed < total // 2:
            print("💡 Рекомендуется переустановка: python install.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Проверка прервана")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")