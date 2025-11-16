# core/events/mud_event.py
from .base_event import WeatherEvent

class MudEvent(WeatherEvent):
    name = "MudEvent"

    def is_triggered(self, day):
        # Эвристика: высокая влажность + осадки в один из соседних дней
        humidity = day.get("humidity", 0)
        precip = bool(day.get("rain_prob", 0))
        # также учитываем melt_flag или если avg temp low + recent precip
        return (humidity >= 75 and precip) or day.get("melt_flag", False)

    def get_message(self, day):
        return f"🟤 {day.get('date')}: высокий риск грязи — мойка быстро загрязнится."
