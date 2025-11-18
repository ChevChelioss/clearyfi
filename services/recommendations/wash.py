#!/usr/bin/env python3
"""
Сервис рекомендаций по мойке автомобиля с интеграцией DeepSeek AI
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta

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


class WashRecommendationService(BaseRecommendationService):
    """Умный сервис рекомендаций по мойке автомобиля с AI"""
    
    def __init__(self, weather_service, locale_manager, deepseek_api_key: str = None):
        super().__init__(weather_service, locale_manager)
        self.deepseek_service = None
        
        if DEEPSEEK_AVAILABLE and deepseek_api_key:
            try:
                self.deepseek_service = DeepSeekService(deepseek_api_key)
                logger.info("✅ DeepSeekService инициализирован для рекомендаций по мойке")
                
                # Тестируем соединение
                if self.deepseek_service.test_connection():
                    logger.info("✅ Соединение с DeepSeek API установлено")
                else:
                    logger.warning("⚠️ Не удалось установить соединение с DeepSeek API")
                    self.deepseek_service = None
                    
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации DeepSeekService: {e}")
                self.deepseek_service = None
    
    def get_recommendation(self, city: str) -> Dict[str, Any]:
        """
        Возвращает умную рекомендацию по мойке с использованием AI
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
            
            # Получаем базовую рекомендацию
            basic_analysis = self._analyze_wash_conditions(forecast)
            
            # Если доступен AI, получаем улучшенную рекомендацию
            ai_recommendation = None
            if self.deepseek_service and self.deepseek_service.is_available():
                weather_data = self._prepare_weather_data(forecast, city)
                ai_recommendation = self.deepseek_service.get_recommendation(weather_data, "car_wash")
            
            # Строим финальную рекомендацию
            if ai_recommendation:
                recommendation_text = self._build_ai_recommendation_text(city, basic_analysis, ai_recommendation, forecast)
            else:
                recommendation_text = self._build_recommendation_text(city, basic_analysis, forecast)
            
            timestamp = get_current_timestamp()
            
            return {
                'success': True,
                'recommendation': recommendation_text,
                'city': city,
                'data': {
                    'analysis': basic_analysis,
                    'timestamp': timestamp,
                    'weather_condition': forecast.current.condition,
                    'temperature': forecast.current.temperature,
                    'ai_enhanced': ai_recommendation is not None
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка в сервисе рекомендаций по мойке: {e}")
            return {
                'success': False,
                'recommendation': self.locale.get_message('service_unavailable'),
                'city': city,
                'data': {}
            }
    
    def _analyze_wash_conditions(self, forecast: WeatherForecast) -> Dict[str, Any]:
        """Анализирует условия для мойки с новой логикой"""
        today = forecast.get_today_forecast()
        tomorrow = forecast.get_tomorrow_forecast()
        day_after_tomorrow = forecast.daily[2] if len(forecast.daily) > 2 else None
        
        if not today:
            return {'decision': 'no_data', 'confidence': 0, 'reasons': []}
        
        reasons = []
        confidence = 0
        
        # КРИТИЧЕСКИЕ ФАКТОРЫ (автоматическое "нет")
        critical_no_factors = []
        
        # 1. Осадки сегодня - категорическое НЕТ
        if today.precipitation_amount > 0:
            critical_no_factors.append(f"❌ Сейчас {self._get_precipitation_type(today.condition)}")
        
        # 2. Сильный ветер (>10 м/с) - пыль осядет на мокрую машину
        if today.wind_speed > 10:
            critical_no_factors.append(f"💨 Сильный ветер ({today.wind_speed} м/с)")
        
        # 3. Температура ниже 0 - вода замерзнет
        if today.temperature_min < 0:
            critical_no_factors.append(f"🥶 Температура ниже нуля ({today.temperature_min}°C)")
        
        # Если есть критические факторы - сразу "нет"
        if critical_no_factors:
            return {
                'decision': 'definitely_no',
                'confidence': 95,
                'reasons': critical_no_factors,
                'next_good_day': self._find_next_good_day(forecast)
            }
        
        # ОЦЕНОЧНЫЕ ФАКТОРЫ
        positive_factors = []
        warning_factors = []
        
        # Положительные факторы
        if today.precipitation_amount == 0:
            positive_factors.append("✅ Сегодня нет осадков")
            confidence += 25
        
        if tomorrow and tomorrow.precipitation_amount == 0:
            positive_factors.append("✅ Завтра нет осадков")
            confidence += 20
        elif tomorrow:
            warning_factors.append(f"⚠️ Завтра возможны осадки")
            confidence -= 10
        
        if day_after_tomorrow and day_after_tomorrow.precipitation_amount == 0:
            positive_factors.append("✅ Послезавтра нет осадков")
            confidence += 15
        
        # Температурные условия
        if 5 <= today.temperature_min <= 30:
            positive_factors.append("✅ Комфортная температура")
            confidence += 15
        else:
            warning_factors.append(f"🌡️ Температура неидеальная ({today.temperature_min}°C)")
            confidence -= 5
        
        # Ветровые условия
        if today.wind_speed < 5:
            positive_factors.append("✅ Слабый ветер")
            confidence += 10
        elif today.wind_speed < 8:
            warning_factors.append(f"💨 Умеренный ветер ({today.wind_speed} м/с)")
            confidence -= 5
        
        # Определяем решение на основе confidence
        all_reasons = positive_factors + warning_factors
        
        if confidence >= 70 and len(positive_factors) >= 3:
            decision = 'excellent'
        elif confidence >= 50:
            decision = 'good'
        else:
            decision = 'not_recommended'
        
        return {
            'decision': decision,
            'confidence': min(95, max(5, confidence)),
            'reasons': all_reasons,
            'positive_count': len(positive_factors),
            'warning_count': len(warning_factors),
            'next_good_day': self._find_next_good_day(forecast) if decision != 'excellent' else None
        }
    
    def _get_precipitation_type(self, condition: str) -> str:
        """Определяет тип осадков"""
        if 'rain' in condition.lower():
            return "идет дождь"
        elif 'snow' in condition.lower():
            return "идет снег"
        elif 'drizzle' in condition.lower():
            return "моросит дождь"
        else:
            return "ожидаются осадки"
    
    def _find_next_good_day(self, forecast: WeatherForecast) -> Dict[str, Any]:
        """Находит следующий подходящий день для мойки"""
        for i, day in enumerate(forecast.daily[1:]):  # Начинаем с завтрашнего дня
            if (day.precipitation_amount == 0 and 
                day.temperature_min >= 0 and 
                day.wind_speed < 10):
                
                days_until = i + 1
                day_name = self._get_day_name(days_until)
                
                return {
                    'days_until': days_until,
                    'day_name': day_name,
                    'date': day.date,
                    'temperature': day.temperature_day,
                    'condition': day.condition
                }
        
        return None
    
    def _get_day_name(self, days_until: int) -> str:
        """Возвращает название дня"""
        if days_until == 1:
            return "завтра"
        elif days_until == 2:
            return "послезавтра"
        else:
            return f"через {days_until} дня"
    
    def _prepare_weather_data(self, forecast: WeatherForecast, city: str) -> Dict[str, Any]:
        """Подготавливает данные о погоде для AI"""
        today = forecast.get_today_forecast()
        tomorrow = forecast.get_tomorrow_forecast()
        
        forecast_data = []
        for i, day in enumerate(forecast.daily[:3]):
            forecast_data.append({
                'day': i,
                'condition': day.condition,
                'temperature': day.temperature_day,
                'precipitation': day.precipitation_amount,
                'wind_speed': day.wind_speed,
                'humidity': day.humidity
            })
        
        return {
            'city': city,
            'current': {
                'temperature': forecast.current.temperature,
                'feels_like': forecast.current.feels_like,
                'condition': forecast.current.condition,
                'precipitation': today.precipitation_amount if today else 0,
                'humidity': forecast.current.humidity,
                'wind_speed': forecast.current.wind_speed,
                'visibility': forecast.current.visibility
            },
            'forecast': forecast_data,
            'precipitation_today': today.precipitation_amount if today else 0,
            'precipitation_tomorrow': tomorrow.precipitation_amount if tomorrow else 0,
            'wind_speed': forecast.current.wind_speed
        }
    
    def _build_ai_recommendation_text(self, city: str, analysis: Dict[str, Any], 
                                    ai_recommendation: str, forecast: WeatherForecast) -> str:
        """Строит рекомендацию с использованием AI"""
        condition_ru = translate_weather_conditions(forecast.current.condition)
        temperature = round(forecast.current.temperature)
        
        base_text = f"🧼 *Умная рекомендация по мойке для {city}*\n\n"
        base_text += f"🌤️ Сейчас: {condition_ru}, {temperature}°C\n\n"
        base_text += "🤖 *Рекомендация AI-эксперта:*\n\n"
        base_text += f"{ai_recommendation}\n\n"
        base_text += f"_Обновлено: {get_current_timestamp()}_"
        
        return base_text
    
    def _build_recommendation_text(self, city: str, analysis: Dict[str, Any], forecast: WeatherForecast) -> str:
        """Строит текст рекомендации с новой логикой"""
        condition_ru = translate_weather_conditions(forecast.current.condition)
        temperature = round(forecast.current.temperature)
        
        decision = analysis['decision']
        reasons_text = "\n".join([f"• {reason}" for reason in analysis['reasons']])
        
        # Базовый текст с городом и погодой
        base_text = f"🧼 *Рекомендация по мойке для {city}*\n\n"
        base_text += f"🌤️ Сейчас: {condition_ru}, {temperature}°C\n\n"
        
        # Текст в зависимости от решения
        if decision == 'excellent':
            return self.locale.get_message(
                'wash_recommendation_excellent',
                base_text=base_text,
                reasons_text=reasons_text,
                confidence=analysis['confidence'],
                timestamp=get_current_timestamp()
            )
        
        elif decision == 'good':
            return self.locale.get_message(
                'wash_recommendation_good',
                base_text=base_text,
                reasons_text=reasons_text,
                confidence=analysis['confidence'],
                timestamp=get_current_timestamp()
            )
        
        elif decision == 'not_recommended':
            next_day_info = ""
            if analysis.get('next_good_day'):
                next_day = analysis['next_good_day']
                next_day_info = self.locale.get_message(
                    'wash_next_good_day',
                    day_name=next_day['day_name'],
                    temperature=next_day['temperature'],
                    condition=translate_weather_conditions(next_day['condition'])
                )
            
            return self.locale.get_message(
                'wash_recommendation_not_recommended',
                base_text=base_text,
                reasons_text=reasons_text,
                next_day_info=next_day_info,
                timestamp=get_current_timestamp()
            )
        
        else:  # definitely_no
            next_day_info = ""
            if analysis.get('next_good_day'):
                next_day = analysis['next_good_day']
                next_day_info = self.locale.get_message(
                    'wash_next_good_day',
                    day_name=next_day['day_name'],
                    temperature=next_day['temperature'],
                    condition=translate_weather_conditions(next_day['condition'])
                )
            
            return self.locale.get_message(
                'wash_recommendation_definitely_no',
                base_text=base_text,
                reasons_text=reasons_text,
                next_day_info=next_day_info,
                timestamp=get_current_timestamp()
            )
