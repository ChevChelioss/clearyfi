#!/usr/bin/env python3
"""
Диагностика системы рекомендаций
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.location.city_normalizer import CityNormalizer
from services.weather.weather_service import WeatherService
from services.notifications.recommendation_builder import RecommendationBuilder
from core.database import Database

def test_recommendations():
    print("🔍 ТЕСТ СИСТЕМЫ РЕКОМЕНДАЦИЙ")
    print("=" * 50)
    
    # Тестовые города
    test_cities = ["Москва", "Екатеринбург", "Санкт-Петербург"]
    
    for city in test_cities:
        print(f"\n🏙️ Тестируем город: {city}")
        print("-" * 30)
        
        # Проверяем нормализацию
        normalized = CityNormalizer.normalize(city)
        print(f"✅ Нормализован: {normalized}")
        
        # Проверяем погоду
        weather = WeatherService.get_weather_data(normalized)
        print(f"🌤️ Данные погоды: {'✅' if weather else '❌'}")
        
        if weather:
            print(f"   Температура: {weather.get('temperature', 'N/A')}°C")
            print(f"   Осадки: {weather.get('precipitation', 'N/A')}")
        
        # Тестируем рекомендации
        wash_rec = RecommendationBuilder.build_wash_recommendation(normalized)
        tire_rec = RecommendationBuilder.build_tire_recommendation(normalized)
        road_rec = RecommendationBuilder.build_road_conditions(normalized)
        
        print(f"🚗 Рекомендация мойки: {'✅' if wash_rec else '❌'}")
        print(f"🛞 Рекомендация шин: {'✅' if tire_rec else '❌'}")
        print(f"🛣 Дорожные условия: {'✅' if road_rec else '❌'}")

if __name__ == "__main__":
    test_recommendations()
