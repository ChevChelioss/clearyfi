#!/usr/bin/env python3
"""
Менеджер базы данных ClearyFi
Управляет всеми операциями с базой данных SQLite
"""

import sqlite3
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger('DatabaseManager')


class DatabaseManager:
    """
    Менеджер для работы с базой данных SQLite.
    Обеспечивает все операции с пользователями и их настройками.
    """
    
    def __init__(self, db_path: str = 'clearyfi.db'):
        """
        Инициализация менеджера базы данных.
        
        Args:
            db_path: Путь к файлу базы данных SQLite
        """
        self.db_path = db_path
        self.connection = None
        logger.info(f"DatabaseManager инициализирован для {db_path}")

    async def initialize(self) -> bool:
        """
        Инициализирует базу данных и создает необходимые таблицы.
        
        Returns:
            True если успешно, иначе False
        """
        try:
            # Используем asyncio для выполнения в отдельном потоке
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._initialize_sync)
            logger.info("✅ База данных успешно инициализирована")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы данных: {e}")
            return False

    def _initialize_sync(self) -> None:
        """
        Синхронная версия инициализации базы данных.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Создаем таблицу пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    city TEXT,
                    notification_time TEXT DEFAULT '09:00',
                    notifications_enabled INTEGER DEFAULT 0,
                    timezone INTEGER DEFAULT 3,
                    weather_requests INTEGER DEFAULT 0,
                    notifications_received INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Создаем таблицу истории запросов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weather_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    city TEXT,
                    request_type TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Создаем таблицу отправленных уведомлений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sent_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    city TEXT,
                    notification_type TEXT,
                    message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Создаем индекс для улучшения производительности
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_notifications 
                ON users(notifications_enabled, city)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_weather_requests_user 
                ON weather_requests(user_id, timestamp)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.debug("Таблицы базы данных созданы/проверены")
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка SQLite при инициализации: {e}")
            raise

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает данные пользователя по ID.
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            Словарь с данными пользователя или None
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._get_user_sync, user_id)
        except Exception as e:
            logger.error(f"Ошибка получения пользователя {user_id}: {e}")
            return None

    def _get_user_sync(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Синхронная версия получения пользователя.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, username, city, notification_time, 
                       notifications_enabled, timezone, weather_requests,
                       notifications_received, created_at, updated_at
                FROM users 
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'user_id': row[0],
                    'username': row[1],
                    'city': row[2],
                    'notification_time': row[3],
                    'notifications_enabled': bool(row[4]),
                    'timezone': row[5],
                    'weather_requests': row[6] or 0,
                    'notifications_received': row[7] or 0,
                    'created_at': row[8],
                    'updated_at': row[9]
                }
            return None
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка SQLite при получении пользователя: {e}")
            return None

    async def create_user(self, user_id: int, username: str) -> bool:
        """
        Создает нового пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            username: Имя пользователя
            
        Returns:
            True если успешно, иначе False
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._create_user_sync, user_id, username)
        except Exception as e:
            logger.error(f"Ошибка создания пользователя {user_id}: {e}")
            return False

    def _create_user_sync(self, user_id: int, username: str) -> bool:
        """
        Синхронная версия создания пользователя.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username)
                VALUES (?, ?)
            ''', (user_id, username))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            
            if success:
                logger.info(f"Создан пользователь: {username} (ID: {user_id})")
            else:
                logger.debug(f"Пользователь уже существует: {user_id}")
                
            return success
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка SQLite при создании пользователя: {e}")
            return False

    async def update_user_city(self, user_id: int, city: str) -> bool:
        """
        Обновляет город пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            city: Новый город
            
        Returns:
            True если успешно, иначе False
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._update_user_city_sync, user_id, city)
        except Exception as e:
            logger.error(f"Ошибка обновления города для {user_id}: {e}")
            return False

    def _update_user_city_sync(self, user_id: int, city: str) -> bool:
        """
        Синхронная версия обновления города.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET city = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (city, user_id))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            
            if success:
                logger.info(f"Обновлен город для {user_id}: {city}")
                
            return success
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка SQLite при обновлении города: {e}")
            return False

    async def update_notification_settings(self, user_id: int, city: str, 
                                         notification_time: str, 
                                         notifications_enabled: bool) -> bool:
        """
        Обновляет настройки уведомлений пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            city: Город для уведомлений
            notification_time: Время уведомлений
            notifications_enabled: Включены ли уведомления
            
        Returns:
            True если успешно, иначе False
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, 
                self._update_notification_settings_sync, 
                user_id, city, notification_time, notifications_enabled
            )
        except Exception as e:
            logger.error(f"Ошибка обновления настроек для {user_id}: {e}")
            return False

    def _update_notification_settings_sync(self, user_id: int, city: str,
                                         notification_time: str,
                                         notifications_enabled: bool) -> bool:
        """
        Синхронная версия обновления настроек уведомлений.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET city = ?, notification_time = ?, 
                    notifications_enabled = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (city, notification_time, int(notifications_enabled), user_id))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            
            if success:
                logger.info(f"Обновлены настройки уведомлений для {user_id}")
                
            return success
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка SQLite при обновлении настроек: {e}")
            return False

    async def get_subscribed_users(self) -> List[Dict[str, Any]]:
        """
        Получает список пользователей, подписанных на уведомления.
        
        Returns:
            Список пользователей с настройками уведомлений
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._get_subscribed_users_sync)
        except Exception as e:
            logger.error(f"Ошибка получения подписанных пользователей: {e}")
            return []

    def _get_subscribed_users_sync(self) -> List[Dict[str, Any]]:
        """
        Синхронная версия получения подписанных пользователей.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, username, city, notification_time, timezone
                FROM users 
                WHERE notifications_enabled = 1 AND city IS NOT NULL
            ''')
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'user_id': row[0],
                    'username': row[1],
                    'city': row[2],
                    'notification_time': row[3],
                    'timezone': row[4] or 3  # По умолчанию UTC+3
                })
            
            conn.close()
            return users
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка SQLite при получении пользователей: {e}")
            return []

    async def increment_weather_requests(self, user_id: int) -> bool:
        """
        Увеличивает счетчик запросов погоды для пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            True если успешно, иначе False
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._increment_weather_requests_sync, user_id)
        except Exception as e:
            logger.error(f"Ошибка увеличения счетчика запросов для {user_id}: {e}")
            return False

    def _increment_weather_requests_sync(self, user_id: int) -> bool:
        """
        Синхронная версия увеличения счетчика запросов.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET weather_requests = COALESCE(weather_requests, 0) + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            
            return success
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка SQLite при обновлении счетчика: {e}")
            return False

    async def log_weather_request(self, user_id: int, city: str, 
                                request_type: str, success: bool = True) -> bool:
        """
        Логирует запрос погоды в историю.
        
        Args:
            user_id: ID пользователя Telegram
            city: Город запроса
            request_type: Тип запроса (current, forecast, wash)
            success: Успешен ли запрос
            
        Returns:
            True если успешно, иначе False
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, 
                self._log_weather_request_sync, 
                user_id, city, request_type, success
            )
        except Exception as e:
            logger.error(f"Ошибка логирования запроса для {user_id}: {e}")
            return False

    def _log_weather_request_sync(self, user_id: int, city: str,
                                request_type: str, success: bool) -> bool:
        """
        Синхронная версия логирования запроса.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO weather_requests 
                (user_id, city, request_type, success)
                VALUES (?, ?, ?, ?)
            ''', (user_id, city, request_type, int(success)))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            
            return success
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка SQLite при логировании запроса: {e}")
            return False

    async def log_notification(self, user_id: int, city: str,
                             notification_type: str, message: str,
                             success: bool = True) -> bool:
        """
        Логирует отправку уведомления.
        
        Args:
            user_id: ID пользователя Telegram
            city: Город уведомления
            notification_type: Тип уведомления
            message: Текст сообщения
            success: Успешно ли отправлено
            
        Returns:
            True если успешно, иначе False
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self._log_notification_sync,
                user_id, city, notification_type, message, success
            )
        except Exception as e:
            logger.error(f"Ошибка логирования уведомления для {user_id}: {e}")
            return False

    def _log_notification_sync(self, user_id: int, city: str,
                             notification_type: str, message: str,
                             success: bool) -> bool:
        """
        Синхронная версия логирования уведомления.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Обрезаем сообщение если слишком длинное
            truncated_message = message[:500] + "..." if len(message) > 500 else message
            
            cursor.execute('''
                INSERT INTO sent_notifications 
                (user_id, city, notification_type, message, success)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, city, notification_type, truncated_message, int(success)))
            
            # Также обновляем счетчик полученных уведомлений у пользователя
            if success:
                cursor.execute('''
                    UPDATE users 
                    SET notifications_received = COALESCE(notifications_received, 0) + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (user_id,))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            
            return success
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка SQLite при логировании уведомления: {e}")
            return False

    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Получает статистику пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            Словарь со статистикой пользователя
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._get_user_stats_sync, user_id)
        except Exception as e:
            logger.error(f"Ошибка получения статистики для {user_id}: {e}")
            return {}

    def _get_user_stats_sync(self, user_id: int) -> Dict[str, Any]:
        """
        Синхронная версия получения статистики пользователя.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT weather_requests, notifications_received, city, 
                       notifications_enabled, created_at
                FROM users 
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            
            # Получаем общую статистику по пользователям
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            conn.close()
            
            if row:
                return {
                    'weather_requests': row[0] or 0,
                    'notifications_received': row[1] or 0,
                    'city': row[2],
                    'notifications_enabled': bool(row[3]),
                    'created_at': row[4],
                    'total_users': total_users
                }
            return {}
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка SQLite при получении статистики: {e}")
            return {}

    async def get_system_stats(self) -> Dict[str, Any]:
        """
        Получает общую статистику системы.
        
        Returns:
            Словарь со статистикой системы
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._get_system_stats_sync)
        except Exception as e:
            logger.error(f"Ошибка получения системной статистики: {e}")
            return {}

    def _get_system_stats_sync(self) -> Dict[str, Any]:
        """
        Синхронная версия получения системной статистики.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Общее количество пользователей
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            # Активные пользователи (с уведомлениями)
            cursor.execute('SELECT COUNT(*) FROM users WHERE notifications_enabled = 1')
            active_users = cursor.fetchone()[0]
            
            # Общее количество запросов
            cursor.execute('SELECT COUNT(*) FROM weather_requests')
            total_requests = cursor.fetchone()[0]
            
            # Общее количество уведомлений
            cursor.execute('SELECT COUNT(*) FROM sent_notifications')
            total_notifications = cursor.fetchone()[0]
            
            # Популярные города
            cursor.execute('''
                SELECT city, COUNT(*) as count 
                FROM users 
                WHERE city IS NOT NULL 
                GROUP BY city 
                ORDER BY count DESC 
                LIMIT 5
            ''')
            popular_cities = [{'city': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'total_requests': total_requests,
                'total_notifications': total_notifications,
                'popular_cities': popular_cities
            }
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка SQLite при получении системной статистики: {e}")
            return {}

    async def close(self) -> None:
        """
        Закрывает соединение с базой данных.
        """
        try:
            if self.connection:
                self.connection.close()
                logger.info("Соединение с базой данных закрыто")
        except Exception as e:
            logger.error(f"Ошибка при закрытии базы данных: {e}")


# Утилитарные функции для обратной совместимости
def create_database_manager(db_path: str = 'clearyfi.db') -> DatabaseManager:
    """
    Создает и возвращает экземпляр менеджера базы данных.
    
    Args:
        db_path: Путь к файлу базы данных
        
    Returns:
        Экземпляр DatabaseManager
    """
    return DatabaseManager(db_path)


if __name__ == "__main__":
    # Тестирование базы данных
    print("Это модуль менеджера базы данных. Запустите main.py для запуска приложения.")
