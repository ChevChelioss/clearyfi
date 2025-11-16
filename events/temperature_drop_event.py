# core/events/temperature_drop_event.py
from .base_event import WeatherEvent

class TemperatureDropEvent(WeatherEvent):
    name = "TemperatureDropEvent"

    def is_triggered(self, day):
        # Ожидаем поле 'temp_delta' (разница дневной температуры к предыдущему дню)
        # Если нет, используем простую эвристику: средняя temp <= 1°C
        delta = day.get("temp_delta")
        if delta is not None:
            return delta <= -5  # резкое понижение на 5°C и более
        return day.get("temp", 999) <= 1

    def get_message(self, day):
        return f"🧊 {day.get('date')}: резкое похолодание — возможен гололёд."
