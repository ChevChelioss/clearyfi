# core/events/rain_event.py
from .base_event import WeatherEvent

class RainEvent(WeatherEvent):
    name = "RainEvent"

    def is_triggered(self, day):
        # если на день есть накопленный объём осадков
        return bool(day.get("rain_prob", 0))

    def get_message(self, day):
        return f"🌧 {day.get('date')}: ожидаются осадки — мойку лучше отложить."
