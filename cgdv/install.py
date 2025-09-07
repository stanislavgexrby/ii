# install.py - Скрипт автоматической установки
"""
Скрипт автоматической установки GameMatch бота
Запустите: python install.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"Установлена версия: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} найден")
    return True

def create_virtual_env():
    """Создание виртуального окружения"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ Виртуальное окружение уже существует")
        return True
    
    print("📦 Создание виртуального окружения...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Виртуальное окружение создано")
        return True
    except subprocess.CalledProcessError:
        print("❌ Ошибка создания виртуального окружения")
        return False

def get_pip_command():
    """Получение команды pip для текущей системы"""
    if os.name == 'nt':  # Windows
        return str(Path("venv/Scripts/pip.exe"))
    else:  # Linux/macOS
        return str(Path("venv/bin/pip"))

def install_dependencies():
    """Установка зависимостей"""
    print("📥 Установка зависимостей...")
    
    pip_cmd = get_pip_command()
    
    try:
        # Обновляем pip
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
        
        # Устанавливаем зависимости
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        
        print("✅ Зависимости установлены")
        return True
    except subprocess.CalledProcessError:
        print("❌ Ошибка установки зависимостей")
        return False

def create_env_file():
    """Создание .env файла"""
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if env_path.exists():
        print("✅ Файл .env уже существует")
        return True
    
    if not env_example_path.exists():
        print("⚠️  Файл .env.example не найден")
        return False
    
    print("📝 Создание файла .env...")
    
    try:
        shutil.copy(env_example_path, env_path)
        print("✅ Файл .env создан из .env.example")
        print("")
        print("🔧 ВАЖНО: Отредактируйте файл .env и укажите:")
        print("   - BOT_TOKEN (получите у @BotFather)")
        print("   - ADMIN_ID (ваш Telegram ID от @userinfobot)")
        print("")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания .env файла: {e}")
        return False

def create_data_folder():
    """Создание папки для данных"""
    data_path = Path("data")
    
    if not data_path.exists():
        print("📁 Создание папки data...")
        data_path.mkdir()
        print("✅ Папка data создана")
    else:
        print("✅ Папка data уже существует")

def main():
    """Основная функция установки"""
    print("🎮 Установка GameMatch бота")
    print("=" * 40)
    
    # Проверяем Python
    if not check_python_version():
        return False
    
    # Создаем виртуальное окружение
    if not create_virtual_env():
        return False
    
    # Устанавливаем зависимости
    if not install_dependencies():
        return False
    
    # Создаем .env файл
    create_env_file()
    
    # Создаем папку для данных
    create_data_folder()
    
    print("")
    print("🎉 Установка завершена!")
    print("")
    print("📋 Следующие шаги:")
    print("1. Получите токен бота у @BotFather")
    print("2. Узнайте ваш Telegram ID у @userinfobot")
    print("3. Отредактируйте файл .env (укажите BOT_TOKEN и ADMIN_ID)")
    print("4. Запустите бота:")
    
    if os.name == 'nt':  # Windows
        print("   run.bat")
    else:  # Linux/macOS
        print("   ./run.sh")
    
    print("")
    print("📖 Подробные инструкции в README.md")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Установка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)