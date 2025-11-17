#!/usr/bin/env python3
"""
Тестирование работы с городами
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DebugCity')

def test_city_normalizer():
    """Тестируем нормализацию городов"""
    from services.location.city_normalizer import CityNormalizer
    
    print("🧪 Тестирование CityNormalizer")
    print("=" * 50)
    
    # Тестовые города
    test_cities = ['Москва', 'Санкт-Петербург', 'Казань', 'НеизвестныйГород']
    
    for city in test_cities:
        normalized = CityNormalizer.normalize_city_name(city)
        is_popular = CityNormalizer.is_city_popular(city)
        print(f"'{city}' -> '{normalized}' (популярный: {is_popular})")
    
    print("\n🎯 Клавиатура городов:")
    keyboard = CityNormalizer.get_popular_cities_keyboard()
    print(keyboard)

async def test_weather_service():
    """Тестируем проверку городов через WeatherService"""
    from services.weather.weather_service import WeatherService
    
    print("\n🌤 Тестирование WeatherService")
    print("=" * 50)
    
    weather_service = WeatherService(os.getenv('WEATHER_API_KEY'))
    
    test_cities = ['Moscow', 'Saint Petersburg', 'InvalidCity123']
    
    for city in test_cities:
        is_valid = await weather_service.validate_city(city)
        print(f"Город '{city}' валиден: {is_valid}")

async def main():
    test_city_normalizer()
    await test_weather_service()

if __name__ == "__main__":
    asyncio.run(main())
