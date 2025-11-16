#!/usr/bin/env python3
"""Тест системы прогноза погоды"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from services.weather.weather_api_client import WeatherAPIClient
from core.weather_analyzer import WeatherAnalyzer
from config.settings import settings

def test_forecast_system():
    print("🧪 ТЕСТИРУЕМ СИСТЕМУ ПРОГНОЗА...")
    
    # Тестируем получение прогноза
    client = WeatherAPIClient(api_key=settings.OPENWEATHER_API_KEY)
    forecast = client.get_forecast("Москва", days=3)
    
    if forecast:
        print(f"✅ Прогноз получен: {len(forecast.get('days', []))} дней")
        
        # Тестируем анализ прогноза
        analyzer = WeatherAnalyzer()
        recommendation = analyzer.analyze_forecast(forecast)
        
        print("📊 РЕКОМЕНДАЦИИ:")
        print(recommendation)
        
        # Показываем детали по дням
        print("\n📅 ДЕТАЛИ ПРОГНОЗА:")
        for day in forecast.get('days', [])[:3]:
            print(f"  {day.get('date')}: {day.get('temp_min')}°-{day.get('temp_max')}°C, "
                  f"осадки: {day.get('precipitation_prob', 0)*100:.0f}%")
    else:
        print("❌ Не удалось получить прогноз")

if __name__ == "__main__":
    test_forecast_system()
