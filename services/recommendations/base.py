#!/usr/bin/env python3
"""
Базовый класс для сервисов рекомендаций
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime  # ДОБАВИЛИ datetime

from services.weather.openweather import OpenWeatherService
from services.weather.models import WeatherForecast
from locales.manager import LocaleManager
from core.logger import logger


class BaseRecommendationService(ABC):
    """Базовый класс для всех сервисов рекомендаций"""
    
    def __init__(self, weather_service: OpenWeatherService, locale_manager: LocaleManager):
        self.weather_service = weather_service
        self.locale = locale_manager
        self.cache = {}
        self.cache_timeout = 3600  # 1 час
    
    @abstractmethod
    def get_recommendation(self, city: str) -> Dict[str, Any]:
        """
        Возвращает рекомендацию для указанного города.
        
        Args:
            city: Название города
            
        Returns:
            Словарь с результатом:
            - success: bool - успех операции
            - recommendation: str - текст рекомендации
            - city: str - город
            - data: Dict - дополнительные данные
        """
        pass
    
    def _get_weather_data(self, city: str) -> Optional[WeatherForecast]:
        """Получает данные о погоде с кэшированием"""
        cache_key = self._get_cache_key(city)
        
        # Проверяем кэш
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (timestamp.timestamp() + self.cache_timeout) > datetime.now().timestamp():  # ИСПРАВИЛИ: datetime.now()
                return cached_data
        
        # Получаем новые данные
        forecast = self.weather_service.get_weather_forecast(city, days=3)
        if forecast:
            self.cache[cache_key] = (forecast, datetime.now())  # ИСПРАВИЛИ: datetime.now()
        
        return forecast
    
    def _get_cache_key(self, city: str) -> str:
        """Генерирует ключ для кэша"""
        return f"{city}_{self.__class__.__name__}"
