#!/usr/bin/env python3
"""
Модуль работы с базой данных ClearyFi
"""

import sqlite3
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from core.logger import logger


class Database:
    """Класс для работы с базой данных SQLite"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Инициализирует таблицы базы данных"""
        try:
            with self._get_connection() as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        city TEXT,
                        notification_time TEXT DEFAULT '09:00',
                        notifications_enabled INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT (datetime('now')),
                        updated_at TEXT DEFAULT (datetime('now'))
                    )
                ''')
                logger.info("✅ Таблицы базы данных созданы/проверены")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
    
    def _get_connection(self):
        """Возвращает соединение с базой данных"""
        return sqlite3.connect(self.db_path)
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает пользователя по ID
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            Данные пользователя или None
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(
                    'SELECT * FROM users WHERE user_id = ?',
                    (user_id,)
                )
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения пользователя {user_id}: {e}")
            return None
    
    def create_user(self, user_id: int, username: str = None) -> bool:
        """
        Создает нового пользователя
        
        Args:
            user_id: ID пользователя Telegram
            username: Имя пользователя
            
        Returns:
            Успех операции
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR IGNORE INTO users (user_id, username, created_at, updated_at)
                    VALUES (?, ?, datetime('now'), datetime('now'))
                ''', (user_id, username))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания пользователя {user_id}: {e}")
            return False
    
    def update_user_city(self, user_id: int, city: str) -> bool:
        """
        Обновляет город пользователя
        
        Args:
            user_id: ID пользователя Telegram
            city: Название города
            
        Returns:
            Успех операции
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE users 
                    SET city = ?, updated_at = datetime('now')
                    WHERE user_id = ?
                ''', (city, user_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"❌ Ошибка обновления города для {user_id}: {e}")
            return False
    
    def get_user_city(self, user_id: int) -> Optional[str]:
        """
        Получает город пользователя
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            Название города или None
        """
        try:
            user_data = self.get_user_by_id(user_id)
            return user_data.get('city') if user_data else None
        except Exception as e:
            logger.error(f"❌ Ошибка получения города для {user_id}: {e}")
            return None
    
    def update_user_subscription(self, user_id: int, 
                               notifications_enabled: bool = None,
                               notification_time: str = None) -> bool:
        """
        Обновляет настройки подписки пользователя
        
        Args:
            user_id: ID пользователя Telegram
            notifications_enabled: Включены ли уведомления
            notification_time: Время уведомлений
            
        Returns:
            Успех операции
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                update_fields = []
                params = []
                
                if notifications_enabled is not None:
                    update_fields.append("notifications_enabled = ?")
                    params.append(1 if notifications_enabled else 0)
                
                if notification_time is not None:
                    update_fields.append("notification_time = ?")
                    params.append(notification_time)
                
                if not update_fields:
                    return False
                
                update_fields.append("updated_at = datetime('now')")
                params.append(user_id)
                
                query = f'''
                    UPDATE users 
                    SET {', '.join(update_fields)}
                    WHERE user_id = ?
                '''
                
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"❌ Ошибка обновления подписки для {user_id}: {e}")
            return False
    
    def get_users_with_notifications(self) -> List[Dict[str, Any]]:
        """
        Получает всех пользователей с включенными уведомлениями
        
        Returns:
            Список пользователей
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM users 
                    WHERE notifications_enabled = 1 AND city IS NOT NULL
                ''')
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения пользователей с уведомлениями: {e}")
            return []
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Получает всех пользователей
        
        Returns:
            Список всех пользователей
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM users')
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения всех пользователей: {e}")
            return []
