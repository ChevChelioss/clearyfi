# services/weather/weather_service.py
from typing import Dict, List, Optional
from services.weather.weather_api_client import WeatherAPIClient
from core.weather_analyzer import WeatherAnalyzer

class WeatherService:
    """
    Единый сервис для работы с погодными данными.
    Объединяет API клиент и анализатор для предоставления готовых данных.
    """
    
    def __init__(self, api_key: str):
        """
        Инициализация сервиса погоды.
        
        Args:
            api_key: API ключ для OpenWeatherMap
        """
        self.api_client = WeatherAPIClient(api_key)
    
    def get_city_forecast(self, city: str, days: int = 3) -> Optional[Dict]:
        """
        Получает и анализирует прогноз погоды для указанного города.
        
        Args:
            city: Название города
            days: Количество дней для прогноза (максимум 5)
            
        Returns:
            Словарь с проанализированными данными или None в случае ошибки
        """
        try:
            # Получаем сырые данные от API
            forecast = self.api_client.get_forecast(city, days)
            if not forecast:
                return None
            
            # Анализируем данные
            analyzer = WeatherAnalyzer(forecast)
            
            # Возвращаем структурированные данные
            return {
                'city': city,
                'daily_summary': analyzer.get_daily_summary(),
                'best_wash_day': analyzer.get_best_wash_day(),
                'current_weather': analyzer.get_current_weather(),
                'alerts': analyzer.get_weather_alerts(),
                'raw_data': forecast  # На случай дополнительной обработки
            }
            
        except Exception as e:
            # Логирование ошибки можно добавить здесь
            return None
    
    def validate_city(self, city: str) -> bool:
        """
        Проверяет существование города через API.
        
        Args:
            city: Название города для проверки
            
        Returns:
            True если город существует, False в противном случае
        """
        return self.api_client.is_city_valid(city)
    
    def get_immediate_forecast(self, city: str) -> Optional[Dict]:
        """
        Быстрый запрос для получения текущей погоды.
        
        Args:
            city: Название города
            
        Returns:
            Текущая погода или None в случае ошибки
        """
        try:
            forecast = self.api_client.get_forecast(city, days=1)
            if not forecast:
                return None
            
            analyzer = WeatherAnalyzer(forecast)
            return {
                'current_weather': analyzer.get_current_weather(),
                'today_forecast': analyzer.get_today_forecast(),
                'alerts': analyzer.get_weather_alerts()
            }
            
        except Exception:
            return None
