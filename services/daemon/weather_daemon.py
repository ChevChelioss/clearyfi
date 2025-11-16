#!/usr/bin/env python3
"""
ClearyFi Weather Notification Daemon
Автоматическая система уведомлений о погоде для владельцев автомобилей.
"""

import sys
import os
import time
import logging
import traceback
from typing import Dict, List, Tuple, Optional

# =============================================================================
# КОНФИГУРАЦИЯ ПУТЕЙ И ИМПОРТОВ
# =============================================================================

# Добавляем корень проекта в sys.path для корректного импорта модулей
PROJECT_ROOT = "/data/data/com.termux/files/home/projects/clearyfi"
sys.path.insert(0, PROJECT_ROOT)

print(f"🚀 Демон уведомлений запускается...")
print(f"📁 PROJECT_ROOT: {PROJECT_ROOT}")
print(f"📁 Текущая директория: {os.getcwd()}")

try:
    # Импортируем все необходимые модули
    from services.storage.subscriber_db import SubscriberDBConnection
    from services.weather.weather_api_client import WeatherAPIClient
    from core.weather_analyzer import WeatherAnalyzer
    import telebot
    from config.settings import settings
    from services.daemon.daemon_manager import DaemonManager
    
    print("✅ Все модули успешно импортированы!")
    
except ImportError as e:
    print(f"❌ Критическая ошибка импорта: {e}")
    print(f"🔍 Детали ошибки:")
    traceback.print_exc()
    sys.exit(1)

# =============================================================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    handlers=[
        logging.FileHandler("weather_daemon.log"),  # Логи в файл
        logging.StreamHandler()  # Логи в консоль
    ]
)

# Инициализируем Telegram бота
bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN)

# =============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================================

def translate_weather_conditions(conditions: List[str]) -> str:
    """
    Переводит английские названия погодных условий на русский язык.
    
    Args:
        conditions: Список погодных условий от API (на английском)
        
    Returns:
        Строка с перечислением условий на русском языке
    """
    translation_map = {
        'Clear': 'Ясно',
        'Clouds': 'Облачно',
        'Rain': 'Дождь',
        'Drizzle': 'Морось',
        'Thunderstorm': 'Гроза',
        'Snow': 'Снег',
        'Mist': 'Туман',
        'Fog': 'Туман',
        'Haze': 'Дымка'
    }
    
    translated = []
    for condition in conditions:
        # Используем перевод если доступен, иначе оставляем оригинал
        translated_condition = translation_map.get(condition, condition)
        translated.append(translated_condition)
    
    return ', '.join(translated) if translated else 'Ясно'


