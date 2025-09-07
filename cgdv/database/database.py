import sqlite3
import json
import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from config.settings import Settings

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self):
        settings = Settings()
        self.db_path = settings.DATABASE_PATH
        
        # Создаем папку для БД если её нет
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.init_database()
        logger.info(f"📁 База данных инициализирована: {self.db_path}")
    
    def init_database(self):
        """Инициализация структуры базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                profile_data TEXT,
                photo_id TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица лайков
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_user_id, to_user_id),
                FOREIGN KEY (from_user_id) REFERENCES users (telegram_id),
                FOREIGN KEY (to_user_id) REFERENCES users (telegram_id)
            )
        ''')
        
        # Таблица матчей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                UNIQUE(user1_id, user2_id),
                FOREIGN KEY (user1_id) REFERENCES users (telegram_id),
                FOREIGN KEY (user2_id) REFERENCES users (telegram_id)
            )
        ''')
        
        # Индексы для производительности
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_likes_from_user ON likes(from_user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_likes_to_user ON likes(to_user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_matches_users ON matches(user1_id, user2_id)')
        
        conn.commit()
        conn.close()
    
    def _execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Выполнение SQL запроса с обработкой ошибок"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.rowcount
            
            conn.close()
            return result
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка базы данных: {e}")
            if 'conn' in locals():
                conn.close()
            return []
    
    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя по Telegram ID"""
        result = self._execute_query(
            "SELECT * FROM users WHERE telegram_id = ?", 
            (telegram_id,)
        )
        
        if result:
            user = dict(result[0])
            # Парсим JSON данные профиля
            if user['profile_data']:
                try:
                    user['profile_data'] = json.loads(user['profile_data'])
                except json.JSONDecodeError:
                    user['profile_data'] = {}
            else:
                user['profile_data'] = {}
            return user
        
        return None
    
    def create_user(self, telegram_id: int, username: str = None) -> bool:
        """Создание нового пользователя"""
        try:
            self._execute_query(
                "INSERT INTO users (telegram_id, username, profile_data) VALUES (?, ?, ?)",
                (telegram_id, username, "{}")
            )
            logger.info(f"👤 Создан новый пользователь: {telegram_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка создания пользователя: {e}")
            return False
    
    def update_user(self, telegram_id: int, **kwargs) -> bool:
        """Обновление данных пользователя"""
        if not kwargs:
            return False
        
        # Специальная обработка для profile_data
        if 'profile_data' in kwargs and isinstance(kwargs['profile_data'], dict):
            kwargs['profile_data'] = json.dumps(kwargs['profile_data'])
        
        # Добавляем обновление времени активности
        kwargs['last_activity'] = datetime.now().isoformat()
        
        fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [telegram_id]
        
        try:
            self._execute_query(
                f"UPDATE users SET {fields} WHERE telegram_id = ?",
                tuple(values)
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления пользователя: {e}")
            return False
    
    def get_potential_matches(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение потенциальных совпадений для пользователя"""
        query = '''
            SELECT * FROM users 
            WHERE telegram_id != ? 
            AND is_active = 1
            AND profile_data IS NOT NULL
            AND profile_data != '{}'
            AND profile_data != ''
            AND telegram_id NOT IN (
                SELECT to_user_id FROM likes WHERE from_user_id = ?
            )
            ORDER BY RANDOM()
            LIMIT ?
        '''
        
        result = self._execute_query(query, (user_id, user_id, limit))
        
        users = []
        for row in result:
            user = dict(row)
            # Парсим данные профиля
            if user['profile_data']:
                try:
                    user['profile_data'] = json.loads(user['profile_data'])
                    users.append(user)
                except json.JSONDecodeError:
                    continue
        
        return users
    
    def add_like(self, from_user_id: int, to_user_id: int) -> bool:
        """Добавление лайка. Возвращает True если это взаимный лайк"""
        try:
            # Добавляем лайк
            self._execute_query(
                "INSERT INTO likes (from_user_id, to_user_id) VALUES (?, ?)",
                (from_user_id, to_user_id)
            )
            
            # Проверяем взаимный лайк
            mutual_like = self._execute_query(
                "SELECT 1 FROM likes WHERE from_user_id = ? AND to_user_id = ?",
                (to_user_id, from_user_id)
            )
            
            if mutual_like:
                # Создаем матч
                user1_id = min(from_user_id, to_user_id)
                user2_id = max(from_user_id, to_user_id)
                
                self._execute_query(
                    "INSERT OR IGNORE INTO matches (user1_id, user2_id) VALUES (?, ?)",
                    (user1_id, user2_id)
                )
                
                logger.info(f"💖 Создан матч: {from_user_id} <-> {to_user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка добавления лайка: {e}")
            return False
    
    def get_user_matches(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение матчей пользователя"""
        query = '''
            SELECT u.* FROM users u 
            JOIN matches m ON (u.telegram_id = m.user1_id OR u.telegram_id = m.user2_id)
            WHERE (m.user1_id = ? OR m.user2_id = ?) 
            AND u.telegram_id != ?
            AND m.is_active = 1
            ORDER BY m.created_at DESC
        '''
        
        result = self._execute_query(query, (user_id, user_id, user_id))
        
        users = []
        for row in result:
            user = dict(row)
            if user['profile_data']:
                try:
                    user['profile_data'] = json.loads(user['profile_data'])
                    users.append(user)
                except json.JSONDecodeError:
                    continue
        
        return users
    
    def get_stats(self) -> Dict[str, int]:
        """Получение статистики бота"""
        stats = {}
        
        # Общее количество пользователей
        total_users = self._execute_query("SELECT COUNT(*) as count FROM users")
        stats['total_users'] = total_users[0]['count'] if total_users else 0
        
        # Активные пользователи (последние 7 дней)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        active_users = self._execute_query(
            "SELECT COUNT(*) as count FROM users WHERE last_activity > ?", 
            (week_ago,)
        )
        stats['active_users'] = active_users[0]['count'] if active_users else 0
        
        # Количество матчей
        total_matches = self._execute_query("SELECT COUNT(*) as count FROM matches WHERE is_active = 1")
        stats['total_matches'] = total_matches[0]['count'] if total_matches else 0
        
        # Количество лайков за сегодня
        today = datetime.now().strftime('%Y-%m-%d')
        today_likes = self._execute_query(
            "SELECT COUNT(*) as count FROM likes WHERE DATE(created_at) = ?", 
            (today,)
        )
        stats['today_likes'] = today_likes[0]['count'] if today_likes else 0
        
        return stats
    
    def cleanup_inactive_users(self, days: int = 30) -> int:
        """Деактивация неактивных пользователей"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        result = self._execute_query(
            "UPDATE users SET is_active = 0 WHERE last_activity < ? AND is_active = 1",
            (cutoff_date,)
        )
        
        logger.info(f"🧹 Деактивировано {result} неактивных пользователей")
        return result if isinstance(result, int) else 0