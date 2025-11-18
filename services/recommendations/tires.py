#!/usr/bin/env python3
"""
Сервис рекомендаций по шинам и шиномонтажу с интеграцией DeepSeek AI
"""

from typing import Dict, Any, List
from datetime import datetime

from .base import BaseRecommendationService
from services.weather.models import WeatherForecast, ForecastDay
from utils.date_utils import get_current_timestamp
from utils.text_utils import translate_weather_conditions
from core.logger import logger

# Импортируем DeepSeek сервис
try:
    from services.ai.deepseek_service import DeepSeekService
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False
    logger.warning("❌ DeepSeekService недоступен")


class TireRecommendationService(BaseRecommendationService):
    """Сервис рекомендаций по шинам и шиномонтажу с AI"""
    
    def __init__(self, weather_service, locale_manager, deepseek_api_key: str = None):
        super().__init__(weather_service, locale_manager)
        self.deepseek_service = None
        
        if DEEPSEEK_AVAILABLE and deepseek_api_key:
            try:
                self.deepseek_service = DeepSeekService(deepseek_api_key)
                logger.info("✅ DeepSeekService инициализирован для рекомендаций по шинам")
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации DeepSeekService: {e}")
                self.deepseek_service = None
    
    def get_recommendation(self, city: str) -> Dict[str, Any]:
        """
        Возвращает рекомендацию по шинам для указанного города.
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
            
            # Если доступен AI, получаем улучшенную рекомендацию
            ai_recommendation = None
            if self.deepseek_service and self.deepseek_service.is_available():
                weather_data = self._prepare_weather_data(forecast, city, analysis)
                ai_recommendation = self.deepseek_service.get_recommendation(weather_data, "tires")
            
            # Строим финальную рекомендацию
            if ai_recommendation:
                recommendation_text = self._build_ai_recommendation_text(city, analysis, ai_recommendation, forecast)
            else:
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
                    'temperature': forecast.current.temperature,
                    'ai_enhanced': ai_recommendation is not None
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
        
        # Определяем сезонность
        if current_temp < 5:
            season = 'winter'
            season_emoji = '❄️'
            season_text = 'зимний'
            change_recommended = True
        elif current_temp > 15:
            season = 'summer' 
            season_emoji = '☀️'
            season_text = 'летний'
            change_recommended = True
        else:
            season = 'transition'
            season_emoji = '🔄'
            season_text = 'переходный'
            change_recommended = False
        
        # Рекомендации по давлению
        if current_temp < 0:
            pressure_recommendation = "⚠️ Проверьте давление: при морозе оно снижается"
        elif current_temp > 25:
            pressure_recommendation = "🌡️ Будьте осторожны: в жару давление может повыситься"
        else:
            pressure_recommendation = "✅ Давление в норме"
        
        # Рекомендации по шиномонтажу
        if today and today.precipitation_amount > 0:
            service_recommendation = "❌ Сегодня не лучшее время для шиномонтажа из-за осадков"
        else:
            service_recommendation = "✅ Хорошие условия для шиномонтажа"
        
        # Оценка срочности
        if (season == 'winter' and current_temp < 0) or (season == 'summer' and current_temp > 20):
            urgency = "high"
        elif (season == 'winter' and current_temp < 3) or (season == 'summer' and current_temp > 15):
            urgency = "medium"
        else:
            urgency = "low"
        
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
    
    def _prepare_weather_data(self, forecast: WeatherForecast, city: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Подготавливает данные о погоде для AI"""
        today = forecast.get_today_forecast()
        
        forecast_data = []
        for i, day in enumerate(forecast.daily[:3]):
            forecast_data.append({
                'day': i,
                'condition': day.condition,
                'temperature': day.temperature_day,
                'precipitation': day.precipitation_amount,
                'wind_speed': day.wind_speed
            })
        
        return {
            'city': city,
            'current': {
                'temperature': forecast.current.temperature,
                'condition': forecast.current.condition,
                'precipitation': today.precipitation_amount if today else 0,
            },
            'forecast': forecast_data,
            'season': analysis['season'],
            'change_recommended': analysis['change_recommended'],
            'urgency': analysis['urgency']
        }
    
    def _build_ai_recommendation_text(self, city: str, analysis: Dict[str, Any], 
                                    ai_recommendation: str, forecast: WeatherForecast) -> str:
        """Строит рекомендацию с использованием AI"""
        condition_ru = translate_weather_conditions(forecast.current.condition)
        temperature = round(forecast.current.temperature)
        
        base_text = f"🛞 *Умная рекомендация по шинам для {city}*\n\n"
        base_text += f"🌤️ Сейчас: {condition_ru}, {temperature}°C\n\n"
        base_text += "🤖 *Рекомендация AI-эксперта:*\n\n"
        base_text += f"{ai_recommendation}\n\n"
        base_text += f"_Обновлено: {get_current_timestamp()}_"
        
        return base_text
    
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
