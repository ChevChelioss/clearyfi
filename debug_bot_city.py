#!/usr/bin/env python3
"""
Диагностика установки города в боте
"""

import logging
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DebugBot')

async def test_bot_city_setup():
    """Тестируем установку города через бота"""
    from bots.telegram_bot import create_bot
    from services.location.city_normalizer import CityNormalizer
    
    print("🤖 Тестирование установки города в боте")
    print("=" * 50)
    
    # Создаем бота
    bot = create_bot(
        os.getenv('TELEGRAM_BOT_TOKEN'),
        'clearyfi.db',
        os.getenv('WEATHER_API_KEY')
    )
    
    # Тестовый user_id (можно использовать ваш реальный ID из Telegram)
    test_user_id = 123456789
    
    print("1. Проверка методов бота:")
    
    # Проверяем регистрацию пользователя
    try:
        registered = await bot._register_user(test_user_id, "TestUser")
        print(f"   ✅ Регистрация пользователя: {registered}")
    except Exception as e:
        print(f"   ❌ Ошибка регистрации: {e}")
    
    # Проверяем установку города
    try:
        success = await bot._update_user_settings(
            user_id=test_user_id,
            city="Москва",
            notification_time="09:00",
            notifications_enabled=False
        )
        print(f"   ✅ Установка города: {success}")
    except Exception as e:
        print(f"   ❌ Ошибка установки города: {e}")
    
    # Проверяем получение города
    try:
        city = await bot._get_user_city(test_user_id)
        print(f"   ✅ Получение города: {city}")
    except Exception as e:
        print(f"   ❌ Ошибка получения города: {e}")
    
    print("\n2. Проверка ConversationHandler:")
    print("   Убедитесь, что в bots/telegram_bot.py:")
    print("   - ConversationHandler зарегистрирован")
    print("   - Метод _setup_city_start возвращает CITY_SELECTION")
    print("   - Метод _setup_city_process использует await для validate_city")
    
    print("\n🎯 Рекомендации по диагностике:")
    print("   1. Запустите бота: python main.py")
    print("   2. Откройте Telegram и нажмите '⚙️ Настройки'")
    print("   3. Выберите город из списка")
    print("   4. Проверьте логи в терминале")

async def main():
    await test_bot_city_setup()

if __name__ == "__main__":
    asyncio.run(main())
