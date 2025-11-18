#!/usr/bin/env python3
"""
Сервис для работы с DeepSeek API
Интеграция AI для улучшения рекомендаций ClearyFi
"""

import requests
import json
from typing import Dict, Any, Optional

from .base_ai_service import BaseAIService
from core.logger import logger


class DeepSeekService(BaseAIService):
    """Сервис для работы с DeepSeek AI"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.deepseek.com/v1/chat/completions")
        logger.info("✅ DeepSeekService инициализирован")
    
    def get_recommendation(self, weather_data: Dict[str, Any], context: str = "car_wash") -> Optional[str]:
        """
        Получает улучшенную рекомендацию от DeepSeek AI
        
        Args:
            weather_data: Данные о погоде и контексте
            context: Контекст рекомендации (car_wash, tires, roads, maintenance)
            
        Returns:
            Улучшенная рекомендация или None при ошибке
        """
        if not self.is_available():
            logger.warning("❌ DeepSeekService недоступен - отсутствует API ключ")
            return None
        
        try:
            prompt = self._build_prompt(weather_data, context)
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": self._get_system_prompt(context)
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 600,
                "stream": False
            }
            
            logger.debug(f"📤 Отправка запроса к DeepSeek API: {context}")
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=15)
            response.raise_for_status()
            
            result = response.json()
            recommendation = result['choices'][0]['message']['content'].strip()
            
            logger.info(f"✅ Получена рекомендация от DeepSeek AI для контекста: {context}")
            return recommendation
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка сети при запросе к DeepSeek: {e}")
            return None
        except KeyError as e:
            logger.error(f"❌ Ошибка парсинга ответа DeepSeek: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка в DeepSeekService: {e}")
            return None
    
    def _get_system_prompt(self, context: str) -> str:
        """Возвращает системный промпт в зависимости от контекста"""
        prompts = {
            "car_wash": (
                "Ты опытный автомобильный эксперт и метеоролог. "
                "Дай четкую, полезную рекомендацию по мойке автомобиля на основе погодных условий. "
                "Будь конкретен, уверен и дай actionable совет. "
                "Не используй расплывчатые фразы вроде 'рекомендуем оценить необходимость'. "
                "Дай четкий ответ: МЫТЬ или НЕ МЫТЬ, с конкретными причинами и альтернативами."
            ),
            "tires": (
                "Ты эксперт по автомобильным шинам и сезонному обслуживанию. "
                "Дай четкие рекомендации по шинам на основе погодных условий. "
                "Учитывай температуру, осадки, сезонность. "
                "Будь конкретен в рекомендациях по давлению, смене резины, шиномонтажу."
            ),
            "roads": (
                "Ты опытный инструктор по вождению и эксперт по дорожным условиям. "
                "Дай практические советы по вождению на основе текущей погоды. "
                "Предупреди об опасностях и дай конкретные рекомендации по стилю вождения."
            ),
            "maintenance": (
                "Ты автомеханик с многолетним опытом. "
                "Дай рекомендации по техническому обслуживанию автомобиля на основе погодных условий. "
                "Учитывай сезонность, температуру, влажность. "
                "Будь конкретен в советах по жидкостям, системам автомобиля."
            )
        }
        
        return prompts.get(context, prompts["car_wash"])
    
    def _build_prompt(self, weather_data: Dict[str, Any], context: str) -> str:
        """Строит промпт для AI на основе данных о погоде"""
        
        current = weather_data.get('current', {})
        forecast = weather_data.get('forecast', [])
        city = weather_data.get('city', 'неизвестный город')
        
        prompt = f"""
КОНТЕКСТ: {context.upper()}
ГОРОД: {city}

