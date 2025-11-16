# services/weather/weather_api_client.py

import requests
from typing import Dict, Any, Optional


class WeatherAPIClient:
    """
    Клиент для получения прогноза погоды на 5+ дней.
    Работает с OpenWeather API (forecast).
    """

    BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

    def __init__(self, api_key: str, lang: str = "ru"):
        self.api_key = api_key
        self.lang = lang

    # ----------------------------------------------------------------------

    def get_forecast(self, city: str, days: int = 5) -> Optional[Dict[str, Any]]:
        """
        Запрашивает прогноз погоды для города.

        :param city: Название города
        :param days: Количество дней (OpenWeather выдает до 5)
        :return: Сырые данные прогноза или None при ошибке
        """

        params = {
            "q": f"{city},RU",          # важный твой фикс (город + страна)
            "appid": self.api_key,
            "units": "metric",          # температура в °C
            "lang": self.lang
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)

            if response.status_code != 200:
                print(f"[ERROR] Weather API: HTTP {response.status_code}")
                return None

            data = response.json()

            # Защита от странных данных
            if "list" not in data:
                print("[ERROR] Weather API: нет поля list")
                return None

            return data

        except Exception as e:
            print(f"[EXCEPTION] WeatherAPIClient: {e}")
            return None

    # ----------------------------------------------------------------------

    def is_city_valid(self, city: str) -> bool:
        """
        Быстрая проверка существования города.
        Используем тот же API, но проверяем только статус ответа.
        """

        params = {
            "q": f"{city},RU",
            "appid": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=7)
            return response.status_code == 200

        except:
            return False
