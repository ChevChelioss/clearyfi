import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "subscribers.db")


# =============================================================================
# ПОТОКОБЕЗОПАСНЫЙ КЛАСС-ДИСПЕТЧЕР
# =============================================================================

class SubscriberDBConnection:
    """
    Каждый вызов открывает собственное соединение SQLite.
    Полностью потокобезопасно: соединение создаётся в том же потоке,
    в котором выполняются SQL-операции.
    """

    def __enter__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=True)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Автоматическая инициализация таблицы (если её ещё нет)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                user_id INTEGER PRIMARY KEY,
                chat_id INTEGER,
                username TEXT,
                city TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            );
        """)
        self.conn.commit()

        return self  # вернём объект как "db"

    # -------------------------------------------------------------------------

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print("❌ Ошибка в SubscriberDBConnection:", exc_val)
        self.conn.commit()
        self.conn.close()

    # =============================================================================
    # CRUD — ОПЕРАЦИИ
    # =============================================================================

    def add_or_update_user(self, user_id, chat_id, username, city=None):
        """
        Создаёт запись или обновляет существующую.
        """
        created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute("""
            INSERT INTO subscribers (user_id, chat_id, username, city, is_active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                chat_id=excluded.chat_id,
                username=excluded.username
        """, (user_id, chat_id, username, city, created_time))

    # -------------------------------------------------------------------------

    def update_user_city(self, user_id, city):
        """
        Обновляет город пользователя.
        """
        self.cursor.execute("""
            UPDATE subscribers SET city=? WHERE user_id=?
        """, (city, user_id))

    # -------------------------------------------------------------------------

    def deactivate_user(self, user_id):
        """
        Отключает подписку.
        """
        self.cursor.execute("""
            UPDATE subscribers SET is_active=0 WHERE user_id=?
        """, (user_id,))

    # -------------------------------------------------------------------------

    def activate_user(self, user_id):
        """
        Включает подписку.
        """
        self.cursor.execute("""
            UPDATE subscribers SET is_active=1 WHERE user_id=?
        """, (user_id,))

    # -------------------------------------------------------------------------

    def get_user_by_chat_id(self, chat_id):
        """
        Возвращает запись пользователя или None.
        """
        self.cursor.execute("""
            SELECT * FROM subscribers WHERE chat_id=?
        """, (chat_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    # -------------------------------------------------------------------------

    def get_all_active_users(self):
        """
        Список всех активных подписчиков — пригодится для ежедневной рассылки.
        """
        self.cursor.execute("""
            SELECT * FROM subscribers WHERE is_active=1
        """)
        rows = self.cursor.fetchall()
        return [dict(r) for r in rows]
