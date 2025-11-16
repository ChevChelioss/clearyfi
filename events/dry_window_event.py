# core/events/dry_window_event.py
from .base_event import WeatherEvent

class DryWindowEvent(WeatherEvent):
    name = "DryWindowEvent"

    def is_triggered(self, day):
        # Если нет осадков и влажность невысока — это сухое окно
        return day.get("rain_prob", 0) == 0 and day.get("humidity", 100) < 70

    def get_message(self, day):
        return f"✅ {day.get('date')}: сухое окно — хорошее время для мойки."
