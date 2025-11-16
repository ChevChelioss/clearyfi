# run_local_events_test.py
import json
from core.weather_analyzer import WeatherAnalyzer

# Загружаем пример прогноза
with open("sample_forecast.json", "r", encoding="utf-8") as f:
    sample = json.load(f)

# Создаём анализатор
wa = WeatherAnalyzer(sample)

# wa.daily — нормализованный список дней
print("\n=== Daily summary ===")
for d in wa.daily:
    print(f"{d['date']}: temp={d['temp']}°C, hum={d['humidity']}%, wind={d['wind']} m/s, rain_prob={d['rain_prob']}, cond={d['conditions']}")

# Печатаем события по дню
print("\n=== Events detected ===")
for d in wa.daily:
    evs = wa.get_day_events(d)
    print(f"\n{d['date']}:")
    if not evs:
        print("  (no events)")
    for e in evs:
        if "message" in e:
            print(f"  - {e['name']}: {e['message']}")
        else:
            print(f"  - {e['name']}: ERROR: {e.get('error')}")
