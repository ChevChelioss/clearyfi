#!/usr/bin/env python3
"""
Скрипт для проверки и отладки базы данных
"""

import sys
import os
import tempfile

# Добавляем путь к корневой папке проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Database
from core.logger import logger


def test_database():
    """Тестирует все функции базы данных"""
    logger.info("🧪 Запуск теста базы данных...")
    
    # Создаем временный файл для тестирования вместо памяти
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        # Используем временный файл для тестирования
        db = Database(temp_db_path)
        
        # Тест 1: Добавление пользователей
        test_users = [
            (111111111, "User1"),
            (222222222, "User2"), 
            (333333333, "User3")
        ]
        
        for user_id, username in test_users:
            success = db.add_user(user_id, username)
            print(f"➕ Добавление {username}: {'✅' if success else '❌'}")
        
        # Тест 2: Обновление городов
        cities = ["Москва", "Санкт-Петербург", "Екатеринбург"]
        for i, (user_id, username) in enumerate(test_users):
            success = db.update_user_city(user_id, cities[i])
            print(f"🏙️  Город для {username}: {'✅' if success else '❌'}")
        
        # Тест 3: Включение подписок
        for user_id, username in test_users[:2]:  # Первые два пользователя
            success = db.update_user_subscription(user_id, True)
            print(f"🔔 Подписка для {username}: {'✅' if success else '❌'}")
        
        # Тест 4: Получение данных
        print("\n📊 Статистика:")
        user_count = db.get_user_count()
        subscribed_count = len(db.get_subscribed_users())
        print(f"   • Всего пользователей: {user_count}")
        print(f"   • Подписанных: {subscribed_count}")
        
        # Тест 5: Поиск по городам
        for city in cities:
            users = db.get_users_by_city(city)
            print(f"   • Пользователей в {city}: {len(users)}")
        
        # Тест 6: Проверка данных пользователей
        print("\n👤 Проверка данных пользователей:")
        for user_id, username in test_users:
            user_data = db.get_user(user_id)
            if user_data:
                print(f"   • {username}: город={user_data['city']}, подписка={user_data['notifications_enabled']}")
            else:
                print(f"   • {username}: ❌ не найден")
        
        print("\n✅ Тест базы данных завершен!")
        
    finally:
        # Удаляем временный файл
        try:
            os.unlink(temp_db_path)
            logger.info(f"✅ Временный файл базы данных удален: {temp_db_path}")
        except:
            pass


if __name__ == "__main__":
    test_database()
