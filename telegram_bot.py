import logging
import telebot
from telebot.types import Message
from typing import Dict, Any, List

from services.storage.subscriber_db import SubscriberDBConnection
from services.weather.weather_api_client import WeatherAPIClient
from core.weather_analyzer import WeatherAnalyzer
from config.settings import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN)
pending_city_input = {}

# -----------------------------------------------------------------------------
# /start - Начало работы
# -----------------------------------------------------------------------------
@bot.message_handler(commands=['start'])
def cmd_start(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username

    with SubscriberDBConnection() as db:
        user = db.get_user_by_chat_id(chat_id)
        if user is None or user["city"] is None:
            bot.send_message(chat_id, 
                "👋 *Добро пожаловать в ClearyFi!*\n\n"
                "Я помогу вам с рекомендациями по мойке автомобиля на основе прогноза погоды.\n\n"
                "📝 *Для начала работы введите ваш город:*",
                parse_mode='Markdown'
            )
            db.add_or_update_user(user_id, chat_id, username)
            pending_city_input[chat_id] = True
            return

        bot.send_message(
            chat_id,
            "👋 *С возвращением в ClearyFi!*\n\n"
            f"🏙️ Ваш город: {user['city']}\n\n"
            "*🚀 Доступные команды:*\n"
            "/now - Погода прямо сейчас\n"
            "/today - Прогноз на сегодня\n" 
            "/tomorrow - Что ожидает завтра\n"
            "/wash - Рекомендация по мойке\n"
            "/alerts - Погодные предупреждения\n"
            "/status - Ваши настройки\n"
            "/city - Сменить город\n\n"
            "_📧 Вы также получаете ежедневные уведомления с прогнозами_",
            parse_mode='Markdown'
        )

# -----------------------------------------------------------------------------
# /status - Статус пользователя
# -----------------------------------------------------------------------------
@bot.message_handler(commands=['status'])
def cmd_status(message: Message):
    chat_id = message.chat.id
    
    with SubscriberDBConnection() as db:
        user = db.get_user_by_chat_id(chat_id)
        
        if not user or not user.get("city"):
            bot.send_message(chat_id, 
                "❌ *Вы еще не настроили бота*\n\n"
                "Используйте /start чтобы начать работу.",
                parse_mode='Markdown'
            )
            return
            
        status_text = (
            "📊 *Ваш статус в ClearyFi:*\n\n"
            f"🏙️ *Город:* {user['city']}\n"
            f"🔔 *Уведомления:* {'✅ ВКЛ' if user.get('is_active', 1) else '❌ ВЫКЛ'}\n"
            f"⏰ *Время уведомлений:* {user.get('notification_time', '09:00')}\n\n"
            "_Используйте /city чтобы изменить город_"
        )
        
        bot.send_message(chat_id, status_text, parse_mode='Markdown')

# -----------------------------------------------------------------------------
# /now - Текущая погода
# -----------------------------------------------------------------------------
@bot.message_handler(commands=['now'])
def cmd_now(message: Message):
    chat_id = message.chat.id
    
    with SubscriberDBConnection() as db:
        user = db.get_user_by_chat_id(chat_id)
        if not user or not user.get("city"):
            bot.send_message(chat_id, "❌ Сначала укажите город через /start")
            return
            
    try:
        weather_client = WeatherAPIClient(api_key=settings.OPENWEATHER_API_KEY)
        forecast = weather_client.get_forecast(user["city"])
        
        if forecast:
            analyzer = WeatherAnalyzer(forecast)
            current = analyzer.get_current_weather()
            
            if current:
                # Получаем emoji для погоды
                weather_emoji = get_weather_emoji(current['weather_main'])
                
                message_text = (
                    f"{weather_emoji} *Погода сейчас в {user['city']}:*\n\n"
                    f"🌡 *Температура:* {current['temperature']:.1f}°C\n"
                    f"🎯 *Ощущается как:* {current['feels_like']:.1f}°C\n"
                    f"💧 *Влажность:* {current['humidity']}%\n"
                    f"📊 *Давление:* {current['pressure']} гПа\n"
                    f"💨 *Ветер:* {current['wind_speed']} м/с\n"
                    f"☁️ *Состояние:* {current['weather']}\n\n"
                    f"_Обновлено: сейчас_"
                )
                
                bot.send_message(chat_id, message_text, parse_mode='Markdown')
            else:
                bot.send_message(chat_id, "❌ Не удалось получить текущую погоду")
        else:
            bot.send_message(chat_id, "❌ Не удалось получить данные о погоде")
            
    except Exception as e:
        logging.error(f"Ошибка команды now: {e}")
        bot.send_message(chat_id, "❌ Ошибка при получении погоды")

# -----------------------------------------------------------------------------
# /today - Прогноз на сегодня
# -----------------------------------------------------------------------------
@bot.message_handler(commands=['today'])
def cmd_today(message: Message):
    chat_id = message.chat.id
    
    with SubscriberDBConnection() as db:
        user = db.get_user_by_chat_id(chat_id)
        if not user or not user.get("city"):
            bot.send_message(chat_id, "❌ Сначала укажите город через /start")
            return
            
    try:
        weather_client = WeatherAPIClient(api_key=settings.OPENWEATHER_API_KEY)
        forecast = weather_client.get_forecast(user["city"])
        
        if forecast:
            analyzer = WeatherAnalyzer(forecast)
            today = analyzer.get_today_forecast()
            
            if today:
                recommendation = get_daily_recommendation(today, "сегодня")
                
                message_text = (
                    f"📅 *Прогноз на сегодня для {user['city']}:*\n\n"
                    f"{recommendation}"
                )
                
                bot.send_message(chat_id, message_text, parse_mode='Markdown')
            else:
                bot.send_message(chat_id, "❌ Не удалось получить прогноз на сегодня")
        else:
            bot.send_message(chat_id, "❌ Не удалось получить данные о погоде")
            
    except Exception as e:
        logging.error(f"Ошибка команды today: {e}")
        bot.send_message(chat_id, "❌ Ошибка при получении прогноза")

# -----------------------------------------------------------------------------
# /tomorrow - Прогноз на завтра
# -----------------------------------------------------------------------------
@bot.message_handler(commands=['tomorrow'])
def cmd_tomorrow(message: Message):
    chat_id = message.chat.id
    
    with SubscriberDBConnection() as db:
        user = db.get_user_by_chat_id(chat_id)
        if not user or not user.get("city"):
            bot.send_message(chat_id, "❌ Сначала укажите город через /start")
            return
            
    try:
        weather_client = WeatherAPIClient(api_key=settings.OPENWEATHER_API_KEY)
        forecast = weather_client.get_forecast(user["city"])
        
        if forecast:
            analyzer = WeatherAnalyzer(forecast)
            tomorrow = analyzer.get_tomorrow_forecast()
            
            if tomorrow:
                recommendation = get_daily_recommendation(tomorrow, "завтра")
                
                message_text = (
                    f"📅 *Прогноз на завтра для {user['city']}:*\n\n"
                    f"{recommendation}"
                )
                
                bot.send_message(chat_id, message_text, parse_mode='Markdown')
            else:
                bot.send_message(chat_id, "❌ Не удалось получить прогноз на завтра")
        else:
            bot.send_message(chat_id, "❌ Не удалось получить данные о погоде")
            
    except Exception as e:
        logging.error(f"Ошибка команды tomorrow: {e}")
        bot.send_message(chat_id, "❌ Ошибка при получении прогноза")

# -----------------------------------------------------------------------------
# /wash - Рекомендация по мойке
# -----------------------------------------------------------------------------
@bot.message_handler(commands=['wash'])
def cmd_wash(message: Message):
    chat_id = message.chat.id
    
    with SubscriberDBConnection() as db:
        user = db.get_user_by_chat_id(chat_id)
        if not user or not user.get("city"):
            bot.send_message(chat_id, "❌ Сначала укажите город через /start")
            return
            
    try:
        weather_client = WeatherAPIClient(api_key=settings.OPENWEATHER_API_KEY)
        forecast = weather_client.get_forecast(user["city"])
        
        if forecast:
            analyzer = WeatherAnalyzer(forecast)
            recommendation = analyzer.get_detailed_recommendation()
            
            message_text = (
                f"🚗 *Рекомендация по мойке для {user['city']}:*\n\n"
                f"{recommendation}"
            )
            
            bot.send_message(chat_id, message_text, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "❌ Не удалось получить прогноз")
            
    except Exception as e:
        logging.error(f"Ошибка команды wash: {e}")
        bot.send_message(chat_id, "❌ Ошибка при анализе погоды")

# -----------------------------------------------------------------------------
# /alerts - Погодные предупреждения
# -----------------------------------------------------------------------------
@bot.message_handler(commands=['alerts'])
def cmd_alerts(message: Message):
    chat_id = message.chat.id
    
    with SubscriberDBConnection() as db:
        user = db.get_user_by_chat_id(chat_id)
        if not user or not user.get("city"):
            bot.send_message(chat_id, "❌ Сначала укажите город через /start")
            return
            
    try:
        weather_client = WeatherAPIClient(api_key=settings.OPENWEATHER_API_KEY)
        forecast = weather_client.get_forecast(user["city"])
        
        if forecast:
            analyzer = WeatherAnalyzer(forecast)
            alerts = analyzer.get_weather_alerts()
            
            if alerts:
                message_text = f"⚠️ *Погодные предупреждения для {user['city']}:*\n\n" + "\n".join(alerts)
            else:
                message_text = f"✅ *В {user['city']} особых предупреждений нет*\n\n_Погодные условия стабильные_"
                
            bot.send_message(chat_id, message_text, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "❌ Не удалось получить прогноз")
            
    except Exception as e:
        logging.error(f"Ошибка команды alerts: {e}")
        bot.send_message(chat_id, "❌ Ошибка при анализе погоды")

# -----------------------------------------------------------------------------
# /city - Смена города
# -----------------------------------------------------------------------------
@bot.message_handler(commands=['city'])
def cmd_city(message: Message):
    chat_id = message.chat.id
    pending_city_input[chat_id] = True
    bot.send_message(chat_id, 
        "🏙️ *Введите новый город:*\n\n"
        "_Например: Москва, Санкт-Петербург, Екатеринбург_",
        parse_mode='Markdown'
    )

# -----------------------------------------------------------------------------
# Ввод города
# -----------------------------------------------------------------------------
@bot.message_handler(func=lambda msg: msg.chat.id in pending_city_input)
def set_city(message: Message):
    chat_id = message.chat.id
    text = message.text.strip()
    user_id = message.from_user.id

    if not text:
        bot.send_message(chat_id, "❌ Пожалуйста, введите корректное название города:")
        return

    # Проверяем город через API
    weather_client = WeatherAPIClient(api_key=settings.OPENWEATHER_API_KEY)
    if not weather_client.is_city_valid(text):
        bot.send_message(chat_id, 
            f"❌ *Город '{text}' не найден*\n\n"
            "Пожалуйста, проверьте написание и введите город еще раз:",
            parse_mode='Markdown'
        )
        return

    # Сохраняем город в базу
    with SubscriberDBConnection() as db:
        db.update_user_city(user_id, text)

    del pending_city_input[chat_id]
    
    bot.send_message(
        chat_id,
        f"✅ *Отлично! Город '{text}' сохранен!*\n\n"
        "📧 Вы будете получать ежедневные уведомления с прогнозом погоды "
        "и рекомендациями по мойке автомобиля.\n\n"
        "*🚀 Теперь можете использовать команды:*\n"
        "/now - Погода сейчас\n"
        "/today - Прогноз на сегодня\n"
        "/wash - Рекомендация по мойке\n"
        "/alerts - Погодные предупреждения",
        parse_mode='Markdown'
    )

# -----------------------------------------------------------------------------
# Вспомогательные функции
# -----------------------------------------------------------------------------
def get_weather_emoji(weather_main: str) -> str:
    """Возвращает emoji для типа погоды"""
    emoji_map = {
        'Clear': '☀️',
        'Clouds': '☁️',
        'Rain': '🌧️',
        'Drizzle': '🌦️',
        'Thunderstorm': '⛈️',
        'Snow': '❄️',
        'Mist': '🌫️',
        'Fog': '🌫️'
    }
    return emoji_map.get(weather_main, '🌤️')

def get_daily_recommendation(day_data: Dict[str, Any], day_name: str) -> str:
    """Генерирует рекомендацию для конкретного дня"""
    temp = day_data.get('temp', {}).get('day', 0)
    weather = day_data.get('weather', [{}])[0].get('description', 'Неизвестно')
    humidity = day_data.get('humidity', 0)
    wind_speed = day_data.get('wind_speed', 0)
    
    recommendation = f"• 🌡 Температура: {temp:.1f}°C\n"
    recommendation += f"• ☁️ Погода: {weather}\n"
    recommendation += f"• 💧 Влажность: {humidity}%\n"
    recommendation += f"• 💨 Ветер: {wind_speed} м/с\n\n"
    
    # Простая рекомендация по мойке
    if 'rain' in weather.lower() or 'snow' in weather.lower():
        recommendation += f"❌ *{day_name.capitalize()} не подходит для мойки* - ожидаются осадки"
    elif temp < 0:
        recommendation += f"⚠️ *{day_name.capitalize()} не рекомендуется для мойки* - возможен лед"
    elif temp > 15:
        recommendation += f"✅ *{day_name.capitalize()} отлично подходит для мойки* - тепло и сухо"
    elif temp > 5:
        recommendation += f"⚠️ *{day_name.capitalize()} можно помыть* - но будет прохладно"
    else:
        recommendation += f"❌ *{day_name.capitalize()} не подходит для мойки* - слишком холодно"
    
    return recommendation

# -----------------------------------------------------------------------------
# Запуск бота
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 ClearyFi Telegram Bot запущен с новыми командами!")
    print("📋 Доступные команды: /start, /status, /now, /today, /tomorrow, /wash, /alerts, /city")
    bot.infinity_polling(timeout=60, skip_pending=True)
