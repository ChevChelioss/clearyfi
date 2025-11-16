# core/events/melt_event.py
from .base_event import WeatherEvent

class MeltEvent(WeatherEvent):
    name = "MeltEvent"

    def is_triggered(self, day):
        # Таяние предполагается если температура > 0 и были/есть осадки в предыдущие дни.
        # В этом простом детекторе мы смотрим на наличие 'melt_flag' в day (producer должен выставлять)
        return day.get("melt_flag", False)

    def get_message(self, day):
        return f"🌊 {day.get('date')}: возможное таяние снега — после таяния дороги станут грязными."