ТЕКУЩИЕ ПОГОДНЫЕ УСЛОВИЯ:
- Температура: {current.get('temperature', 'N/A')}°C
- Ощущается как: {current.get('feels_like', 'N/A')}°C  
- Погода: {current.get('condition', 'N/A')}
- Осадки: {current.get('precipitation', 0)} мм
- Влажность: {current.get('humidity', 'N/A')}%
- Ветер: {current.get('wind_speed', 'N/A')} м/с
- Видимость: {current.get('visibility', 'N/A')} м

ПРОГНОЗ НА 3 ДНЯ:
{self._format_forecast(forecast)}

ДОПОЛНИТЕЛЬНЫЕ ДАННЫЕ:
{self._get_context_specific_data(weather_data, context)}

ПОЖАЛУЙСТА, ДАЙ:
1. ЧЕТКУЮ РЕКОМЕНДАЦИЮ (однозначный ответ)
2. КОНКРЕТНЫЕ ПРИЧИНЫ и факты
3. ПРАКТИЧЕСКИЕ СОВЕТЫ и альтернативы
4. ПРЕДУПРЕЖДЕНИЯ об опасностях если есть

Будь конкретен, уверен и полезен для автомобилиста.
"""
        return prompt
    
    def _format_forecast(self, forecast: list) -> str:
        """Форматирует прогноз для промпта"""
        if not forecast:
            return "  Нет данных прогноза"
        
        forecast_text = ""
        for i, day in enumerate(forecast[:3]):
            day_name = self._get_day_name(i)
            forecast_text += (
                f"  {day_name}: {day.get('condition', 'N/A')}, "
                f"{day.get('temperature', 'N/A')}°C, "
                f"осадки: {day.get('precipitation', 0)} мм, "
                f"ветер: {day.get('wind_speed', 'N/A')} м/с\n"
            )
        
        return forecast_text
    
    def _get_day_name(self, day_index: int) -> str:
        """Возвращает название дня"""
        days = ["Сегодня", "Завтра", "Послезавтра"]
        return days[day_index] if day_index < len(days) else f"День {day_index + 1}"
    
    def _get_context_specific_data(self, weather_data: Dict[str, Any], context: str) -> str:
        """Возвращает дополнительные данные в зависимости от контекста"""
        if context == "tires":
            return (
                "ДАННЫЕ ДЛЯ ШИН:\n"
                f"- Сезон: {weather_data.get('season', 'N/A')}\n"
                f"- Смена резины рекомендована: {weather_data.get('change_recommended', 'N/A')}\n"
                f"- Срочность: {weather_data.get('urgency', 'N/A')}"
            )
        elif context == "roads":
            return (
                "ДОРОЖНЫЕ УСЛОВИЯ:\n"
                f"- Риски: {', '.join(weather_data.get('risks', []))}\n"
                f"- Уровень опасности: {weather_data.get('danger_level', 'N/A')}\n"
                f"- Оценка условий: {weather_data.get('condition_score', 'N/A')}/5"
            )
        elif context == "maintenance":
            return (
                "ТЕХНИЧЕСКОЕ ОБСЛУЖИВАНИЕ:\n"
                f"- Сезон: {weather_data.get('season', 'N/A')}\n"
                f"- Срочность обслуживания: {weather_data.get('urgency', 'N/A')}\n"
                f"- Рекомендации по жидкостям: {len(weather_data.get('fluid_recommendations', []))}"
            )
        else:  # car_wash
            return (
                "ДАННЫЕ ДЛЯ МОЙКИ:\n"
                f"- Осадки сегодня: {weather_data.get('precipitation_today', 0)} мм\n"
                f"- Осадки завтра: {weather_data.get('precipitation_tomorrow', 0)} мм\n"
                f"- Ветер: {weather_data.get('wind_speed', 'N/A')} м/с"
            )
    
    def test_connection(self) -> bool:
        """Тестирует соединение с DeepSeek API"""
        try:
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "Тестовое сообщение. Ответь 'OK'"}],
                "max_tokens": 5
            }
            
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования DeepSeek: {e}")
            return False
