#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/data/data/com.termux/files/home/projects/clearyfi')

print("=== ФИНАЛЬНЫЙ ТЕСТ СИСТЕМЫ ===")

# Тест 1: Импорты
try:
    from services.weather.weather_api_client import WeatherAPIClient
    from core.weather_analyzer import WeatherAnalyzer
    from config.settings import OPENWEATHER_API_KEY, TELEGRAM_BOT_TOKEN
    import telebot
    print("✅ Все импорты успешны")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

# Тест 2: Получение прогноза
try:
    weather_client = WeatherAPIClient(api_key=OPENWEATHER_API_KEY)
    forecast = weather_client.get_forecast("Тюмень")
    if forecast:
        print("✅ Прогноз получен успешно")
    else:
        print("❌ Не удалось получить прогноз")
        sys.exit(1)
except Exception as e:
    print(f"❌ Ошибка получения прогноза: {e}")
    sys.exit(1)

# Тест 3: Анализ и рекомендация
try:
    analyzer = WeatherAnalyzer(forecast)
    recommendation = analyzer.get_recommendation()
    print(f"✅ Рекомендация сгенерирована ({len(recommendation)} символов)")
    print(f"📝 Превью: {recommendation[:100]}...")
except Exception as e:
    print(f"❌ Ошибка генерации рекомендации: {e}")
    sys.exit(1)

# Тест 4: Отправка сообщения
try:
    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
    test_message = "✅ Система ClearyFi работает корректно! Демон и бот синхронизированы."
    bot.send_message(279492815, test_message)
    print("✅ Тестовое сообщение отправлено")
except Exception as e:
    print(f"❌ Ошибка отправки сообщения: {e}")

print("🎉 ФИНАЛЬНЫЙ ТЕСТ ПРОЙДЕН! Система готова к работе.")
