# core/events/base_event.py
from typing import Dict, Any

class WeatherEvent:
    """
    Базовый интерфейс погодного события.
    Подклассы реализуют is_triggered(day) и get_message(day).
    day — словарь с полями:
      date, temp, humidity, wind, conditions(list), rain_prob (0/1)
    """
    name: str = "WeatherEvent"

    def is_triggered(self, day: Dict[str, Any]) -> bool:
        raise NotImplementedError

    def get_message(self, day: Dict[str, Any]) -> str:
        return f"{self.name} triggered on {day.get('date')}"
