# core/weather_analyzer.py

from typing import List, Dict, Any, Optional
import statistics
from events import (
    RainEvent, SnowEvent, MeltEvent, MudEvent,
    TemperatureDropEvent, DryWindowEvent
)

class WeatherAnalyzer:
    """
    Центральный модуль анализа погоды.
    Принимает прогноз погоды на 5+ дней и возвращает:
    - лучший день для мойки
    - оценку рисков
    - описание погодных условий
    """

    def __init__(self, forecast_data: Dict[str, Any]):
        """
        :param forecast_data: Сырые данные прогноза от API
        """
        self.raw = forecast_data
        self.daily = self._normalize_daily_data()

    # ----------------------------------------------------------------------
    # 1. НОРМАЛИЗАЦИЯ ДАННЫХ
    # ----------------------------------------------------------------------

    def _normalize_daily_data(self) -> List[Dict[str, Any]]:
        """
        Приводит данные API к нормальной структуре и добавляет вспомогательные флаги:
        - date
        - temp (avg)
        - humidity (avg)
        - wind (avg)
        - rain_prob (0/1)
        - conditions (uniq list)
        - temp_delta (разница с предыдущим днём, °C)
        - temp_drop (bool если падение <= -5°C)
        - melt_flag (bool если ранее был снег и сейчас temp > 0)
        - mud_flag (эвристика грязи)
        - dry_window (bool если нет осадков и влажность низкая)
        """
        if "list" not in self.raw:
            return []

        # группируем по дате
        normalized = {}
        for block in self.raw["list"]:
            dt_txt = block.get("dt_txt")
            if not dt_txt:
                # иногда есть поле dt (unix); fallback
                ts = block.get("dt")
                if ts:
                    import datetime
                    dt_txt = datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d 00:00:00")
                else:
                    continue

            day = dt_txt.split(" ")[0]
            entry = normalized.setdefault(day, {
                "temps": [],
                "humidity": [],
                "wind": [],
                "conditions": [],
                "rain_vol": []
            })

            # collect
            m = block.get("main", {})
            entry["temps"].append(m.get("temp", 0))
            entry["humidity"].append(m.get("humidity", 0))
            entry["wind"].append(block.get("wind", {}).get("speed", 0))

            for w in block.get("weather", []):
                entry["conditions"].append(w.get("main", ""))

            # rain/snow volumes
            rain = 0
            snow = 0
            if isinstance(block.get("rain"), dict):
                rain = block["rain"].get("3h", 0) or block["rain"].get("1h", 0) or 0
            if isinstance(block.get("snow"), dict):
                snow = block["snow"].get("3h", 0) or block["snow"].get("1h", 0) or 0
            entry["rain_vol"].append(rain + snow)

        # собираем в список с вычислениями
        dates = sorted(normalized.keys())
        result = []
        prev_temp = None
        prev_had_snow = False

        for date in dates:
            v = normalized[date]
            avg_temp = round((sum(v["temps"]) / len(v["temps"])) if v["temps"] else 0, 1)
            avg_humidity = round((sum(v["humidity"]) / len(v["humidity"])) if v["humidity"] else 0, 1)
            avg_wind = round((sum(v["wind"]) / len(v["wind"])) if v["wind"] else 0, 1)
            total_precip = sum(v["rain_vol"]) if v["rain_vol"] else 0
            rain_prob = 1 if total_precip > 0 else 0
            conds = list({c for c in v["conditions"] if c})  # unique non-empty

            # temp_delta relative to previous day
            temp_delta = None
            temp_drop = False
            if prev_temp is not None:
                temp_delta = round(avg_temp - prev_temp, 1)
                if temp_delta <= -5:
                    temp_drop = True

            # melt_flag: если ранее (предыдущий день) был снег и текущ temp > 0
            melt_flag = False
            if prev_had_snow and avg_temp > 0:
                melt_flag = True

            # mud_flag heuristic: высокий риск грязи если влажность высокая и были осадки или melt_flag
            mud_flag = False
            if (avg_humidity >= 75 and rain_prob == 1) or melt_flag:
                mud_flag = True

            # dry_window: если нет осадков и влажность невысока
            dry_window = False
            if rain_prob == 0 and avg_humidity < 70:
                dry_window = True

            # save whether this day had snow (for next day's melt detection)
            had_snow = any(("snow" in c.lower() for c in v["conditions"]))

            result.append({
                "date": date,
                "temp": avg_temp,
                "humidity": avg_humidity,
                "wind": avg_wind,
                "rain_prob": rain_prob,
                "conditions": conds,
                "temp_delta": temp_delta,
                "temp_drop": temp_drop,
                "melt_flag": melt_flag,
                "mud_flag": mud_flag,
                "dry_window": dry_window,
                "had_snow": had_snow
            })

            prev_temp = avg_temp
            prev_had_snow = had_snow

        return result

    # ----------------------------------------------------------------------
    # 2. ОСНОВНАЯ ЛОГИКА АНАЛИЗА
    # ----------------------------------------------------------------------

    def get_best_wash_day(self) -> Optional[Dict[str, Any]]:
        """
        Возвращает ЛУЧШИЙ день для мойки на основе критериев:
        - отсутствие дождя
        - влажность < 85%
        - температура > 0
        - ветер < 10 м/с
        """

        candidates = []

        for day in self.daily:
            if (
                day["rain_prob"] == 0 and
                day["humidity"] < 85 and
                day["temp"] > 0 and
                day["wind"] < 10
            ):
                candidates.append(day)

        if not candidates:
            return None

        # Чем меньше ветер, тем лучше
        candidates.sort(key=lambda x: (x["wind"], -x["temp"]))
        return candidates[0]

    # ----------------------------------------------------------------------

    def get_daily_summary(self) -> List[Dict[str, Any]]:
        """Возвращает краткую сводку по каждому дню."""
        return self.daily

    # ----------------------------------------------------------------------


	# ----------------------------------------------------------------------
    # Event integration
    # ----------------------------------------------------------------------
    def get_day_events(self, day: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Запускает все event-декторы на одном дне и возвращает список
        с результатами: [{'name':..., 'message':...}, ...]
        """
        detectors = [
            RainEvent(), SnowEvent(), MeltEvent(),
            MudEvent(), TemperatureDropEvent(), DryWindowEvent()
        ]
        triggered = []
        for d in detectors:
            try:
                if d.is_triggered(day):
                    triggered.append({"name": d.name, "message": d.get_message(day)})
            except Exception as e:
                # надёжность: не ломать весь анализ из-за одного детектора
                triggered.append({"name": d.name, "error": str(e)})
        return triggered


    def get_recommendation(self) -> str:
        """Готовая рекомендация пользователю."""

        day = self.get_best_wash_day()

        if not day:
            return "❌ Ближайшие дни не подходят для мойки — погода нестабильна."

        return (
            f"✔ Идеальный день для мойки: {day['date']}\n"
            f"• Температура: {day['temp']}°C\n"
            f"• Влажность: {day['humidity']}%\n"
            f"• Ветер: {day['wind']} м/с\n"
            f"• Условия: {', '.join(day['conditions'])}"
        )

     # ----------------------------------------------------------------------
     # New integration
     # ----------------------------------------------------------------------

    def get_current_weather(self) -> Dict[str, Any]:
        """Получает текущую погоду (первый период прогноза)"""
        if not self.raw or 'list' not in self.raw or len(self.raw['list']) == 0:
            return {}
        
        current = self.raw['list'][0]
        return {
            'temperature': current['main']['temp'] - 273.15,  # K to C
            'feels_like': current['main']['feels_like'] - 273.15,
            'humidity': current['main']['humidity'],
            'pressure': current['main']['pressure'],
            'wind_speed': current['wind']['speed'],
            'weather': current['weather'][0]['description'],
            'weather_main': current['weather'][0]['main'],
            'icon': current['weather'][0]['icon']
        }

    def get_today_forecast(self) -> Dict[str, Any]:
        """Получает прогноз на сегодня"""
        if not self.daily or len(self.daily) == 0:
            return {}
        
        return self.daily[0]

    def get_tomorrow_forecast(self) -> Dict[str, Any]:
        """Получает прогноз на завтра"""
        if not self.daily or len(self.daily) < 2:
            return {}
        
        return self.daily[1]

    def get_weather_alerts(self) -> List[str]:
        """Анализирует прогноз для выявления предупреждений"""
        alerts = []
        
        # Анализируем ближайшие 12 часов (4 периода по 3 часа)
        for period in self.raw.get('list', [])[:4]:
            weather_main = period.get('weather', [{}])[0].get('main', '').lower()
            temp = period.get('main', {}).get('temp', 0) - 273.15
            wind_speed = period.get('wind', {}).get('speed', 0)
            
            # Проверяем различные опасные условия
            if 'rain' in weather_main:
                alerts.append("🌧️ Ожидается дождь")
            elif 'snow' in weather_main:
                alerts.append("❄️ Ожидается снег")
            elif temp < 0:
                alerts.append("🧊 Температура ниже 0°C - возможен гололед!")
            elif 'thunderstorm' in weather_main:
                alerts.append("⚡ Возможна гроза")
            elif wind_speed > 10:
                alerts.append("💨 Сильный ветер")
        
        # Убираем дубликаты
        return list(set(alerts))

def get_detailed_recommendation(self) -> str:
    """Детальная рекомендация по мойке с обоснованием"""
    best_day = self.get_best_wash_day()
    
    if not best_day:
        return "❌ Не удалось определить лучший день для мойки"
    
    date = best_day.get('date', 'Неизвестно')
    
    # ИСПРАВЛЕНИЕ: безопасное получение температуры
    temp_data = best_day.get('temp', {})
    if isinstance(temp_data, dict):
        temp = temp_data.get('day', 0)
    else:
        temp = temp_data  # если это уже число
    
    weather_data = best_day.get('weather', [{}])
    weather = weather_data[0].get('description', 'Неизвестно') if weather_data else 'Неизвестно'
    humidity = best_day.get('humidity', 0)
    wind_speed = best_day.get('wind_speed', 0)
    
    recommendation = f"✅ *Лучший день для мойки: {date}*\n\n"
    recommendation += f"• 🌡 Температура: {temp:.1f}°C\n"
    recommendation += f"• ☁️ Погода: {weather}\n"
    recommendation += f"• 💧 Влажность: {humidity}%\n"
    recommendation += f"• 💨 Ветер: {wind_speed} м/с\n\n"
    
    # Добавляем обоснование
    if temp > 15:
        recommendation += "_Отличные условия - тепло и сухо_"
    elif temp > 5:
        recommendation += "_Хорошие условия, но может быть прохладно_"
    else:
        recommendation += "_Прохладно, но мойка возможна в теплом боксе_"
    
    return recommendation
