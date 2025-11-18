#!/usr/bin/env python3
"""
Сервис дорожных условий и рекомендаций по вождению с интеграцией DeepSeek AI
"""

from typing import Dict, Any, List
from datetime import datetime

from .base import BaseRecommendationService
from services.weather.models import WeatherForecast
from utils.date_utils import get_current_timestamp
from utils.text_utils import translate_weather_conditions, format_wind_speed, format_precipitation
from core.logger import logger

# Импортируем DeepSeek сервис
try:
    from services.ai.deepseek_service import DeepSeekService
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False
    logger.warning("❌ DeepSeekService недоступен")


class RoadConditionService(BaseRecommendationService):
    """Сервис дорожных условий и рекомендаций по вождению с AI"""
    
    def __init__(self, weather_service, locale_manager, deepseek_api_key: str = None):
        super().__init__(weather_service, locale_manager)
        self.deepseek_service = None
        
        if DEEPSEEK_AVAILABLE and deepseek_api_key:
            try:
                self.deepseek_service = DeepSeekService(deepseek_api_key)
                logger.info("✅ DeepSeekService инициализирован для дорожных условий")
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации DeepSeekService: {e}")
                self.deepseek_service = None
    
    def get_recommendation(self, city: str) -> Dict[str, Any]:
        """
        Возвращает рекомендацию по дорожным условиям для указанного города.
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
            
            # Анализируем дорожные условия
            analysis = self._analyze_road_conditions(forecast)
            
            # Если доступен AI, получаем улучшенную рекомендацию
            ai_recommendation = None
            if self.deepseek_service and self.deepseek_service.is_available():
                weather_data = self._prepare_weather_data(forecast, city, analysis)
                ai_recommendation = self.deepseek_service.get_recommendation(weather_data, "roads")
            
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
            logger.error(f"❌ Ошибка в сервисе дорожных условий: {e}")
            return {
                'success': False,
                'recommendation': self.locale.get_message('service_unavailable'),
                'city': city,
                'data': {}
            }
    
    def _analyze_road_conditions(self, forecast: WeatherForecast) -> Dict[str, Any]:
        """Анализирует дорожные условия"""
        current = forecast.current
        today = forecast.get_today_forecast()
        
        # Определяем основные риски
        risks = self._get_road_risks(forecast)
        
        # Советы по вождению
        driving_tips = self._get_driving_tips(risks)
        
        # Общая оценка условий
        condition_score = self._calculate_condition_score(risks)
        
        # Уровень опасности
        danger_level = self._get_danger_level(risks, current)
        
        return {
            'risks': risks,
            'driving_tips': driving_tips,
            'condition_score': condition_score,
            'danger_level': danger_level,
            'current_temperature': current.temperature,
            'precipitation': today.precipitation_amount if today else 0,
            'wind_speed': current.wind_speed,
            'visibility': current.visibility
        }
    
    def _get_road_risks(self, forecast: WeatherForecast) -> List[str]:
        """Определяет риски на дорогах"""
        risks = []
        current = forecast.current
        today = forecast.get_today_forecast()
        
        # Гололед
        if current.temperature < 2 and (current.condition in ['Rain', 'Drizzle', 'Freezing rain'] or (today and today.precipitation_amount > 0)):
            risks.append('black_ice')
        
        # Снегопад
        if current.condition == 'Snow' or (today and today.precipitation_amount > 5):
            risks.append('snow')
        
        # Дождь
        if current.condition in ['Rain', 'Drizzle'] or (today and today.precipitation_amount > 0):
            risks.append('rain')
        
        # Туман
        if current.condition in ['Fog', 'Mist']:
            risks.append('fog')
        
        # Сильный ветер
        if current.wind_speed > 10:
            risks.append('strong_wind')
        
        # Плохая видимость
        if current.visibility < 1000:
            risks.append('poor_visibility')
        
        return risks
    
    def _get_driving_tips(self, risks: List[str]) -> List[str]:
        """Возвращает советы по вождению на основе рисков"""
        tips = []
        
        if 'black_ice' in risks:
            tips.append("⚠️ Возможен гололед - снизьте скорость и избегайте резких маневров")
        if 'snow' in risks:
            tips.append("❄️ Снегопад - используйте зимнюю резину, держите дистанцию")
        if 'rain' in risks:
            tips.append("🌧️ Дождь - включите фары, уменьшите скорость")
        if 'fog' in risks:
            tips.append("🌫️ Туман - включите противотуманные фары, снизьте скорость")
        if 'strong_wind' in risks:
            tips.append("💨 Сильный ветер - крепче держите руль, будьте осторожны на открытых участках")
        if 'poor_visibility' in risks:
            tips.append("👁️ Плохая видимость - включите фары, увеличьте дистанцию")
        
        if not tips:
            tips.append("✅ Дорожные условия хорошие - безопасной дороги!")
        
        return tips
    
    def _calculate_condition_score(self, risks: List[str]) -> int:
        """Вычисляет оценку дорожных условий (1-5, где 5 - отлично)"""
        if not risks:
            return 5
        elif len(risks) == 1:
            return 4
        elif len(risks) == 2:
            return 3
        elif len(risks) == 3:
            return 2
        else:
            return 1
    
    def _get_danger_level(self, risks: List[str], current_weather) -> str:
        """Определяет уровень опасности"""
        if not risks:
            return "low"
        
        # Высокая опасность при гололеде, сильном снегопаде или очень плохой видимости
        high_risk_conditions = ['black_ice']
        if any(risk in high_risk_conditions for risk in risks) or current_weather.visibility < 500:
            return "high"
        elif len(risks) >= 2:
            return "medium"
        else:
            return "low"
    
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
                'wind_speed': forecast.current.wind_speed,
                'visibility': forecast.current.visibility
            },
            'forecast': forecast_data,
            'risks': analysis['risks'],
            'danger_level': analysis['danger_level'],
            'condition_score': analysis['condition_score']
        }
    
    def _build_ai_recommendation_text(self, city: str, analysis: Dict[str, Any], 
                                    ai_recommendation: str, forecast: WeatherForecast) -> str:
        """Строит рекомендацию с использованием AI"""
        condition_ru = translate_weather_conditions(forecast.current.condition)
        temperature = round(forecast.current.temperature)
        
        base_text = f"🛣 *Умная рекомендация по дорожным условиям для {city}*\n\n"
        base_text += f"🌤️ Сейчас: {condition_ru}, {temperature}°C\n\n"
        base_text += "🤖 *Рекомендация AI-эксперта:*\n\n"
        base_text += f"{ai_recommendation}\n\n"
        base_text += f"_Обновлено: {get_current_timestamp()}_"
        
        return base_text
    
    def _build_recommendation_text(self, city: str, analysis: Dict[str, Any], forecast: WeatherForecast) -> str:
        """Строит текст рекомендации по дорожным условиям"""
        condition_ru = translate_weather_conditions(forecast.current.condition)
        temperature = round(forecast.current.temperature)
        
        # Формируем список советов
        tips_text = "\n".join([f"• {tip}" for tip in analysis['driving_tips']])
        
        # Оценка условий
        score = analysis['condition_score']
        if score >= 4:
            condition_emoji = "✅"
            condition_text = "Отличные"
        elif score >= 3:
            condition_emoji = "⚠️"
            condition_text = "Удовлетворительные"
        else:
            condition_emoji = "❌"
            condition_text = "Сложные"
        
        # Уровень опасности
        danger_text = ""
        if analysis['danger_level'] == "high":
            danger_text = "\n🚨 *ВЫСОКИЙ УРОВЕНЬ ОПАСНОСТИ* - будьте предельно осторожны!"
        elif analysis['danger_level'] == "medium":
            danger_text = "\n⚠️ *Повышенная осторожность* - условия требуют внимания"
        
        return self.locale.get_message(
            'road_conditions',
            city=city,
            condition=condition_ru,
            temperature=temperature,
            condition_emoji=condition_emoji,
            condition_text=condition_text,
            tips_text=tips_text,
            danger_text=danger_text,
            timestamp=get_current_timestamp()
        )