def get_day_name(date_str: str) -> str:
    """
    Преобразует дату в формате YYYY-MM-DD в название дня недели на русском.
    
    Args:
        date_str: Строка с датой в формате ГГГГ-ММ-ДД
        
    Returns:
        Название дня недели на русском языке
    """
    days_mapping = {
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
        # Парсим дату из строки
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        # Получаем английское название дня недели
        english_day = date_obj.strftime('%A')
        # Возвращаем русский перевод
        return days_mapping.get(english_day, date_str)
    except (ValueError, TypeError) as e:
        logging.warning(f"Ошибка преобразования даты '{date_str}': {e}")
        return date_str


def get_wash_recommendation(day_data: Dict) -> Tuple[str, str]:
    """
    Определяет рекомендацию по мойке автомобиля на основе погодных данных.
    Условия смягчены для более реалистичных рекомендаций в российском климате.
    """
    temp = day_data.get('temp', 0)
    rain_prob = day_data.get('rain_prob', 0)
    humidity = day_data.get('humidity', 0)
    wind = day_data.get('wind', 0)
    
    # 🔄 СМЯГЧЕННЫЕ КРИТЕРИИ ОЦЕНКИ ДЛЯ МОЙКИ:
    
    # 1. ОТЛИЧНЫЕ условия
    if rain_prob == 0 and temp >= 10 and humidity <= 75 and wind < 8:
        return "🌟", "Идеальный день для мойки"
    elif rain_prob == 0 and temp >= 3 and humidity <= 85 and wind < 12:
        return "✅", "Хороший день для мойки"
    
    # 2. УСЛОВНО ПОДХОДЯЩИЕ условия
    elif rain_prob == 0 and temp >= -2 and humidity <= 90:
        if temp < 3:
            return "⚠️", "Можно помыть, но будет прохладно"
        elif humidity > 85:
            return "⚠️", "Можно помыть, но сохнуть будет дольше"
        elif wind >= 8:
            return "⚠️", "Можно помыть, но ветрено"
        else:
            return "⚠️", "Условно подходит для мойки"
    
    # 3. НЕРЕКОМЕНДУЕМЫЕ условия
    
    # Главный запрещающий фактор - осадки
    elif rain_prob > 0:
        precipitation_type = "дождь" if temp > 0 else "снег"
        return "❌", f"Не рекомендуется: ожидается {precipitation_type}"
    
    # Сильный ветер
    elif wind >= 12:
        return "❌", "Не рекомендуется: сильный ветер"
    
    # Очень высокая влажность
    elif humidity > 90:
        return "❌", "Не рекомендуется: очень высокая влажность"
    
    # Слишком холодно
    elif temp < -2:
        return "❌", "Не рекомендуется: возможен лед"
    
    # 4. НЕОПРЕДЕЛЕННЫЕ условия
    else:
        return "❓", "Сложные погодные условия"


def get_weather_tips(days_forecast: List[Dict]) -> str:
    """
    Возвращает полезные советы на основе прогноза с учетом СМЯГЧЕННЫХ критериев.
    """
    tips = []
    
    # Анализируем прогноз для выявления ключевых паттернов
    
    # Паттерн 1: Дождливые дни (сохраняем - осадки всегда проблема)
    rainy_days = [day for day in days_forecast if day.get('rain_prob', 0) > 0]
    if rainy_days:
        rainy_count = len(rainy_days)
        if rainy_count >= 2:
            tips.append("🌧️ *Совет:* Несколько дождливых дней - мойку лучше отложить")
        else:
            tips.append("🌧️ *Совет:* В дождливые дни мойку лучше отложить")
    
    # Паттерн 2: Холодные дни (обновляем критерий с -2°C)
    cold_days = [day for day in days_forecast if day.get('temp', 0) < -2]
    if cold_days:
        tips.append("🧊 *Совет:* При температуре ниже -2°C возможен лед на дорогах")
    
    # Паттерн 3: Ветреные дни (обновляем критерий с 12 м/с)
    windy_days = [day for day in days_forecast if day.get('wind', 0) >= 12]
    if windy_days:
        tips.append("💨 *Совет:* В сильный ветер машина быстро покрывается пылью")
    
    # Паттерн 4: Благоприятный период (обновляем критерии)
    good_days = [day for day in days_forecast if 
                day.get('rain_prob', 0) == 0 and 
                day.get('temp', 0) >= 3 and
                day.get('humidity', 0) <= 85 and
                day.get('wind', 0) < 12]
    
    if len(good_days) >= 2:
        tips.append("👍 *Совет:* Отличные дни для ухода за автомобилем!")
    elif len(good_days) == 1:
        tips.append("👌 *Совет:* Есть подходящий день для мойки")
    
    # Паттерн 5: Высокая влажность (новый паттерн)
    humid_days = [day for day in days_forecast if day.get('humidity', 0) > 90]
    if humid_days:
        tips.append("💧 *Совет:* Высокая влажность - машина будет долго сохнуть")
    
    # Паттерн 6: Идеальные условия (новый паттерн)
    perfect_days = [day for day in days_forecast if 
                   day.get('rain_prob', 0) == 0 and 
                   day.get('temp', 0) >= 10 and
                   day.get('humidity', 0) <= 75 and
                   day.get('wind', 0) < 8]
    
    if perfect_days:
        tips.append("🌟 *Совет:* Идеальные условия для мойки и ухода за авто!")
    
    # Форматируем советы если они есть
    if tips:
        tips_text = "💡 *Полезные советы:*\n" + "\n".join(f"• {tip}" for tip in tips) + "\n\n"
        return tips_text
    else:
        return ""

def calculate_day_score(day_data: Dict) -> int:
    """
    Рассчитывает балл дня для мойки (0-10).
    Чем выше балл - тем лучше условия.
    """
    score = 0
    
    temp = day_data.get('temp', 0)
    rain_prob = day_data.get('rain_prob', 0)
    humidity = day_data.get('humidity', 0)
    wind = day_data.get('wind', 0)
    
    # Баллы за температуру
    if temp >= 15: score += 3
    elif temp >= 10: score += 2
    elif temp >= 3: score += 1
    elif temp >= -2: score += 0
    else: score -= 2
    
    # Баллы за осадки
    if rain_prob == 0: score += 3
    else: score -= 3
    
    # Баллы за влажность
    if humidity <= 70: score += 2
    elif humidity <= 80: score += 1
    elif humidity <= 90: score += 0
    else: score -= 1
    
    # Баллы за ветер
    if wind < 5: score += 2
    elif wind < 8: score += 1
    elif wind < 12: score += 0
    else: score -= 1
    
    return max(0, min(10, score))  # Ограничиваем диапазон 0-10


# =============================================================================
# ОСНОВНЫЕ ФУНКЦИИ ДЕМОНА
# =============================================================================

def send_recommendation(chat_id: int, city: str) -> bool:
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
            # 🔥 ДОБАВЛЯЕМ РАСЧЕТ БАЛЛА ЗДЕСЬ:
            day_score = calculate_day_score(day)
            day['wash_score'] = day_score  # Сохраняем для возможного использования
            
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
    """
    Основной цикл работы демона уведомлений.
    
    Бесконечный цикл который:
    1. Проверяет активных подписчиков
    2. Отправляет им уведомления
    3. Ожидает заданный интервал
    4. Обрабатывает ошибки и восстанавливается
    """
    try:
        # Инициализация настроек демона
        DaemonManager.init_settings()
        logging.info("🚀 Демон уведомлений запущен!")

        # Основной рабочий цикл
        while True:
            # Получаем интервал между проверками (в часах)
            interval_hours = DaemonManager.get_interval()
            logging.info(f"🔍 Проверяем подписчиков...")
            
            # Получаем список всех активных подписчиков
            with SubscriberDBConnection() as db:
                users = db.get_all_active_users()
                
            logging.info(f"📋 Найдено активных подписчиков: {len(users)}")
            
            # Отправляем уведомления каждому подписчику
            success_count = 0
            for user in users:
                try:
                    if send_recommendation(user["chat_id"], user["city"]):
                        success_count += 1
                    # Задержка между отправками чтобы не превысить лимиты Telegram API
                    time.sleep(1)
                except Exception as e:
                    logging.error(f"❌ Ошибка обработки пользователя {user}: {e}")
                    continue
            
            # Логируем результаты итерации
            logging.info(f"✅ Успешно отправлено: {success_count}/{len(users)}")
            logging.info(f"⏳ Следующая проверка через {interval_hours} часов")
            
            # Ожидаем до следующей проверки (переводим часы в секунды)
            time.sleep(interval_hours * 3600)
            
    except Exception as e:
        # Обработка критических ошибок - логируем и перезапускаем через 5 минут
        logging.error(f"❌ Критическая ошибка в демоне: {e}")
        logging.debug(traceback.format_exc())
        logging.info("🔄 Попытка перезапуска через 5 минут...")
        time.sleep(300)  # 5 минут


# =============================================================================
# ТОЧКА ВХОДА
# =============================================================================

if __name__ == "__main__":
    """
    Точка входа при запуске скрипта напрямую.
    Запускает основной цикл демона.
    """
    run_daemon()
