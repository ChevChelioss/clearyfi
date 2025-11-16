#!/usr/bin/env python3
"""
Проверка конфигурации ClearyFi
"""

import os
import sys
from dotenv import load_dotenv

def check_configuration():
    """Проверяет все необходимые настройки"""
    
    print("🔧 ПРОВЕРКА КОНФИГУРАЦИИ CLEARYFI")
    print("=" * 50)
    
    # Загружаем .env файл
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("💡 Создайте файл .env на основе .env.example")
        return False
    
    load_dotenv()
    
    # Проверяем обязательные переменные
    required_vars = {
        'TELEGRAM_BOT_TOKEN': 'Токен Telegram бота',
        'WEATHER_API_KEY': 'API ключ OpenWeatherMap'
    }
    
    all_ok = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value and value not in ['your_telegram_bot_token_here', 'your_openweathermap_api_key_here']:
            print(f"✅ {description}: настроен")
        else:
            print(f"❌ {description}: НЕ настроен")
            all_ok = False
    
    # Проверяем опциональные переменные
    optional_vars = {
        'DATABASE_PATH': 'clearyfi.db',
        'LOG_LEVEL': 'INFO',
        'DEFAULT_TIMEZONE': '3'
    }
    
    print("\n⚙️  Опциональные настройки:")
    for var, default in optional_vars.items():
        value = os.getenv(var, default)
        print(f"   {var}: {value}")
    
    print("\n" + "=" * 50)
    
    if all_ok:
        print("🎉 ВСЕ НАСТРОЙКИ КОРРЕКТНЫ! Можно запускать приложение.")
        return True
    else:
        print("💡 Заполните отсутствующие настройки в файле .env")
        return False

if __name__ == "__main__":
    success = check_configuration()
    sys.exit(0 if success else 1)
