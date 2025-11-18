#!/usr/bin/env python3
"""
Тестовый скрипт для проверки сервисов
"""

import os
import sys

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import Config
from services.weather.openweather import OpenWeatherService
from services.recommendations.wash import WashRecommendationService
from locales.manager import LocaleManager

def test_weather_service():
    """Тестирует погодный сервис"""
    print("🧪 Тестируем погодный сервис...")
    
    try:
        config = Config()
        weather_service = OpenWeatherService(config.weather.api_key)
        
        # Тестируем Москву
        weather = weather_service.get_current_weather("Москва")
        
        if weather:
            print(f"✅ Погодный сервис работает!")
            print(f"🌡 Температура в Москве: {weather.temperature}°C")
            print(f"☁️ Состояние: {weather.condition}")
        else:
            print("❌ Не удалось получить данные о погоде")
            
    except Exception as e:
        print(f"❌ Ошибка в погодном сервисе: {e}")

def test_wash_recommendation():
    """Тестирует сервис рекомендаций по мойке"""
    print("\n🧪 Тестируем сервис рекомендаций по мойке...")
    
    try:
        config = Config()
        locale = LocaleManager("ru")
        weather_service = OpenWeatherService(config.weather.api_key)
        wash_service = WashRecommendationService(weather_service, locale)
        
        result = wash_service.get_recommendation("Москва")
        
        if result["success"]:
            print("✅ Сервис рекомендаций работает!")
            print(f"📝 Рекомендация: {result['recommendation'][:100]}...")
        else:
            print(f"❌ Ошибка в сервисе рекомендаций: {result['recommendation']}")
            
    except Exception as e:
        print(f"❌ Ошибка в сервисе рекомендаций: {e}")

if __name__ == "__main__":
    print("🚀 Запускаем тестирование сервисов ClearyFi...")
    test_weather_service()
    test_wash_recommendation()
    print("\n🎯 Тестирование завершено!")
