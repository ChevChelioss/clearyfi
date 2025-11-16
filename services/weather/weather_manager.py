#!/usr/bin/env python3
"""
WeatherManager — слой кеширования и группировки городов.
"""

import time
from typing import Dict, Optional
from services.weather.weather_api_client import WeatherAPIClient
from services.location.city_normalizer import CityNormalizer
from services.storage.subscriber_db import SubscriberDBConnection
from core.weather_analyzer import WeatherAnalyzer


class WeatherManager:
    def __init__(self, cache_ttl_minutes: int = 30):
        self.client = WeatherAPIClient()
        self.analyzer = WeatherAnalyzer()
        self.normalizer = CityNormalizer()

        self.cache_ttl = cache_ttl_minutes * 60
        self.city_cache: Dict[str, dict] = {}

    def get_weather_for_city(self, city: str, force: bool = False) -> Optional[dict]:
        """
        Получает погоду для города с кешированием
        """
        city_norm = self.normalizer.normalize(city)

        # Кеш
        if (not force) and (city_norm in self.city_cache):
            cached = self.city_cache[city_norm]
            if time.time() - cached["ts"] < self.cache_ttl:
                return cached["data"]

        # Иначе свежий запрос
        data = self.client.get_forecast(city_norm)
        if data:
            self.city_cache[city_norm] = {
                "ts": time.time(),
                "data": data
            }

        return data

    def update_all_cities_weather(self) -> Dict[str, dict]:
        """
        Обновляет погоду по всем активным городам.
        Возвращает {город: {weather, analysis}}
        """
        result = {}

        with SubscriberDBConnection() as db:
            cities = db.get_unique_active_cities()

        for city in cities:
            weather = self.get_weather_for_city(city, force=True)
            if not weather:
                continue

            analysis = self.analyzer.analyze_forecast(weather)

            result[city] = {
                "weather": weather,
                "analysis": analysis
            }

        return result

    def normalize_city(self, city: str) -> str:
        return self.normalizer.normalize(city)
