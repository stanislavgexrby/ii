# run.bat - Скрипт запуска для Windows
@echo off
chcp 65001 > nul
echo 🎮 Запуск TeammateBot...

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python 3.8+ с python.org
    pause
    exit /b 1
)

REM Проверяем версию Python
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo ✅ Python %python_version% найден

REM Создаем виртуальное окружение если его нет
if not exist "venv" (
    echo 📦 Создание виртуального окружения...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Ошибка создания виртуального окружения
        pause
        exit /b 1
    )
)

REM Активируем виртуальное окружение
echo 🔌 Активация виртуального окружения...
call venv\Scripts\activate

REM Обновляем pip
echo 📥 Обновление pip...
python -m pip install --upgrade pip >nul 2>&1

REM Устанавливаем зависимости
echo 📥 Установка зависимостей...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Ошибка установки зависимостей
    pause
    exit /b 1
)

REM Проверяем конфигурацию
echo 🔧 Проверка конфигурации...

if exist ".env" (
    echo ✅ Найден файл .env
) else (
    echo ⚠️  Файл .env не найден. Создайте его из .env.example
    echo Или запустите: python install.py
    pause
    exit /b 1
)

echo ✅ Конфигурация проверена

REM Создаем папку для данных
if not exist "data" mkdir data

REM Запускаем бота
echo 🚀 Запуск бота...
echo Для остановки нажмите Ctrl+C
echo.

python main.py

pause