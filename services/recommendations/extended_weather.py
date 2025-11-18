#!/usr/bin/env python3
"""
Сервис расширенных погодных рекомендаций для автомобилистов
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta

from .base import BaseRecommendationService
from services.weather.models import WeatherForecast, ForecastDay
from utils.date_utils import get_current_timestamp, format_date_short
from utils.text_utils import translate_weather_conditions, format_wind_speed, format_precipitation
from core.logger import logger


class ExtendedWeatherService(BaseRecommendationService):
    """Сервис расширенных погодных рекомендаций для автомобилистов"""
    
    def get_recommendation(self, city: str) -> Dict[str, Any]:
        """
        Возвращает расширенную погодную рекомендацию для автомобилиста
        
        Логика рекомендаций:
        - Детальный прогноз на несколько дней
        - Специфические рекомендации для водителей
        - Предупреждения об опасных явлениях
        - Советы по подготовке автомобиля
        
        Args:
            city: Название города
            
        Returns:
            Словарь с результатом
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
            
            # Анализируем расширенные погодные условия
            analysis = self._analyze_extended_weather(forecast)
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
            logger.error(f"❌ Ошибка в сервисе расширенных погодных рекомендаций: {e}")
            return {
                'success': False,
                'recommendation': self.locale.get_message('service_unavailable'),
                'city': city,
                'data': {}
            }
    
    def _analyze_extended_weather(self, forecast: WeatherForecast) -> Dict[str, Any]:
        """Анализирует расширенные погодные условия"""
        current = forecast.current
        daily_forecast = forecast.daily
        
        # Анализ текущих условий
        current_analysis = self._analyze_current_conditions(current)
        
        # Прогноз на несколько дней
        forecast_analysis = self._analyze_multi_day_forecast(daily_forecast)
        
        # Опасные явления
        hazards = self._detect_weather_hazards(forecast)
        
        # Рекомендации для автомобилиста
        driver_recommendations = self._get_driver_recommendations(current_analysis, hazards)
        
        # Подготовка автомобиля
        car_preparation = self._get_car_preparation_recommendations(forecast_analysis)
        
        return {
            'current_analysis': current_analysis,
            'forecast_analysis': forecast_analysis,
            'hazards': hazards,
            'driver_recommendations': driver_recommendations,
            'car_preparation': car_preparation,
            'days_forecast': len(daily_forecast)
        }
    
    def _analyze_current_conditions(self, current_weather) -> Dict[str, Any]:
        """Анализирует текущие погодные условия"""
        return {
            'condition': current_weather.condition,
            'description': current_weather.description,
            'temperature': current_weather.temperature,
            'feels_like': current_weather.feels_like,
            'humidity': current_weather.humidity,
            'wind_speed': current_weather.wind_speed,
            'visibility': current_weather.visibility,
            'comfort_level': self._calculate_comfort_level(current_weather)
        }
    
    def _analyze_multi_day_forecast(self, daily_forecast: List[ForecastDay]) -> List[Dict[str, Any]]:
        """Анализирует прогноз на несколько дней"""
        analysis = []
        
        for i, day in enumerate(daily_forecast[:5]):  # Ограничиваем 5 днями
            day_analysis = {
                'day': format_date_short(day.date),
                'condition': day.condition,
                'temp_day': day.temperature_day,
                'temp_night': day.temperature_night,
                'precipitation': day.precipitation_amount,
                'precipitation_probability': day.precipitation_probability,
                'wind_speed': day.wind_speed,
                'driving_conditions': self._assess_driving_conditions(day)
            }
            analysis.append(day_analysis)
        
        return analysis
    
    def _detect_weather_hazards(self, forecast: WeatherForecast) -> List[Dict[str, Any]]:
        """Обнаруживает опасные погодные явления"""
        hazards = []
        current = forecast.current
        
        # Сильный ветер
        if current.wind_speed > 15:
            hazards.append({
                'type': 'strong_wind',
                'level': 'high',
                'message': f"💨 Сильный ветер ({current.wind_speed} м/с) - будьте осторожны на трассе"
            })
        
        # Плохая видимость
        if current.visibility < 1000:
            hazards.append({
                'type': 'poor_visibility',
                'level': 'high' if current.visibility < 500 else 'medium',
                'message': f"👁️ Плохая видимость ({current.visibility} м) - включите фары"
            })
        
        # Экстремальные температуры
        if current.temperature < -20:
            hazards.append({
                'type': 'extreme_cold',
                'level': 'high',
                'message': "🥶 Экстремальный холод - проверьте аккумулятор и жидкости"
            })
        elif current.temperature > 35:
            hazards.append({
                'type': 'extreme_heat',
                'level': 'high',
                'message': "🔥 Сильная жара - риск перегрева двигателя"
            })
        
        # Осадки
        today = forecast.get_today_forecast()
        if today and today.precipitation_amount > 10:
            hazards.append({
                'type': 'heavy_precipitation',
                'level': 'high',
                'message': "🌧️ Сильные осадки - снизьте скорость"
            })
        
        return hazards
    
    def _get_driver_recommendations(self, current_analysis: Dict[str, Any], hazards: List[Dict[str, Any]]) -> List[str]:
        """Возвращает рекомендации для водителя"""
        recommendations = []
        
        # Базовые рекомендации по комфорту
        comfort = current_analysis['comfort_level']
        if comfort == 'low':
            recommendations.append("🚗 Подготовьтесь к сложным условиям вождения")
        elif comfort == 'medium':
            recommendations.append("⚠️ Условия требуют повышенного внимания")
        else:
            recommendations.append("✅ Комфортные условия для вождения")
        
        # Рекомендации по видимости
        if current_analysis['visibility'] < 2000:
            recommendations.append("💡 Включите ближний свет фар")
        if current_analysis['visibility'] < 1000:
            recommendations.append("🚨 Включите противотуманные фары")
        
        # Рекомендации по осадкам
        if any(h['type'] in ['heavy_precipitation'] for h in hazards):
            recommendations.append("🌧️ Увеличьте дистанцию до впереди идущего автомобиля")
        
        # Температурные рекомендации
        if current_analysis['temperature'] < 0:
            recommendations.append("❄️ Осторожно, возможен гололед")
        elif current_analysis['temperature'] > 25:
            recommendations.append("☀️ Используйте солнцезащитный козырек")
        
        return recommendations
    
    def _get_car_preparation_recommendations(self, forecast_analysis: List[Dict[str, Any]]) -> List[str]:
        """Возвращает рекомендации по подготовке автомобиля"""
        recommendations = []
        
        # Анализируем прогноз на ближайшие дни
        for day in forecast_analysis[:2]:  # Сегодня и завтра
            if day['precipitation'] > 5:
                recommendations.append("🧽 Подготовьте дворники к дождю")
                break
        
        # Проверяем резкие изменения температуры
        if len(forecast_analysis) > 1:
            temp_diff = abs(forecast_analysis[0]['temp_day'] - forecast_analysis[1]['temp_day'])
            if temp_diff > 10:
                recommendations.append("📉 Резкое изменение температуры - проверьте системы автомобиля")
        
        # Рекомендации по давлению в шинах при изменении температуры
        if any(day['temp_day'] < 5 for day in forecast_analysis[:3]):
            recommendations.append("🛞 Проверьте давление в шинах - при похолодании оно снижается")
        
        return recommendations
    
    def _calculate_comfort_level(self, weather_data) -> str:
        """Вычисляет уровень комфорта для вождения"""
        score = 0
        
        # Температура (оптимальная 15-25°C)
        temp = weather_data.temperature
        if 15 <= temp <= 25:
            score += 2
        elif 5 <= temp < 15 or 25 < temp <= 30:
            score += 1
        
        # Видимость (чем больше, тем лучше)
        visibility = weather_data.visibility
        if visibility >= 5000:
            score += 2
        elif visibility >= 2000:
            score += 1
        
        # Ветер (чем меньше, тем лучше)
        wind = weather_data.wind_speed
        if wind < 5:
            score += 2
        elif wind < 10:
            score += 1
        
        # Осадки
        if weather_data.condition in ['Clear', 'Cloudy']:
            score += 2
        elif weather_data.condition in ['Partly cloudy']:
            score += 1
        
        if score >= 6:
            return 'high'
        elif score >= 4:
            return 'medium'
        else:
            return 'low'
    
    def _assess_driving_conditions(self, day: ForecastDay) -> str:
        """Оценивает условия для вождения на конкретный день"""
        if day.precipitation_amount > 5:
            return "сложные"
        elif day.precipitation_amount > 0:
            return "умеренные"
        elif day.wind_speed > 10:
            return "ветреные"
        else:
            return "хорошие"
    
    def _build_recommendation_text(self, city: str, analysis: Dict[str, Any], forecast: WeatherForecast) -> str:
        """Строит текст расширенной погодной рекомендации"""
        current = forecast.current
        condition_ru = translate_weather_conditions(current.condition)
        temperature = round(current.temperature)
        
        # Формируем прогноз на дни
        forecast_text = ""
        for day_analysis in analysis['forecast_analysis'][:3]:  # 3 дня
            forecast_text += (
                f"• {day_analysis['day']}: {day_analysis['temp_day']:.0f}°C, "
                f"{translate_weather_conditions(day_analysis['condition'])}, "
                f"вождение: {day_analysis['driving_conditions']}\n"
            )
        
        # Опасные явления
        hazards_text = ""
        if analysis['hazards']:
            hazards_text = "\n🚨 *Опасные явления:*\n"
            for hazard in analysis['hazards']:
                hazards_text += f"• {hazard['message']}\n"
        
        # Рекомендации для водителя
        driver_text = "\n".join([f"• {rec}" for rec in analysis['driver_recommendations']])
        
        # Подготовка автомобиля
        preparation_text = "\n".join([f"• {rec}" for rec in analysis['car_preparation']])
        
        return self.locale.get_message(
            'extended_weather_recommendation',
            city=city,
            condition=condition_ru,
            temperature=temperature,
            forecast_text=forecast_text,
            hazards_text=hazards_text,
            driver_text=driver_text,
            preparation_text=preparation_text,
            comfort_level=analysis['current_analysis']['comfort_level'],
            timestamp=get_current_timestamp()
        )
