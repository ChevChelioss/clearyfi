#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/data/data/com.termux/files/home/projects/clearyfi')

from services.weather.weather_api_client import WeatherAPIClient
from core.weather_analyzer import WeatherAnalyzer
from core.recommendation_engine import RecommendationEngine
from config.settings import settings

print("=== ТЕСТ РЕКОМЕНДАЦИЙ ===")

try:
    # Получаем прогноз
    weather_client = WeatherAPIClient(api_key=settings.OPENWEATHER_API_KEY)
    forecast = weather_client.get_forecast("Тюмень")
    
    if forecast:
        print("✅ Прогноз получен")
        
        # Анализируем
        analyzer = WeatherAnalyzer(forecast)
        days = analyzer.days
        events = analyzer.get_events()
        
        print(f"📅 Дней проанализировано: {len(days)}")
        print(f"📊 Событий найдено: {len(events)}")
        
        # Генерируем рекомендацию
        recommendation = RecommendationEngine().build_forecast_summary(days, events)
        print(f"📝 Рекомендация сгенерирована: {len(recommendation)} символов")
        print("\n" + "="*50)
        print(recommendation)
        print("="*50)
    else:
        print("❌ Не удалось получить прогноз")
        
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
