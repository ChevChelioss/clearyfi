#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/data/data/com.termux/files/home/projects/clearyfi')

from services.weather.weather_api_client import WeatherAPIClient
from core.weather_analyzer import WeatherAnalyzer
from config.settings import OPENWEATHER_API_KEY

print("=== ПРОВЕРКА WEATHER_ANALYZER ===")

try:
    # Получаем прогноз
    weather_client = WeatherAPIClient(api_key=OPENWEATHER_API_KEY)
    forecast = weather_client.get_forecast("Тюмень")
    
    if forecast:
        print("✅ Прогноз получен")
        
        # Создаем анализатор
        analyzer = WeatherAnalyzer(forecast)
        
        # Проверяем атрибуты и методы
        print("\n📊 Атрибуты WeatherAnalyzer:")
        for attr_name in dir(analyzer):
            if not attr_name.startswith('_'):
                attr_value = getattr(analyzer, attr_name)
                if not callable(attr_value):
                    print(f"  - {attr_name}: {type(attr_value)}")
        
        print("\n🔧 Методы WeatherAnalyzer:")
        for method_name in dir(analyzer):
            if not method_name.startswith('_') and callable(getattr(analyzer, method_name)):
                print(f"  - {method_name}()")
                
        # Проверяем конкретные методы
        print("\n🔍 Проверяем методы получения данных:")
        if hasattr(analyzer, 'get_events'):
            events = analyzer.get_events()
            print(f"✅ get_events() вернул: {type(events)}, длина: {len(events) if events else 0}")
        else:
            print("❌ get_events() не существует")
            
        # Проверяем, есть ли данные о днях
        if hasattr(analyzer, 'days'):
            print(f"✅ analyzer.days: {len(analyzer.days)} дней")
        elif hasattr(analyzer, 'get_days'):
            days = analyzer.get_days()
            print(f"✅ get_days() вернул: {len(days)} дней")
        else:
            print("❌ Не найдено способа получить данные о днях")
        
    else:
        print("❌ Не удалось получить прогноз")
        
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
