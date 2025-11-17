#!/usr/bin/env python3
"""
Модели данных для погодного сервиса
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class WeatherData:
    """Данные о текущей погоде"""
    temperature: float
    feels_like: float
    humidity: float
    pressure: float
    wind_speed: float
    wind_direction: float
    cloudiness: float
    visibility: float
    condition: str
    description: str
    icon: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует в словарь для сериализации"""
        return {
            'temperature': self.temperature,
            'feels_like': self.feels_like,
            'humidity': self.humidity,
            'pressure': self.pressure,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'cloudiness': self.cloudiness,
            'visibility': self.visibility,
            'condition': self.condition,
            'description': self.description,
            'icon': self.icon,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ForecastDay:
    """Прогноз на один день"""
    date: str
    temperature_day: float
    temperature_night: float
    temperature_min: float
    temperature_max: float
    humidity: float
    wind_speed: float
    condition: str
    description: str
    precipitation_probability: float
    precipitation_amount: float


@dataclass
class WeatherForecast:
    """Полный прогноз погоды"""
    city: str
    current: WeatherData
    daily: List[ForecastDay]
    timezone: str
    
    def get_today_forecast(self) -> Optional[ForecastDay]:
        """Возвращает прогноз на сегодня"""
        if self.daily:
            return self.daily[0]
        return None
    
    def get_tomorrow_forecast(self) -> Optional[ForecastDay]:
        """Возвращает прогноз на завтра"""
        if len(self.daily) > 1:
            return self.daily[1]
        return None
