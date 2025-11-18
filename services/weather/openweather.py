#!/usr/bin/env python3
"""
Сервис для работы с OpenWeatherMap API
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List  # ДОБАВИЛИ List
from urllib.parse import quote
from collections import Counter  # ДОБАВИЛИ Counter

from core.logger import logger
from .models import WeatherData, ForecastDay, WeatherForecast


class OpenWeatherService:
    """Сервис для получения данных о погоде с OpenWeatherMap"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.session = requests.Session()
        self.session.timeout = 10
        
        logger.info("✅ OpenWeatherService инициализирован")
    
    def get_current_weather(self, city: str) -> Optional[WeatherData]:
        """
        Получает текущую погоду для города
        
        Args:
            city: Название города
            
        Returns:
            Данные о погоде или None при ошибке
        """
        try:
            url = f"{self.base_url}/weather"
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'ru'
            }
            
            logger.debug(f"Запрос погоды для города: {city}")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_current_weather(data)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка запроса погоды для {city}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка обработки данных погоды для {city}: {e}")
            return None
    
    def get_weather_forecast(self, city: str, days: int = 3) -> Optional[WeatherForecast]:
        """
        Получает прогноз погоды на несколько дней
        
        Args:
            city: Название города
            days: Количество дней прогноза (1-5)
            
        Returns:
            Прогноз погоды или None при ошибке
        """
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'ru',
                'cnt': days * 8  # 8 записей в день (каждые 3 часа)
            }
            
            logger.debug(f"Запрос прогноза для города: {city} на {days} дней")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_forecast(data, city, days)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка запроса прогноза для {city}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка обработки прогноза для {city}: {e}")
            return None
    
    def validate_city(self, city: str) -> bool:
        """
        Проверяет, существует ли город в OpenWeatherMap
        
        Args:
            city: Название города
            
        Returns:
            True если город существует
        """
        try:
            weather = self.get_current_weather(city)
            return weather is not None
        except Exception:
            return False
    
    def _parse_current_weather(self, data: Dict[str, Any]) -> WeatherData:
        """Парсит данные текущей погоды"""
        return WeatherData(
            temperature=data['main']['temp'],
            feels_like=data['main']['feels_like'],
            humidity=data['main']['humidity'],
            pressure=data['main']['pressure'],
            wind_speed=data['wind']['speed'],
            wind_direction=data['wind'].get('deg', 0),
            cloudiness=data['clouds']['all'],
            visibility=data.get('visibility', 10000),
            condition=data['weather'][0]['main'],
            description=data['weather'][0]['description'],
            icon=data['weather'][0]['icon'],
            timestamp=datetime.fromtimestamp(data['dt'])
        )
    
    def _parse_forecast(self, data: Dict[str, Any], city: str, days: int) -> WeatherForecast:
        """Парсит данные прогноза погоды"""
        # Получаем текущую погоду
        current_weather = self._parse_current_weather({
            **data['list'][0],
            'name': data['city']['name']
        })
        
        # Группируем прогноз по дням
        daily_forecasts = []
        daily_data = {}
        
        for forecast in data['list']:
            forecast_date = datetime.fromtimestamp(forecast['dt']).strftime('%Y-%m-%d')
            
            if forecast_date not in daily_data:
                daily_data[forecast_date] = {
                    'temps': [],
                    'humidity': [],
                    'wind_speed': [],
                    'conditions': [],
                    'precipitation': 0
                }
            
            daily_data[forecast_date]['temps'].append(forecast['main']['temp'])
            daily_data[forecast_date]['humidity'].append(forecast['main']['humidity'])
            daily_data[forecast_date]['wind_speed'].append(forecast['wind']['speed'])
            daily_data[forecast_date]['conditions'].append(forecast['weather'][0]['main'])
            
            # Осадки
            rain = forecast.get('rain', {}).get('3h', 0)
            snow = forecast.get('snow', {}).get('3h', 0)
            daily_data[forecast_date]['precipitation'] += rain + snow
        
        # Создаем прогноз на каждый день
        for date_str, day_data in list(daily_data.items())[:days]:
            temps = day_data['temps']
            forecast_day = ForecastDay(
                date=date_str,
                temperature_day=max(temps),
                temperature_night=min(temps),
                temperature_min=min(temps),
                temperature_max=max(temps),
                humidity=sum(day_data['humidity']) / len(day_data['humidity']),
                wind_speed=sum(day_data['wind_speed']) / len(day_data['wind_speed']),
                condition=self._get_most_common_condition(day_data['conditions']),
                description="",
                precipitation_probability=self._calculate_precipitation_probability(day_data['conditions']),
                precipitation_amount=day_data['precipitation']
            )
            daily_forecasts.append(forecast_day)
        
        return WeatherForecast(
            city=city,
            current=current_weather,
            daily=daily_forecasts,
            timezone=data['city']['timezone']
        )
    
    def _get_most_common_condition(self, conditions: List[str]) -> str:
        """Возвращает наиболее частное погодное условие"""
        return Counter(conditions).most_common(1)[0][0]  # ИСПРАВИЛИ: убрали лишний импорт внутри метода
    
    def _calculate_precipitation_probability(self, conditions: List[str]) -> float:
        """Вычисляет вероятность осадков"""
        precip_conditions = ['Rain', 'Snow', 'Drizzle', 'Thunderstorm']
        precip_count = sum(1 for condition in conditions if condition in precip_conditions)
        return precip_count / len(conditions) if conditions else 0.0
