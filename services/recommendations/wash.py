#!/usr/bin/env python3
"""
Сервис рекомендаций по мойке автомобиля
"""

from typing import Dict, Any
from datetime import datetime

from .base import BaseRecommendationService
from services.weather.models import WeatherForecast, ForecastDay
from utils.date_utils import get_current_timestamp
from utils.text_utils import translate_weather_conditions
from core.logger import logger


class WashRecommendationService(BaseRecommendationService):
    """Сервис рекомендаций по мойке автомобиля"""
    
    def get_recommendation(self, city: str) -> Dict[str, Any]:
        """
        Возвращает рекомендацию по мойке автомобиля
        
        Логика рекомендаций:
        - Хорошо: нет осадков 2+ дня, температура > 5°C
        - Условно: нет осадков сегодня, но завтра возможны
        - Плохо: осадки сегодня или температура < 0°C
        """
        try:
            forecast = self._get_weather_data(city)
            
            if not forecast:
                return {
                    'success': False,
                    'recommendation': self.locale.get_error('weather_service_error'),
                    'city': city,
                    'data': {}
                }
            
            # Анализируем погодные условия
            analysis = self._analyze_wash_conditions(forecast)
            recommendation_text = self._build_recommendation_text(city, analysis, forecast)
            timestamp = get_current_timestamp()
            
            return {
                'success': True,
                'recommendation': recommendation_text,
                'city': city,
                'data': {
                    'analysis': analysis,
                    'timestamp': timestamp,
                    'weather_condition': forecast.current.condition,
                    'temperature': forecast.current.temperature
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка в сервисе рекомендаций по мойке: {e}")
            return {
                'success': False,
                'recommendation': self.locale.get_error('wash_recommendation_error'),
                'city': city,
                'data': {}
            }
    
    def _analyze_wash_conditions(self, forecast: WeatherForecast) -> Dict[str, Any]:
        """Анализирует условия для мойки"""
        today = forecast.get_today_forecast()
        tomorrow = forecast.get_tomorrow_forecast()
        
        if not today:
            return {'score': 0, 'reason': 'no_data'}
        
        # Балльная система оценки
        score = 0
        reasons = []
        
        # Температурные условия
        if today.temperature_min > 5:
            score += 2
            reasons.append('good_temperature')
        elif today.temperature_min > 0:
            score += 1
            reasons.append('acceptable_temperature')
        else:
            score -= 2
            reasons.append('low_temperature')
        
        # Осадки сегодня
        if today.precipitation_amount == 0:
            score += 3
            reasons.append('no_precipitation_today')
        else:
            score -= 3
            reasons.append('precipitation_today')
        
        # Осадки завтра
        if tomorrow and tomorrow.precipitation_amount == 0:
            score += 2
            reasons.append('no_precipitation_tomorrow')
        elif tomorrow:
            score -= 1
            reasons.append('possible_precipitation_tomorrow')
        
        # Ветер
        if today.wind_speed < 5:
            score += 1
            reasons.append('low_wind')
        elif today.wind_speed > 10:
            score -= 1
            reasons.append('high_wind')
        
        return {
            'score': score,
            'reasons': reasons,
            'today_precipitation': today.precipitation_amount,
            'tomorrow_precipitation': tomorrow.precipitation_amount if tomorrow else 0,
            'temperature': today.temperature_min
        }
    
    def _build_recommendation_text(self, city: str, analysis: Dict[str, Any], forecast: WeatherForecast) -> str:
        """Строит текст рекомендации"""
        today = forecast.get_today_forecast()
        
        if analysis['score'] >= 5:
            # Отличные условия
            condition_ru = translate_weather_conditions(forecast.current.condition)
            return self.locale.get_message(
                'wash_recommendation_excellent',
                city=city,
                condition=condition_ru,
                temperature=forecast.current.temperature,
                timestamp=get_current_timestamp()
            )
        
        elif analysis['score'] >= 2:
            # Хорошие условия
            condition_ru = translate_weather_conditions(forecast.current.condition)
            return self.locale.get_message(
                'wash_recommendation_good',
                city=city,
                condition=condition_ru,
                temperature=forecast.current.temperature,
                timestamp=get_current_timestamp()
            )
        
        elif analysis['score'] >= 0:
            # Условные условия
            condition_ru = translate_weather_conditions(forecast.current.condition)
            return self.locale.get_message(
                'wash_recommendation_conditional',
                city=city,
                condition=condition_ru,
                temperature=forecast.current.temperature,
                timestamp=get_current_timestamp()
            )
        
        else:
            # Плохие условия
            condition_ru = translate_weather_conditions(forecast.current.condition)
            return self.locale.get_message(
                'wash_recommendation_bad',
                city=city,
                condition=condition_ru,
                temperature=forecast.current.temperature,
                timestamp=get_current_timestamp()
            )
