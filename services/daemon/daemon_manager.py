import sqlite3
import os
from datetime import datetime

DB_PATH = "services/storage/subscribers.db"

class DaemonManager:
    @staticmethod
    def init_settings():
        """Создаёт таблицу настроек демона"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daemon_settings (
                id INTEGER PRIMARY KEY,
                interval_hours INTEGER DEFAULT 6,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Одна строка настроек по умолчанию
        cursor.execute("SELECT * FROM daemon_settings WHERE id = 1")
        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO daemon_settings (id, interval_hours) 
                VALUES (1, 6)
            """)
        
        conn.commit()
        conn.close()

    @staticmethod
    def get_interval():
        """Получаем интервал проверки"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT interval_hours FROM daemon_settings WHERE id=1")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 6
