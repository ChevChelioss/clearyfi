"""
Клиент для работы с API погодного сервиса
"""

import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger('WeatherAPIClient')


class WeatherAPIClient:
    """
    Клиент для взаимодействия с OpenWeatherMap API
    """
    
    def __init__(self, api_key: str):
        """
        Инициализация клиента погодного API.
        
        Args:
            api_key: API ключ для OpenWeatherMap
        """
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.session = None
        
        logger.info("WeatherAPIClient инициализирован")

    async def _ensure_session(self):
        """Обеспечивает наличие активной сессии aiohttp."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """
        Выполняет HTTP запрос к API.
        
        Args:
            endpoint: Конечная точка API
            params: Параметры запроса
            
        Returns:
            Ответ API в виде словаря или None при ошибке
        """
        try:
            await self._ensure_session()
            
            url = f"{self.base_url}/{endpoint}"
            params['appid'] = self.api_key
            params['units'] = 'metric'  # Для получения в Цельсиях
            params['lang'] = 'ru'       # Русский язык
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Успешный запрос к {endpoint}")
                    return data
                else:
                    logger.error(f"Ошибка API {endpoint}: {response.status}")
                    return None
                    
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети при запросе к {endpoint}: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запросе к {endpoint}: {e}")
            return None

    async def get_forecast(self, city: str, days: int = 3) -> Optional[Dict]:
        """
        Получает прогноз погоды для указанного города.
        
        Args:
            city: Название города
            days: Количество дней для прогноза (1-5)
            
        Returns:
            Словарь с данными прогноза или None при ошибке
        """
        try:
            # Ограничиваем количество дней
            days = max(1, min(days, 5))
            
            # Используем endpoint прогноза на 5 дней (3 часа интервал)
            params = {
                'q': city,
                'cnt': days * 8  # 8 точек данных в день (24/3)
            }
            
            data = await self._make_request('forecast', params)
            
            if data and 'list' in data:
                logger.info(f"Получен прогноз для {city} на {days} дней")
                return self._process_forecast_data(data, days)
            else:
                logger.error(f"Неверный ответ API для города {city}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения прогноза для {city}: {e}")
            return None

    async def get_current_weather(self, city: str) -> Optional[Dict]:
        """
        Получает текущую погоду для указанного города.
        
        Args:
            city: Название города
            
        Returns:
            Словарь с текущими погодными данными или None при ошибке
        """
        try:
            params = {'q': city}
            data = await self._make_request('weather', params)
            
            if data:
                logger.info(f"Получена текущая погода для {city}")
                return self._process_current_weather_data(data)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения текущей погоды для {city}: {e}")
            return None

    async def is_city_valid(self, city: str) -> bool:
        """
        Проверяет существование города через API.
        
        Args:
            city: Название города для проверки
            
        Returns:
            True если город существует, False в противном случае
        """
        try:
            data = await self.get_current_weather(city)
            return data is not None
            
        except Exception as e:
            logger.error(f"Ошибка проверки города {city}: {e}")
            return False

    def _process_forecast_data(self, raw_data: Dict, days: int) -> Dict:
        """
        Обрабатывает сырые данные прогноза в структурированный формат.
        
        Args:
            raw_data: Сырые данные от API
            days: Количество дней для прогноза
            
        Returns:
            Структурированные данные прогноза
        """
        try:
            processed_data = {
                'city': raw_data.get('city', {}).get('name', 'Unknown'),
                'country': raw_data.get('city', {}).get('country', 'Unknown'),
                'daily_data': []
            }
            
            # Группируем по дням
            from collections import defaultdict
            import datetime
            
            daily_forecasts = defaultdict(list)
            
            for forecast in raw_data['list']:
                # Преобразуем timestamp в дату
                forecast_date = datetime.datetime.fromtimestamp(
                    forecast['dt']
                ).strftime('%Y-%m-%d')
                
                daily_forecasts[forecast_date].append(forecast)
            
            # Обрабатываем каждый день
            for date, forecasts in list(daily_forecasts.items())[:days]:
                day_data = self._process_daily_forecast(date, forecasts)
                processed_data['daily_data'].append(day_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Ошибка обработки данных прогноза: {e}")
            return {}

    def _process_daily_forecast(self, date: str, forecasts: List[Dict]) -> Dict:
        """
        Обрабатывает прогнозы для одного дня.
        
        Args:
            date: Дата в формате YYYY-MM-DD
            forecasts: Список прогнозов на этот день
            
        Returns:
            Структурированные данные за день
        """
        try:
            temperatures = [f['main']['temp'] for f in forecasts]
            humidities = [f['main']['humidity'] for f in forecasts]
            wind_speeds = [f['wind']['speed'] for f in forecasts]
            
            # Определяем основные погодные условия дня
            conditions = []
            for forecast in forecasts:
                for weather in forecast['weather']:
                    condition = weather['main']
                    if condition not in conditions:
                        conditions.append(condition)
            
            # Расчет вероятности дождя
            rain_probability = 0
            for forecast in forecasts:
                if 'rain' in forecast and forecast['rain'].get('3h', 0) > 0:
                    rain_probability = max(rain_probability, 30)  # Базовая вероятность
                
                for weather in forecast['weather']:
                    if weather['main'] in ['Rain', 'Drizzle', 'Thunderstorm']:
                        rain_probability = 100  # Если дождь предсказан, вероятность 100%
            
            return {
                'date': date,
                'temp_avg': sum(temperatures) / len(temperatures),
                'temp_min': min(temperatures),
                'temp_max': max(temperatures),
                'humidity_avg': sum(humidities) / len(humidities),
                'wind_avg': sum(wind_speeds) / len(wind_speeds),
                'conditions': conditions,
                'rain_probability': rain_probability,
                'forecast_count': len(forecasts)
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки дневного прогноза для {date}: {e}")
            return {}

    def _process_current_weather_data(self, raw_data: Dict) -> Dict:
        """
        Обрабатывает данные о текущей погоде.
        
        Args:
            raw_data: Сырые данные от API
            
        Returns:
            Структурированные данные о текущей погоде
        """
        try:
            main = raw_data.get('main', {})
            weather = raw_data.get('weather', [{}])[0]
            wind = raw_data.get('wind', {})
            
            return {
                'temperature': main.get('temp', 0),
                'feels_like': main.get('feels_like', 0),
                'humidity': main.get('humidity', 0),
                'pressure': main.get('pressure', 0) * 0.750062,  # Переводим в мм рт. ст.
                'wind_speed': wind.get('speed', 0),
                'wind_direction': wind.get('deg', 0),
                'weather': weather.get('description', ''),
                'visibility': raw_data.get('visibility', 0),
                'clouds': raw_data.get('clouds', {}).get('all', 0),
                'city': raw_data.get('name', 'Unknown'),
                'country': raw_data.get('sys', {}).get('country', 'Unknown'),
                'timestamp': raw_data.get('dt', 0)
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки текущей погоды: {e}")
            return {}

    async def close(self):
        """Закрывает сессию aiohttp."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("Сессия WeatherAPIClient закрыта")


# Синхронная обертка для обратной совместимости
class SyncWeatherAPIClient:
    """
    Синхронная обертка для WeatherAPIClient
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.async_client = WeatherAPIClient(api_key)
    
    def get_forecast(self, city: str, days: int = 3) -> Optional[Dict]:
        """Синхронная версия get_forecast"""
        return asyncio.run(self.async_client.get_forecast(city, days))
    
    def get_current_weather(self, city: str) -> Optional[Dict]:
        """Синхронная версия get_current_weather"""
        return asyncio.run(self.async_client.get_current_weather(city))
    
    def is_city_valid(self, city: str) -> bool:
        """Синхронная версия is_city_valid"""
        return asyncio.run(self.async_client.is_city_valid(city))
    
    def close(self):
        """Синхронная версия close"""
        asyncio.run(self.async_client.close())
