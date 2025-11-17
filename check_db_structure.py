#!/usr/bin/env python3
"""
Проверяет структуру базы данных
"""

import sqlite3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import logger


def check_database_structure(db_path="clearyfi.db"):
    """Проверяет структуру таблиц в базе данных"""
    logger.info(f"🔍 Проверка структуры базы данных: {db_path}")
    
    if not os.path.exists(db_path):
        logger.error(f"❌ Файл базы данных не найден: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем существование таблицы users
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        users_table = cursor.fetchone()
        
        if not users_table:
            logger.error("❌ Таблица 'users' не найдена в базе данных")
            return False
        
        logger.info("✅ Таблица 'users' существует")
        
        # Проверяем структуру таблицы users
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        logger.info("📋 Структура таблицы 'users':")
        expected_columns = {
            'user_id': 'INTEGER',
            'username': 'TEXT', 
            'city': 'TEXT',
            'notification_time': 'TEXT',
            'notifications_enabled': 'INTEGER',
            'created_at': 'TEXT',
            'updated_at': 'TEXT'
        }
        
        for column in columns:
            col_name = column[1]
            col_type = column[2]
            logger.info(f"   • {col_name} ({col_type})")
            
            if col_name in expected_columns:
                if col_type == expected_columns[col_name]:
                    logger.info(f"     ✅ Корректный тип")
                else:
                    logger.warning(f"     ⚠️  Ожидался тип {expected_columns[col_name]}, получен {col_type}")
        
        # Проверяем индексы
        cursor.execute("PRAGMA index_list(users)")
        indexes = cursor.fetchall()
        
        logger.info("📊 Индексы таблицы 'users':")
        for index in indexes:
            index_name = index[1]
            logger.info(f"   • {index_name}")
        
        conn.close()
        logger.info("✅ Структура базы данных проверена успешно")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки структуры базы данных: {e}")
        return False


if __name__ == "__main__":
    check_database_structure()
