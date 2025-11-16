#!/usr/bin/env python3
import sys
import os
import time
import logging
import traceback
from typing import Dict

# Добавляем корень проекта в sys.path
PROJECT_ROOT = "/data/data/com.termux/files/home/projects/clearyfi"
sys.path.insert(0, PROJECT_ROOT)

print(f"🚀 Демон запускается...")
print(f"📁 PROJECT_ROOT: {PROJECT_ROOT}")
print(f"📁 Текущая директория: {os.getcwd()}")

try:
    # Импортируем все модули
    from services.storage.subscriber_db import SubscriberDBConnection
    from services.weather.weather_api_client import WeatherAPIClient
    from core.weather_analyzer import WeatherAnalyzer
    from core.recommendation_engine import RecommendationEngine
    import telebot
    from config.settings import settings
    from services.daemon.daemon_manager import DaemonManager
    
    print("✅ Все модули успешно импортированы!")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print(f"🔍 Детали ошибки:")
    traceback.print_exc()
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    handlers=[
        logging.FileHandler("weather_daemon.log"),
        logging.StreamHandler()
    ]
)

bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN)

def send_recommendation(chat_id: int, city: str):
    """Отправка рекомендации пользователю на основе прогноза погоды"""
    try:
        logging.info(f"📨 Отправляем уведомление для {city} (chat_id: {chat_id})")

        # Получаем прогноз на 3 дня
        from config.settings import settings
        weather_client = WeatherAPIClient(api_key=settings.OPENWEATHER_API_KEY)
        forecast = weather_client.get_forecast(city, days=3)

        if not forecast:
            logging.warning(f"Не удалось получить прогноз для {city}")
            return False

        # Дополнительная проверка структуры данных
        if "list" not in forecast:
            logging.warning(f"Некорректная структура данных для {city}")
            return False

        # Анализируем прогноз
        analyzer = WeatherAnalyzer(forecast)
        
        # ПОЛУЧАЕМ ДЕТАЛЬНУЮ ИНФОРМАЦИЮ О ДНЯХ
        daily_summary = analyzer.get_daily_summary()
        
        # Формируем улучшенное сообщение
        message = f"🌤 *Прогноз для {city} на 3 дня:*\n\n"
        
        # Анализируем каждый день и даем рекомендации
        for i, day in enumerate(daily_summary[:3]):
            date = day.get('date', 'Unknown')
            temp = day.get('temp', 0)
            humidity = day.get('humidity', 0)
            wind = day.get('wind', 0)
            rain_prob = day.get('rain_prob', 0)
            conditions = ', '.join(day.get('conditions', ['ясно']))
            
            # Определяем, подходит ли день для мойки
            wash_suitable = "✅" if (
                rain_prob == 0 and 
                humidity < 85 and 
                temp > 0 and 
                wind < 10
            ) else "⚠️" if (
                rain_prob == 0 and 
                temp > -5
            ) else "❌"
            
            wash_reason = ""
            if wash_suitable == "✅":
                wash_reason = " - хороший день для мойки"
            elif wash_suitable == "⚠️":
                wash_reason = " - можно помыть с осторожностью"
            else:
                reasons = []
                if rain_prob > 0:
                    reasons.append("ожидаются осадки")
                if temp <= 0:
                    reasons.append("температура низкая")
                if humidity >= 85:
                    reasons.append("высокая влажность")
                if wind >= 10:
                    reasons.append("сильный ветер")
                wash_reason = f" - не рекомендуется: {', '.join(reasons)}"
            
            day_label = "Сегодня" if i == 0 else "Завтра" if i == 1 else f"Послезавтра"
            message += (
                f"{wash_suitable} *{day_label} ({date})*:\n"
                f"   🌡 {temp}°C, 💧 {humidity}%, 💨 {wind} м/с\n"
                f"   ☁️ {conditions}\n"
                f"   {wash_reason}\n\n"
            )
            message += (
                f"{wash_suitable} *{day_label} ({date})*:\n"
                f"   🌡 {temp}°C, 💧 {humidity}%, 💨 {wind} м/с\n"
                f"   ☁️ {conditions}\n"
                f"   {wash_reason}\n\n"
            )

        # Добавляем общую рекомендацию
        best_day = analyzer.get_best_wash_day()
        if best_day:
            message += f"🎯 *Лучший день для мойки:* {best_day['date']}\n"
        else:
            message += "💡 *Совет:* Если срочно нужно помыть машину, выбирайте день без осадков\n"

        message += "\n🚗 _ClearyFi - ваш умный автоассистент_"

        # Отправляем через бота
        bot.send_message(
            chat_id,
            message,
            parse_mode='Markdown'
        )

        logging.info(f"✅ Уведомление отправлено для {city}")
        return True

    except Exception as e:
        logging.error(f"❌ Ошибка отправки для {city}: {e}")
        logging.debug(traceback.format_exc())
        return False

def run_daemon():
    """Основной цикл демона"""
    try:
        DaemonManager.init_settings()
        logging.info("🚀 Демон уведомлений запущен!")
        
        while True:
            interval_hours = DaemonManager.get_interval()
            logging.info(f"🔍 Проверяем подписчиков...")
            
            # Получаем всех активных подписчиков
            with SubscriberDBConnection() as db:
                users = db.get_all_active_users()
                
            logging.info(f"📋 Найдено активных подписчиков: {len(users)}")
            
            # Отправляем уведомления каждому подписчику
            success_count = 0
            for user in users:
                try:
                    if send_recommendation(user["chat_id"], user["city"]):
                        success_count += 1
                    # Небольшая задержка между отправками
                    time.sleep(1)
                except Exception as e:
                    logging.error(f"Ошибка обработки пользователя {user}: {e}")
                    continue
            
            logging.info(f"✅ Успешно отправлено: {success_count}/{len(users)}")
            logging.info(f"⏳ Следующая проверка через {interval_hours} часов")
            
            # Ожидаем до следующей проверки
            time.sleep(interval_hours * 3600)
            
    except Exception as e:
        logging.error(f"❌ Критическая ошибка в демоне: {e}")
        logging.debug(traceback.format_exc())
        # Ждем 5 минут перед повторной попыткой
        time.sleep(300)

if __name__ == "__main__":
    run_daemon()
