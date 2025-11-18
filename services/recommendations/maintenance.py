#!/usr/bin/env python3
"""
Сервис рекомендаций по техническому обслуживанию автомобиля с интеграцией DeepSeek AI
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta

from .base import BaseRecommendationService
from services.weather.models import WeatherForecast
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


class MaintenanceService(BaseRecommendationService):
    """Сервис рекомендаций по техническому обслуживанию автомобиля с AI"""
    
    def __init__(self, weather_service, locale_manager, database, deepseek_api_key: str = None):
        super().__init__(weather_service, locale_manager)
        self.database = database
        self.maintenance_schedule = self._get_maintenance_schedule()
        self.deepseek_service = None
        
        if DEEPSEEK_AVAILABLE and deepseek_api_key:
            try:
                self.deepseek_service = DeepSeekService(deepseek_api_key)
                logger.info("✅ DeepSeekService инициализирован для технического обслуживания")
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации DeepSeekService: {e}")
                self.deepseek_service = None
    
    def get_recommendation(self, city: str) -> Dict[str, Any]:
        """
        Возвращает рекомендацию по техническому обслуживанию
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
            
            # Анализируем условия для ТО
            analysis = self._analyze_maintenance_conditions(forecast)
            
            # Если доступен AI, получаем улучшенную рекомендацию
            ai_recommendation = None
            if self.deepseek_service and self.deepseek_service.is_available():
                weather_data = self._prepare_weather_data(forecast, city, analysis)
                ai_recommendation = self.deepseek_service.get_recommendation(weather_data, "maintenance")
            
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
            logger.error(f"❌ Ошибка в сервисе технического обслуживания: {e}")
            return {
                'success': False,
                'recommendation': self.locale.get_message('service_unavailable'),
                'city': city,
                'data': {}
            }
    
    def _analyze_maintenance_conditions(self, forecast: WeatherForecast) -> Dict[str, Any]:
        """Анализирует условия для технического обслуживания"""
        current_temp = forecast.current.temperature
        season = self._get_current_season()
        
        # Определяем рекомендации по сезону
        seasonal_recommendations = self._get_seasonal_recommendations(season, current_temp)
        
        # Рекомендации по жидкостям
        fluid_recommendations = self._get_fluid_recommendations(current_temp)
        
        # Проверка систем
        system_checks = self._get_system_checks(season, forecast)
        
        # Срочность обслуживания
        urgency = self._calculate_maintenance_urgency(seasonal_recommendations, system_checks)
        
        return {
            'season': season,
            'seasonal_recommendations': seasonal_recommendations,
            'fluid_recommendations': fluid_recommendations,
            'system_checks': system_checks,
            'urgency': urgency,
            'current_temperature': current_temp
        }
    
    def _get_current_season(self) -> str:
        """Определяет текущий сезон"""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'autumn'
    
    def _get_seasonal_recommendations(self, season: str, temperature: float) -> List[str]:
        """Возвращает сезонные рекомендации"""
        recommendations = []
        
        if season == 'winter':
            recommendations.append("❄️ Проверьте антифриз и омывающую жидкость")
            recommendations.append("🔋 Проверьте аккумулятор")
            recommendations.append("🛞 Убедитесь в хорошем состоянии зимней резины")
            
        elif season == 'summer':
            recommendations.append("☀️ Проверьте кондиционер")
            recommendations.append("🌡️ Контролируйте температуру двигателя")
            recommendations.append("💧 Проверьте уровень охлаждающей жидкости")
            
        elif season == 'spring':
            recommendations.append("🌸 Сезонная замена масла")
            recommendations.append("🧹 Мойка и чистка после зимы")
            recommendations.append("🔍 Полная диагностика после зимнего сезона")
            
        else:  # autumn
            recommendations.append("🍂 Подготовка к зиме")
            recommendations.append("🛞 Замена на зимнюю резину")
            recommendations.append("🔧 Проверка отопительной системы")
        
        # Температурные рекомендации
        if temperature < -10:
            recommendations.append("🥶 Сильные морозы - особое внимание к аккумулятору")
        elif temperature > 30:
            recommendations.append("🔥 Сильная жара - контроль перегрева")
        
        return recommendations
    
    def _get_fluid_recommendations(self, temperature: float) -> List[str]:
        """Возвращает рекомендации по жидкостям"""
        recommendations = []
        
        # Рекомендации по моторному маслу
        if temperature < -15:
            recommendations.append("🛢️ Используйте зимнее моторное масло (0W-30, 5W-30)")
        elif temperature > 35:
            recommendations.append("🛢️ Используйте летнее моторное масло (10W-40, 15W-40)")
        else:
            recommendations.append("🛢️ Универсальное моторное масло подходит")
        
        # Омывающая жидкость
        if temperature < 0:
            recommendations.append("💧 Используйте незамерзающую омывающую жидкость")
        
        # Тормозная жидкость
        recommendations.append("🛑 Проверьте тормозную жидкость (замена раз в 2 года)")
        
        return recommendations
    
    def _get_system_checks(self, season: str, forecast: WeatherForecast) -> List[str]:
        """Возвращает список проверок систем"""
        checks = []
        
        # Всесезонные проверки
        checks.extend([
            "✅ Тормозная система",
            "✅ Рулевое управление", 
            "✅ Подвеска",
            "✅ Электрооборудование",
            "✅ Система зажигания"
        ])
        
        # Сезонные проверки
        if season in ['winter', 'autumn']:
            checks.extend([
                "✅ Отопитель салона",
                "✅ Обогрев стекол и зеркал",
                "✅ Система запуска в холодную погоду"
            ])
        
        if season in ['summer', 'spring']:
            checks.extend([
                "✅ Кондиционер",
                "✅ Система охлаждения",
                "✅ Вентиляция салона"
            ])
        
        # Погодные проверки
        if forecast.current.condition in ['Rain', 'Snow']:
            checks.append("✅ Дворники и омыватели")
        
        if forecast.current.wind_speed > 8:
            checks.append("✅ Уплотнители дверей и окон")
        
        return checks
    
    def _calculate_maintenance_urgency(self, seasonal_recs: List[str], system_checks: List[str]) -> str:
        """Определяет срочность обслуживания"""
        urgent_indicators = [
            "антифриз", "аккумулятор", "тормоз", "масло", "перегрев"
        ]
        
        for rec in seasonal_recs:
            if any(indicator in rec.lower() for indicator in urgent_indicators):
                return "high"
        
        return "medium" if len(seasonal_recs) > 3 else "low"
    
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
            })
        
        return {
            'city': city,
            'current': {
                'temperature': forecast.current.temperature,
                'condition': forecast.current.condition,
            },
            'forecast': forecast_data,
            'season': analysis['season'],
            'urgency': analysis['urgency'],
            'fluid_recommendations': analysis['fluid_recommendations']
        }
    
    def _build_ai_recommendation_text(self, city: str, analysis: Dict[str, Any], 
                                    ai_recommendation: str, forecast: WeatherForecast) -> str:
        """Строит рекомендацию с использованием AI"""
        condition_ru = translate_weather_conditions(forecast.current.condition)
        temperature = round(forecast.current.temperature)
        
        base_text = f"🔧 *Умная рекомендация по ТО для {city}*\n\n"
        base_text += f"🌤️ Сейчас: {condition_ru}, {temperature}°C\n\n"
        base_text += "🤖 *Рекомендация AI-эксперта:*\n\n"
        base_text += f"{ai_recommendation}\n\n"
        base_text += f"_Обновлено: {get_current_timestamp()}_"
        
        return base_text
    
    def _build_recommendation_text(self, city: str, analysis: Dict[str, Any], forecast: WeatherForecast) -> str:
        """Строит текст рекомендации по ТО"""
        condition_ru = translate_weather_conditions(forecast.current.condition)
        temperature = round(forecast.current.temperature)
        
        # Сезонные рекомендации
        seasonal_text = "\n".join([f"• {rec}" for rec in analysis['seasonal_recommendations']])
        
        # Рекомендации по жидкостям
        fluids_text = "\n".join([f"• {rec}" for rec in analysis['fluid_recommendations']])
        
        # Проверки систем
        checks_text = "\n".join([f"• {check}" for check in analysis['system_checks']])
        
        # Уровень срочности
        urgency_text = ""
        if analysis['urgency'] == "high":
            urgency_text = "\n🚨 *ВЫСОКАЯ СРОЧНОСТЬ* - рекомендуем обратиться в сервис!"
        elif analysis['urgency'] == "medium":
            urgency_text = "\n⚠️ *Средняя срочность* - запланируйте визит в сервис"
        
        return self.locale.get_message(
            'maintenance_recommendation',
            city=city,
            condition=condition_ru,
            temperature=temperature,
            seasonal_text=seasonal_text,
            fluids_text=fluids_text,
            checks_text=checks_text,
            urgency_text=urgency_text,
            timestamp=get_current_timestamp()
        )
    
    def _get_maintenance_schedule(self) -> Dict[str, Any]:
        """Возвращает график технического обслуживания"""
        return {
            'daily': ["Проверка уровня жидкостей", "Внешний осмотр"],
            'weekly': ["Проверка давления в шинах", "Проверка фар"],
            'monthly': ["Замена масла (при необходимости)", "Диагностика систем"],
            'seasonal': ["Сезонная замена резины", "Комплексная диагностика"]
        }
