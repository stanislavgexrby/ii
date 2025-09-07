# run.sh - Скрипт запуска для Linux/macOS
#!/bin/bash

echo "🎮 Запуск TeammateBot..."

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен. Установите Python 3.8+ и попробуйте снова."
    exit 1
fi

# Проверяем версию Python
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)"; then
    echo "❌ Требуется Python 3.8+, установлена версия $python_version"
    exit 1
fi

echo "✅ Python $python_version найден"

# Создаем виртуальное окружение если его нет
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Ошибка создания виртуального окружения"
        exit 1
    fi
fi

# Активируем виртуальное окружение
echo "🔌 Активация виртуального окружения..."
source venv/bin/activate

# Обновляем pip
echo "📥 Обновление pip..."
pip install --upgrade pip > /dev/null 2>&1

# Устанавливаем зависимости
echo "📥 Установка зависимостей..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Ошибка установки зависимостей"
    exit 1
fi

# Проверяем конфигурацию
echo "🔧 Проверка конфигурации..."

# Проверяем наличие .env файла
if [ -f ".env" ]; then
    echo "✅ Найден файл .env"
    # Загружаем переменные из .env
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  Файл .env не найден. Создайте его из .env.example"
    echo "Или запустите: python3 install.py"
    exit 1
fi

# Проверяем токен бота
if [ -z "$BOT_TOKEN" ] || [ "$BOT_TOKEN" = "your_bot_token_here" ]; then
    echo "❌ BOT_TOKEN не настроен!"
    echo "Получите токен у @BotFather и добавьте в .env файл"
    exit 1
fi

echo "✅ Конфигурация проверена"

# Создаем папку для данных
mkdir -p data

# Запускаем бота
echo "🚀 Запуск бота..."
echo "Для остановки нажмите Ctrl+C"
echo ""

python3 main.py