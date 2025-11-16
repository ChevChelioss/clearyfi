from core.weather_analyzer import WeatherAnalyzer
import json

# загрузим пример тестового прогноза из файла или API позже
sample = json.loads(open("sample_forecast.json").read())

wa = WeatherAnalyzer(sample)

print("Сводка:")
print(wa.get_daily_summary())

print("\nРекомендация:")
print(wa.get_recommendation())
