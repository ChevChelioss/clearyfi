#!/usr/bin/env python3
"""
Система базы данных для ClearyFi
Использует SQLite для хранения данных пользователей
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from core.logger import logger


class Database:
    """
    Управление базой данных ClearyFi.
    Обеспечивает надежное хранение данных пользователей.
    """
    
    def __init__(self, db_path: str = "clearyfi.db"):
        self.db_path = db_path
        self._init_db()
        logger.info(f"✅ База данных инициализирована: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Создает и возвращает соединение с базой данных"""
        conn = sqlite3.connect(self.db_path)
        # Включаем поддержку внешних ключей
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def _init_db(self) -> None:
        """Инициализирует таблицы базы данных"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
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
            
            # Индексы для ускорения поиска
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_city 
                ON users(city)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_notifications 
                ON users(notifications_enabled)
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Таблицы базы данных созданы/проверены")
            
        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка инициализации базы данных: {e}")
            raise
    
    def add_user(self, user_id: int, username: str) -> bool:
        """
        Добавляет нового пользователя в базу данных.
        
        Args:
            user_id: ID пользователя в Telegram
            username: Имя пользователя
            
        Returns:
            True если успешно, False при ошибке
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Используем INSERT OR IGNORE чтобы избежать дубликатов
            cursor.execute('''
                INSERT OR IGNORE INTO users 
                (user_id, username, created_at) 
                VALUES (?, ?, datetime('now'))
            ''', (user_id, username))
            
            conn.commit()
            conn.close()
            return True
                
        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка добавления пользователя {user_id}: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о пользователе.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Словарь с данными пользователя или None если не найден
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, username, city, notification_time, 
                       notifications_enabled, created_at, updated_at
                FROM users 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'user_id': result[0],
                    'username': result[1],
                    'city': result[2],
                    'notification_time': result[3] or '09:00',
                    'notifications_enabled': bool(result[4]),
                    'created_at': result[5],
                    'updated_at': result[6]
                }
            return None
                
        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка получения пользователя {user_id}: {e}")
            return None
    
    def get_user_city(self, user_id: int) -> Optional[str]:
        """
        Получает город пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Название города или None если не установлен
        """
        user = self.get_user(user_id)
        return user['city'] if user and user['city'] else None
    
    def update_user_city(self, user_id: int, city: str) -> bool:
        """
        Обновляет город пользователя.
        
        Args:
            user_id: ID пользователя
            city: Название города
            
        Returns:
            True если успешно, False при ошибке
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET city = ?, updated_at = datetime('now')
                WHERE user_id = ?
            ''', (city, user_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Город пользователя {user_id} обновлен: {city}")
            return True
                
        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка обновления города для {user_id}: {e}")
            return False
    
    def is_user_subscribed(self, user_id: int) -> bool:
        """
        Проверяет, подписан ли пользователь на уведомления.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если подписан, False если нет
        """
        user = self.get_user(user_id)
        return user['notifications_enabled'] if user else False
    
    def update_user_subscription(self, user_id: int, enabled: bool) -> bool:
        """
        Обновляет статус подписки пользователя.
        
        Args:
            user_id: ID пользователя
            enabled: Включена ли подписка
            
        Returns:
            True если успешно, False при ошибке
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET notifications_enabled = ?, updated_at = datetime('now')
                WHERE user_id = ?
            ''', (int(enabled), user_id))
            
            conn.commit()
            conn.close()
            
            status = "включена" if enabled else "выключена"
            logger.info(f"✅ Подписка пользователя {user_id} {status}")
            return True
                
        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка обновления подписки для {user_id}: {e}")
            return False
    
    def get_subscribed_users(self) -> List[Dict[str, Any]]:
        """
        Получает список всех подписанных пользователей.
        
        Returns:
            Список словарей с данными пользователей
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, username, city, notification_time
                FROM users 
                WHERE notifications_enabled = 1
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            users = []
            for result in results:
                users.append({
                    'user_id': result[0],
                    'username': result[1],
                    'city': result[2],
                    'notification_time': result[3] or '09:00'
                })
            
            return users
                
        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка получения подписанных пользователей: {e}")
            return []
    
    def get_user_count(self) -> int:
        """
        Возвращает общее количество пользователей.
        
        Returns:
            Количество пользователей
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else 0
                
        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка получения количества пользователей: {e}")
            return 0
    
    def get_users_by_city(self, city: str) -> List[Dict[str, Any]]:
        """
        Получает всех пользователей из определенного города.
        
        Args:
            city: Название города
            
        Returns:
            Список пользователей
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, username, notifications_enabled
                FROM users 
                WHERE city = ?
            ''', (city,))
            
            results = cursor.fetchall()
            conn.close()
            
            users = []
            for result in results:
                users.append({
                    'user_id': result[0],
                    'username': result[1],
                    'notifications_enabled': bool(result[2])
                })
            
            return users
                
        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка получения пользователей по городу {city}: {e}")
            return []

    def backup_database(self, backup_path: str) -> bool:
        """
        Создает резервную копию базы данных.
        
        Args:
            backup_path: Путь для сохранения резервной копии
            
        Returns:
            True если успешно, False при ошибке
        """
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"✅ Резервная копия создана: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка создания резервной копии: {e}")
            return False
