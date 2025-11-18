#!/usr/bin/env python3
"""
Сервис рекомендаций по шинам и шиномонтажу
"""

from typing import Dict, Any, List
from datetime import datetime

from .base import BaseRecommendationService
from services.weather.models import WeatherForecast, ForecastDay
from utils.date_utils import get_current_timestamp
from utils.text_utils import translate_weather_conditions
from core.logger import logger


class TireRecommendationService(BaseRecommendationService):
    """Сервис рекомендаций по шинам и шиномонтажу"""
    
    def get_recommendation(self, city: str) -> Dict[str, Any]:
        """
        Возвращает рекомендацию по шинам для указанного города.
        
        Логика рекомендаций:
        - Сезонная смена: летняя/зимняя резина
        - Давление в шинах: рекомендации по температуре
        - Шиномонтаж: рекомендации по погодным условиям
        
        Args:
            city: Название города
            
        Returns:
            Словарь с результатом:
            - success: bool - успех операции
            - recommendation: str - текст рекомендации
            - city: str - город
            - data: Dict - дополнительные данные
        """
        try:
            forecast = self._get_weather_data(city)
            
            if not forecast:
                return {
                    'success': False,
                    'recommendation': self.locale.get_message('weather_service_error'),
                    'city': city,
                    'data': {}
                }
            
            # Анализируем условия для шин
            analysis = self._analyze_tire_conditions(forecast)
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
            logger.error(f"❌ Ошибка в сервисе рекомендаций по шинам: {e}")
            return {
                'success': False,
                'recommendation': self.locale.get_message('service_unavailable'),
                'city': city,
                'data': {}
            }
    
    def _analyze_tire_conditions(self, forecast: WeatherForecast) -> Dict[str, Any]:
        """Анализирует условия для рекомендаций по шинам"""
        current_temp = forecast.current.temperature
        today = forecast.get_today_forecast()
        tomorrow = forecast.get_tomorrow_forecast()
        
        # Определяем сезонность
        if current_temp < 5:
            season = 'winter'
            season_emoji = '❄️'
            season_text = 'зимний'
        elif current_temp > 15:
            season = 'summer' 
            season_emoji = '☀️'
            season_text = 'летний'
        else:
            season = 'transition'
            season_emoji = '🔄'
            season_text = 'переходный'
        
        # Проверяем, нужно ли менять резину
        change_recommended = self._should_change_tires(season, forecast)
        
        # Рекомендации по давлению
        pressure_recommendation = self._get_pressure_recommendation(current_temp)
        
        # Рекомендации по шиномонтажу
        service_recommendation = self._get_service_recommendation(forecast)
        
        # Оценка срочности
        urgency = self._calculate_urgency(season, forecast)
        
        return {
            'season': season,
            'season_emoji': season_emoji,
            'season_text': season_text,
            'change_recommended': change_recommended,
            'pressure_recommendation': pressure_recommendation,
            'service_recommendation': service_recommendation,
            'urgency': urgency,
            'current_temperature': current_temp
        }
    
    def _should_change_tires(self, season: str, forecast: WeatherForecast) -> bool:
        """Определяет, рекомендуется ли смена шин"""
        # Если сейчас зима и температура ниже 5, то зимняя резина
        # Если лето и температура выше 15, то летняя
        # В переходный период (5-15) смотрим прогноз на неделю
        if season == 'winter':
            # Проверяем, что в ближайшие дни не ожидается потепление выше 7
            for day in forecast.daily[:3]:
                if day.temperature_max > 7:
                    return False
            return True
        elif season == 'summer':
            # Проверяем, что в ближайшие дни не ожидается похолодание ниже 10
            for day in forecast.daily[:3]:
                if day.temperature_min < 10:
                    return False
            return True
        else:
            # В переходный период не рекомендуем смену, если нет устойчивого тренда
            return False
    
    def _get_pressure_recommendation(self, temperature: float) -> str:
        """Возвращает рекомендацию по давлению в шинах"""
        # При понижении температуры давление падает, и наоборот
        if temperature < 0:
            return "⚠️ Проверьте давление: при морозе оно снижается"
        elif temperature > 25:
            return "🌡️ Будьте осторожны: в жару давление может повыситься"
        else:
            return "✅ Давление в норме"
    
    def _get_service_recommendation(self, forecast: WeatherForecast) -> str:
        """Возвращает рекомендацию по шиномонтажу"""
        # Если ожидается дождь или снег, не рекомендуется шиномонтаж
        today = forecast.get_today_forecast()
        if today and today.precipitation_amount > 0:
            return "❌ Сегодня не лучшее время для шиномонтажа из-за осадков"
        else:
            return "✅ Хорошие условия для шиномонтажа"
    
    def _calculate_urgency(self, season: str, forecast: WeatherForecast) -> str:
        """Определяет срочность рекомендаций"""
        current_temp = forecast.current.temperature
        
        if season == 'winter' and current_temp < 0:
            return "high"  # Высокая срочность - уже морозы
        elif season == 'summer' and current_temp > 20:
            return "high"  # Высокая срочность - уже жара
        elif (season == 'winter' and current_temp < 3) or (season == 'summer' and current_temp > 15):
            return "medium"  # Средняя срочность - скоро смена
        else:
            return "low"  # Низкая срочность
    
    def _build_recommendation_text(self, city: str, analysis: Dict[str, Any], forecast: WeatherForecast) -> str:
        """Строит текст рекомендации по шинам"""
        condition_ru = translate_weather_conditions(forecast.current.condition)
        temperature = round(forecast.current.temperature)
        
        # Определяем основной совет по сезону
        if analysis['change_recommended']:
            if analysis['season'] == 'winter':
                season_advice = f"{analysis['season_emoji']} Рекомендуется переход на зимнюю резину"
            else:
                season_advice = f"{analysis['season_emoji']} Рекомендуется переход на летнюю резину"
        else:
            season_advice = f"{analysis['season_emoji']} Сезонная смена шин не требуется"
        
        # Определяем срочность
        urgency_text = ""
        if analysis['urgency'] == "high":
            urgency_text = "\n🚨 *Срочно!* Рекомендуем выполнить в ближайшее время"
        elif analysis['urgency'] == "medium":
            urgency_text = "\n⚠️ *Внимание!* Рекомендуем запланировать на неделю"
        
        return self.locale.get_message(
            'tire_recommendation',
            city=city,
            condition=condition_ru,
            temperature=temperature,
            season_advice=season_advice,
            pressure_recommendation=analysis['pressure_recommendation'],
            service_recommendation=analysis['service_recommendation'],
            urgency_text=urgency_text,
            timestamp=get_current_timestamp()
        )
