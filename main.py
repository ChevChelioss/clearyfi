from config.settings import OPENWEATHER_API_KEY
from services.weather.weather_api_client import WeatherAPIClient
from core.weather_analyzer import WeatherAnalyzer


def main():
    city = "Москва"

    api = WeatherAPIClient(api_key=OPENWEATHER_API_KEY)
    forecast = api.get_forecast(city)

    if not forecast:
        print("Ошибка получения данных")
        return

    analyzer = WeatherAnalyzer(forecast)

    print("\nСводка по дням:")
    for d in analyzer.get_daily_summary():
        print(d)

    print("\nРекомендация:")
    print(analyzer.get_recommendation())


if __name__ == "__main__":
    main()
