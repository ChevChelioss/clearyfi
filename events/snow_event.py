# core/events/snow_event.py
from .base_event import WeatherEvent

class SnowEvent(WeatherEvent):
    name = "SnowEvent"

    def is_triggered(self, day):
        conds = [c.lower() for c in (day.get("conditions") or [])]
        return any("snow" in c for c in conds)

    def get_message(self, day):
        return f"❄️ {day.get('date')}: снег в прогнозе — возможно грязь/заносы."
