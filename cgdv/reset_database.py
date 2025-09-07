# reset_database.py
"""
Скрипт для сброса базы данных TeammateBot
Используйте если возникли проблемы с миграциями
"""

import os
from pathlib import Path

def reset_database():
    """Сброс базы данных"""
    db_path = Path("data/teammates.db")
    
    if db_path.exists():
        try:
            os.remove(db_path)
            print("✅ База данных удалена")
        except Exception as e:
            print(f"❌ Ошибка удаления базы данных: {e}")
            return False
    else:
        print("✅ База данных не существует")
    
    print("🔄 Перезапустите бота для создания новой базы данных")
    return True

if __name__ == "__main__":
    print("🗑️  Сброс базы данных TeammateBot")
    print("⚠️  ВНИМАНИЕ: Все данные будут удалены!")
    
    confirm = input("Продолжить? (y/N): ").lower().strip()
    
    if confirm == 'y':
        reset_database()
    else:
        print("❌ Операция отменена")