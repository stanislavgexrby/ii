# database/database.py
"""
База данных для бота поиска сокомандников
"""

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
                game TEXT NOT NULL,
                name TEXT,
                nickname TEXT,
                age INTEGER,
                rating TEXT,
                positions TEXT,
                additional_info TEXT,
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
        
        # Таблица матчей (взаимные лайки)
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
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_game ON users(game)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_likes_from_user ON likes(from_user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_likes_to_user ON likes(to_user_id)')
        
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
            return dict(result[0])
        return None
    
    def create_user(self, telegram_id: int, username: str, game: str) -> bool:
        """Создание нового пользователя"""
        try:
            self._execute_query(
                "INSERT INTO users (telegram_id, username, game) VALUES (?, ?, ?)",
                (telegram_id, username, game)
            )
            logger.info(f"👤 Создан новый пользователь: {telegram_id} ({game})")
            return True
        except Exception as e:
            logger.error(f"Ошибка создания пользователя: {e}")
            return False
    
    def update_user_profile(self, telegram_id: int, name: str, nickname: str, 
                          age: int, rating: str, positions: List[str], 
                          additional_info: str, photo_id: str = None) -> bool:
        """Обновление профиля пользователя"""
        try:
            positions_json = json.dumps(positions)
            
            query = '''
                UPDATE users SET 
                name = ?, nickname = ?, age = ?, rating = ?, 
                positions = ?, additional_info = ?, photo_id = ?,
                last_activity = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
            '''
            
            self._execute_query(query, (
                name, nickname, age, rating, positions_json, 
                additional_info, photo_id, telegram_id
            ))
            
            logger.info(f"✅ Обновлен профиль пользователя: {telegram_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления профиля: {e}")
            return False
    
    def delete_user_profile(self, telegram_id: int) -> bool:
        """Удаление профиля пользователя"""
        try:
            # Удаляем лайки
            self._execute_query(
                "DELETE FROM likes WHERE from_user_id = ? OR to_user_id = ?",
                (telegram_id, telegram_id)
            )
            
            # Удаляем матчи
            self._execute_query(
                "DELETE FROM matches WHERE user1_id = ? OR user2_id = ?",
                (telegram_id, telegram_id)
            )
            
            # Удаляем пользователя
            self._execute_query(
                "DELETE FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            
            logger.info(f"🗑️ Удален профиль пользователя: {telegram_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления профиля: {e}")
            return False
    
    def get_potential_matches(self, user_id: int, rating_filter: str = None, 
                            position_filter: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение потенциальных совпадений с фильтрами"""
        user = self.get_user(user_id)
        if not user:
            return []
        
        # Базовый запрос
        query = '''
            SELECT * FROM users 
            WHERE telegram_id != ? 
            AND game = ?
            AND is_active = 1
            AND name IS NOT NULL
            AND telegram_id NOT IN (
                SELECT to_user_id FROM likes WHERE from_user_id = ?
            )
        '''
        params = [user_id, user['game'], user_id]
        
        # Добавляем фильтр по рейтингу
        if rating_filter:
            query += " AND rating = ?"
            params.append(rating_filter)
        
        # Добавляем фильтр по позиции
        if position_filter and position_filter != "any":
            query += " AND (positions LIKE ? OR positions LIKE ?)"
            params.extend([f'%"{position_filter}"%', f'%"any"%'])
        
        query += " ORDER BY RANDOM() LIMIT ?"
        params.append(limit)
        
        result = self._execute_query(query, tuple(params))
        
        users = []
        for row in result:
            user_dict = dict(row)
            # Парсим позиции
            if user_dict['positions']:
                try:
                    user_dict['positions'] = json.loads(user_dict['positions'])
                except:
                    user_dict['positions'] = []
            else:
                user_dict['positions'] = []
            users.append(user_dict)
        
        return users
    
    def add_like(self, from_user_id: int, to_user_id: int) -> bool:
        """Добавление лайка. Возвращает True если это взаимный лайк"""
        try:
            # Проверяем, не существует ли уже такой лайк
            existing_like = self._execute_query(
                "SELECT 1 FROM likes WHERE from_user_id = ? AND to_user_id = ?",
                (from_user_id, to_user_id)
            )
            
            if existing_like:
                logger.warning(f"⚠️ Лайк уже существует: {from_user_id} -> {to_user_id}")
                # Проверяем есть ли обратный лайк для определения матча
                mutual_like = self._execute_query(
                    "SELECT 1 FROM likes WHERE from_user_id = ? AND to_user_id = ?",
                    (to_user_id, from_user_id)
                )
                return bool(mutual_like)
            
            # Добавляем лайк
            result = self._execute_query(
                "INSERT INTO likes (from_user_id, to_user_id) VALUES (?, ?)",
                (from_user_id, to_user_id)
            )
            
            if not result:
                logger.error(f"❌ Не удалось добавить лайк: {from_user_id} -> {to_user_id}")
                return False
            
            # Проверяем взаимный лайк
            mutual_like = self._execute_query(
                "SELECT 1 FROM likes WHERE from_user_id = ? AND to_user_id = ?",
                (to_user_id, from_user_id)
            )
            
            if mutual_like:
                # Создаем матч
                user1_id = min(from_user_id, to_user_id)
                user2_id = max(from_user_id, to_user_id)
                
                # Используем INSERT OR IGNORE чтобы избежать дублирования матчей
                self._execute_query(
                    "INSERT OR IGNORE INTO matches (user1_id, user2_id) VALUES (?, ?)",
                    (user1_id, user2_id)
                )
                
                logger.info(f"💖 Создан матч: {from_user_id} <-> {to_user_id}")
                return True
            
            logger.info(f"👍 Лайк: {from_user_id} -> {to_user_id}")
            return False
            
        except Exception as e:
            logger.error(f"Ошибка добавления лайка: {e}")
            return False
    
    def get_users_who_liked_me(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение пользователей, которые лайкнули меня"""
        query = '''
            SELECT u.* FROM users u
            JOIN likes l ON u.telegram_id = l.from_user_id
            WHERE l.to_user_id = ?
            AND NOT EXISTS (
                SELECT 1 FROM likes l2 
                WHERE l2.from_user_id = ? AND l2.to_user_id = u.telegram_id
            )
            ORDER BY l.created_at DESC
        '''
        
        result = self._execute_query(query, (user_id, user_id))
        
        users = []
        for row in result:
            user_dict = dict(row)
            # Парсим позиции
            if user_dict['positions']:
                try:
                    user_dict['positions'] = json.loads(user_dict['positions'])
                except:
                    user_dict['positions'] = []
            else:
                user_dict['positions'] = []
            users.append(user_dict)
        
        return users
    
    def get_matches(self, user_id: int) -> List[Dict[str, Any]]:
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
            user_dict = dict(row)
            # Парсим позиции
            if user_dict['positions']:
                try:
                    user_dict['positions'] = json.loads(user_dict['positions'])
                except:
                    user_dict['positions'] = []
            else:
                user_dict['positions'] = []
            users.append(user_dict)
        
        return users
    
    def get_stats(self) -> Dict[str, int]:
        """Получение статистики"""
        stats = {}
        
        # Всего пользователей
        total_users = self._execute_query("SELECT COUNT(*) as count FROM users")
        stats['total_users'] = total_users[0]['count'] if total_users else 0
        
        # По играм
        dota_users = self._execute_query("SELECT COUNT(*) as count FROM users WHERE game = 'dota'")
        stats['dota_users'] = dota_users[0]['count'] if dota_users else 0
        
        cs_users = self._execute_query("SELECT COUNT(*) as count FROM users WHERE game = 'cs'")
        stats['cs_users'] = cs_users[0]['count'] if cs_users else 0
        
        # Активные пользователи (последние 7 дней)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        active_users = self._execute_query(
            "SELECT COUNT(*) as count FROM users WHERE last_activity > ?", 
            (week_ago,)
        )
        stats['active_users'] = active_users[0]['count'] if active_users else 0
        
        # Матчи
        total_matches = self._execute_query("SELECT COUNT(*) as count FROM matches WHERE is_active = 1")
        stats['total_matches'] = total_matches[0]['count'] if total_matches else 0
        
        # Лайки за сегодня
        today = datetime.now().strftime('%Y-%m-%d')
        today_likes = self._execute_query(
            "SELECT COUNT(*) as count FROM likes WHERE DATE(created_at) = ?", 
            (today,)
        )
        stats['today_likes'] = today_likes[0]['count'] if today_likes else 0
        
        return stats
    
    def update_last_activity(self, telegram_id: int):
        """Обновление времени последней активности"""
        self._execute_query(
            "UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE telegram_id = ?",
            (telegram_id,)
        )