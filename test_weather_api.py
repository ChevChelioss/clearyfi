#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/data/data/com.termux/files/home/projects/clearyfi')

from services.weather.weather_api_client import WeatherAPIClient
from config.settings import settings

print("=== ТЕСТ WEATHER API ===")
print(f"API Key exists: {bool(OPENWEATHER_API_KEY)}")

try:
    # Пробуем разные способы создания клиента
    print("Способ 1: С передачей API ключа")
    client1 = WeatherAPIClient(api_key=settings.OPENWEATHER_API_KEY)
    print("✅ Клиент создан успешно")
    
    print("Способ 2: Без передачи API ключа (если он берется из настроек)")
    try:
        client2 = WeatherAPIClient()
        print("✅ Клиент создан без явной передачи ключа")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тестируем получение прогноза
    print("Тестируем получение прогноза для Тюмень...")
    forecast = client1.get_forecast("Тюмень")
    if forecast:
        print("✅ Прогноз получен успешно!")
        print(f"Количество периодов: {len(forecast.get('list', []))}")
    else:
        print("❌ Не удалось получить прогноз")
        
except Exception as e:
    print(f"❌ Критическая ошибка: {e}")
    import traceback
    traceback.print_exc()
