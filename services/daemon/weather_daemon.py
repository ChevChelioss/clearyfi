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
        daily_summary = analyzer.get_daily_summary()
        
        # Создаем улучшенное сообщение
        message = "🚗 *ClearyFi - Ваш персональный автоассистент*\n\n"
        message += f"📍 *Город:* {city}\n\n"
        
        # Главная рекомендация - выносим в начало
        best_day = analyzer.get_best_wash_day()
        if best_day:
            # Форматируем дату для красоты
            date_parts = best_day['date'].split('-')
            formatted_date = f"{date_parts[2]}.{date_parts[1]}"
            
            message += "✅ *РЕКОМЕНДУЕМ ПОМЫТЬ АВТО:*\n"
            message += f"📅 *Когда:* {formatted_date} ({get_day_name(best_day['date'])})\n"
            message += f"🌡 *Температура:* {best_day['temp']:.0f}°C\n"
            message += f"💧 *Влажность:* {best_day['humidity']:.0f}%\n"
            message += f"💨 *Ветер:* {best_day['wind']:.1f} м/с\n"
            message += f"☁️ *Погода:* {translate_weather_conditions(best_day['conditions'])}\n\n"
        else:
            message += "⚠️ *Внимание:* Идеальных дней для мойки не найдено\n\n"
        
        # Детальный прогноз на 3 дня
        message += "📊 *Прогноз на 3 дня:*\n\n"
        
        for i, day in enumerate(daily_summary[:3]):
            # Форматируем дату
            date_parts = day['date'].split('-')
            formatted_date = f"{date_parts[2]}.{date_parts[1]}"
            
            # Определяем статус для мойки
            wash_status, wash_description = get_wash_recommendation(day)
            
            # День недели
            day_name = get_day_name(day['date'])
            if i == 0:
                day_label = "Сегодня"
            elif i == 1:
                day_label = "Завтра" 
            else:
                day_label = day_name
            
            message += f"{wash_status} *{day_label} ({formatted_date})*\n"
            message += f"   {wash_description}\n"
            message += f"   🌡 {day['temp']:.0f}°C | 💧 {day['humidity']:.0f}% | 💨 {day['wind']:.1f} м/с\n"
            message += f"   ☁️ {translate_weather_conditions(day['conditions'])}\n\n"

        # Полезные советы в зависимости от погоды
        message += get_weather_tips(daily_summary[:3])
        
        message += "\n---\n"
        message += "🚗 *ClearyFi* - умные уведомления для вашего авто"

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

def translate_weather_conditions(conditions):
    """Переводит погодные условия на русский язык"""
    translation_map = {
        'Clear': 'Ясно',
        'Clouds': 'Облачно',
        'Rain': 'Дождь',
        'Drizzle': 'Морось',
        'Thunderstorm': 'Гроза',
        'Snow': 'Снег',
        'Mist': 'Туман',
        'Fog': 'Туман'
    }
    
    translated = []
    for condition in conditions:
        if condition in translation_map:
            translated.append(translation_map[condition])
        else:
            translated.append(condition)
    
    return ', '.join(translated) if translated else 'Ясно'

def get_day_name(date_str):
    """Возвращает название дня недели на русском"""
    days = {
        'Monday': 'Понедельник',
        'Tuesday': 'Вторник',
        'Wednesday': 'Среда',
        'Thursday': 'Четверг',
        'Friday': 'Пятница',
        'Saturday': 'Суббота',
        'Sunday': 'Воскресенье'
    }
    
    try:
        from datetime import datetime
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        english_day = date_obj.strftime('%A')
        return days.get(english_day, date_str)
    except:
        return date_str

def get_wash_recommendation(day_data):
    """Определяет рекомендацию по мойке для дня"""
    temp = day_data.get('temp', 0)
    rain_prob = day_data.get('rain_prob', 0)
    humidity = day_data.get('humidity', 0)
    wind = day_data.get('wind', 0)
    
    # Идеальные условия
    if rain_prob == 0 and temp > 5 and humidity < 80 and wind < 8:
        return "✅", "Отличный день для мойки"
    
    # Хорошие условия
    elif rain_prob == 0 and temp > 0 and humidity < 85:
        return "⚠️", "Можно помыть, но будет прохладно"
    
    # Плохие условия - дождь
    elif rain_prob > 0:
        return "❌", "Не рекомендуется: ожидаются осадки"
    
    # Плохие условия - холодно
    elif temp <= 0:
        return "❌", "Не рекомендуется: возможен лед"
    
    # Плохие условия - ветер
    elif wind >= 8:
        return "❌", "Не рекомендуется: сильный ветер"
    
    # Плохие условия - влажность
    elif humidity >= 85:
        return "❌", "Не рекомендуется: высокая влажность"
    
    else:
        return "⚠️", "Условно подходит для мойки"

def get_weather_tips(days_forecast):
    """Возвращает полезные советы на основе прогноза"""
    tips = []
    
    # Проверяем наличие дождя
    rainy_days = [day for day in days_forecast if day.get('rain_prob', 0) > 0]
    if rainy_days:
        tips.append("🌧️ *Совет:* В дождливые дни мойку лучше отложить")
    
    # Проверяем холодные дни
    cold_days = [day for day in days_forecast if day.get('temp', 0) <= 0]
    if cold_days:
        tips.append("🧊 *Совет:* При температуре ниже 0°C возможен гололед")
    
    # Проверяем ветреные дни
    windy_days = [day for day in days_forecast if day.get('wind', 0) >= 8]
    if windy_days:
        tips.append("💨 *Совет:* В ветреную погоду на машину быстро садится пыль")
    
    # Если все дни хорошие
    good_days = [day for day in days_forecast if day.get('rain_prob', 0) == 0 and day.get('temp', 0) > 5]
    if len(good_days) >= 2:
        tips.append("👍 *Совет:* Отличная неделя для ухода за автомобилем!")
    
    if tips:
        return "💡 *Полезные советы:*\n" + "\n".join(f"• {tip}" for tip in tips) + "\n\n"
    else:
        return ""
