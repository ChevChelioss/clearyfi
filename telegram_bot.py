import logging
import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
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
# Вспомогательные функции для клавиатур
# -----------------------------------------------------------------------------
def create_main_keyboard():
    """Создает основную клавиатуру быстрого доступа"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("🌤 Сейчас"),
        KeyboardButton("📅 Сегодня"),
        KeyboardButton("🚗 Мойка"),
        KeyboardButton("⚠️ Опасности"),
        KeyboardButton("🏙 Город"),
        KeyboardButton("📊 Статус")
    )
    return keyboard

def create_weather_actions_keyboard():
    """Создает инлайн-клавиатуру для действий с погодой"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🚗 Мойка", callback_data="quick_wash"),
        InlineKeyboardButton("📅 Завтра", callback_data="quick_tomorrow"),
        InlineKeyboardButton("⚠️ Опасности", callback_data="quick_alerts"),
        InlineKeyboardButton("🏙 Сменить город", callback_data="quick_city")
    )
    return keyboard

def create_city_keyboard():
    """Клавиатура для выбора города (исправленная)"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("📍 Москва"),
        KeyboardButton("📍 Санкт-Петербург"),
        KeyboardButton("📍 Тюмень"), 
        KeyboardButton("📍 Екатеринбург"),
        KeyboardButton("📍 Новосибирск"),
        KeyboardButton("📍 Казань")
    )
    keyboard.add(
        KeyboardButton("📍 Ввести другой город"),
        KeyboardButton("🔙 Назад к меню")
    )
    return keyboard

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
                "🚗 *Добро пожаловать в ClearyFi!*\n\n"
                "Я ваш умный помощник для ухода за автомобилем!\n\n"
                "Я помогу вам:\n"
                "• Найти лучший день для мойки автомобиля\n"  
                "• Получать точные прогнозы погоды\n"
                "• Узнать о погодных предупреждениях\n"
                "• Получать ежедневные рекомендации\n\n"
                "🏙️ *Для начала выберите ваш город:*",
                parse_mode='Markdown',
                reply_markup=create_city_keyboard()
            )
            db.add_or_update_user(user_id, chat_id, username)
            pending_city_input[chat_id] = True
            return

# -----------------------------------------------------------------------------
# /help - Справка по командам
# -----------------------------------------------------------------------------
@bot.message_handler(commands=['help'])
def cmd_help(message: Message):
    help_text = """
🤖 *ClearyFi - ваш авто-погодный помощник*

*🚀 Быстрый доступ через кнопки:*
🌤 Сейчас - Текущая погода
📅 Сегодня - Прогноз на сегодня
🚗 Мойка - Рекомендация по мойке
⚠️ Опасности - Погодные предупреждения
🏙 Город - Сменить город
📊 Статус - Ваши настройки

*📋 Текстовые команды:*
/start - Начать работу
/help - Эта справка
/now - Погода сейчас
/today - Сегодня
/tomorrow - Завтра
/wash - Мойка
/alerts - Опасности
/city - Сменить город
/status - Статус

*💡 Совет:* Используйте кнопки - это удобнее!
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

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
                "Нажмите /start чтобы начать работу.",
                parse_mode='Markdown'
            )
            return
            
        status_text = (
            "📊 *Ваш статус в ClearyFi:*\n\n"
            f"🏙️ *Город:* {user['city']}\n"
            f"🔔 *Уведомления:* {'✅ ВКЛ' if user.get('is_active', True) else '❌ ВЫКЛ'}\n"
            f"⏰ *Время уведомлений:* {user.get('notification_time', '09:00')}\n\n"
        )
        
        # Добавляем подсказки в зависимости от статуса
        if user.get('is_active', True):
            status_text += "_Чтобы отключить уведомления, используйте /unsubscribe_"
        else:
            status_text += "_Чтобы включить уведомления, используйте /subscribe_"
        
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
            bot.send_message(chat_id, 
                "❌ *Сначала укажите город*\n\n"
                "Нажмите /start для настройки",
                parse_mode='Markdown'
            )
            return
            
    try:
        weather_client = WeatherAPIClient(api_key=settings.OPENWEATHER_API_KEY)
        forecast = weather_client.get_forecast(user["city"])
        
        if forecast:
            analyzer = WeatherAnalyzer(forecast)
            current = analyzer.get_current_weather()
            
            if current:  # ← ЭТА СТРОКА ДОЛЖНА БЫТЬ С ОТСТУПОМ 12 ПРОБЕЛОВ
                weather_emoji = get_weather_emoji(current['weather_main'])
                
                message_text = (
                    f"{weather_emoji} *Погода сейчас в {user['city']}:*\n\n"
                    f"🌡 *Температура:* {current['temperature']:.1f}°C\n"
                    f"🎯 *Ощущается как:* {current['feels_like']:.1f}°C\n"
                    f"💧 *Влажность:* {current['humidity']}%\n"
                    f"📊 *Давление:* {current['pressure']:.0f} мм рт. ст.\n"
                    f"💨 *Ветер:* {current['wind_speed']} м/с\n"
                    f"☁️ *Состояние:* {current['weather'].capitalize()}\n\n"
                    f"_Обновлено: сейчас_"
                )
                
                bot.send_message(
                    chat_id, 
                    message_text, 
                    parse_mode='Markdown',
                    reply_markup=create_weather_actions_keyboard()
                )
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
                
                bot.send_message(
                    chat_id, 
                    message_text, 
                    parse_mode='Markdown',
                    reply_markup=create_weather_actions_keyboard()
                )
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
                
                bot.send_message(
                    chat_id, 
                    message_text, 
                    parse_mode='Markdown',
                    reply_markup=create_weather_actions_keyboard()
                )
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
            
            bot.send_message(
                chat_id, 
                message_text, 
                parse_mode='Markdown',
                reply_markup=create_weather_actions_keyboard()
            )
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
                
            bot.send_message(
                chat_id, 
                message_text, 
                parse_mode='Markdown',
                reply_markup=create_weather_actions_keyboard()
            )
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
        "🏙️ *Выберите город из списка или введите свой:*\n\n"
        "_Вы можете выбрать из популярных или ввести любой другой город_",
        parse_mode='Markdown',
        reply_markup=create_city_keyboard()
    )

# -----------------------------------------------------------------------------
# /unsubscribe - Отписаться от уведомлений
# -----------------------------------------------------------------------------
@bot.message_handler(commands=['unsubscribe'])
def cmd_unsubscribe(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    with SubscriberDBConnection() as db:
        db.update_user_active(user_id, False)
        bot.send_message(chat_id, 
            "✅ *Вы отписались от ежедневных уведомлений.*\n\n"
            "Вы больше не будете получать автоматические прогнозы.\n"
            "Чтобы снова подписаться, используйте /subscribe",
            parse_mode='Markdown',
            reply_markup=create_main_keyboard()
        )

# -----------------------------------------------------------------------------
# /subscribe - Подписаться на уведомления  
# -----------------------------------------------------------------------------
@bot.message_handler(commands=['subscribe'])
def cmd_subscribe(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    with SubscriberDBConnection() as db:
        user = db.get_user_by_chat_id(chat_id)
        if not user or not user.get("city"):
            bot.send_message(chat_id, 
                "❌ *Сначала укажите город*\n\n"
                "Используйте /city чтобы установить город",
                parse_mode='Markdown'
            )
            return
        
        db.update_user_active(user_id, True)
        bot.send_message(chat_id, 
            "✅ *Вы подписались на ежедневные уведомления!*\n\n"
            "Теперь вы будете получать прогнозы и рекомендации каждый день в 09:00.",
            parse_mode='Markdown',
            reply_markup=create_main_keyboard()
        )

# -----------------------------------------------------------------------------
# Обработка текстовых команд из кнопок
# -----------------------------------------------------------------------------
@bot.message_handler(func=lambda message: True)
def handle_text_commands(message: Message):
    chat_id = message.chat.id
    text = message.text.strip()
    
    # Если ожидается ввод города
    if chat_id in pending_city_input:
        handle_city_input(message)
        return
    
    # Обработка быстрых команд из кнопок
    command_handlers = {
        "🌤 сейчас": cmd_now,
        "📅 сегодня": cmd_today,
        "🚗 мойка": cmd_wash,
        "⚠️ опасности": cmd_alerts,
        "🏙 город": cmd_city,
        "📊 статус": cmd_status,
        "🔙 назад": lambda msg: bot.send_message(msg.chat.id, "Главное меню:", reply_markup=create_main_keyboard())
    }
    
    # Обработка популярных городов (исправлено)
    if text.startswith("📍 "):
        city_name = text[2:].strip()  # Убираем эмодзи и пробел, обрезаем лишние пробелы
        if city_name == "Другой город":
            bot.send_message(chat_id, "🏙️ Введите название вашего города:")
            pending_city_input[chat_id] = True
            return
        elif city_name != "Назад":
            # Убираем "📍 " из названия города для проверки
            clean_city_name = city_name.replace("📍 ", "").strip()
            handle_city_selection(message, clean_city_name)
            return
    
    # Вызов обработчика команды
    for command_text, handler in command_handlers.items():
        if text.lower() == command_text.lower():
            handler(message)
            return
    
    # Если команда не распознана
    bot.send_message(chat_id, 
        "❌ Команда не распознана\n\n"
        "Используйте кнопки ниже или /help для списка команд",
        reply_markup=create_main_keyboard()
    )

# -----------------------------------------------------------------------------
# Обработка callback-запросов от инлайн-кнопок
# -----------------------------------------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    # Создаем fake message object для вызова команд
    fake_message = type('', (), {'chat': type('', (), {'id': chat_id})(), 'from_user': call.from_user})()
    
    callback_handlers = {
        "quick_wash": cmd_wash,
        "quick_tomorrow": cmd_tomorrow,
        "quick_alerts": cmd_alerts,
        "quick_city": cmd_city
    }
    
    if call.data in callback_handlers:
        callback_handlers[call.data](fake_message)
    
    # Подтверждаем обработку callback
    bot.answer_callback_query(call.id)

# -----------------------------------------------------------------------------
# Обработка ввода города
# -----------------------------------------------------------------------------
def handle_city_input(message: Message):
    chat_id = message.chat.id
    text = message.text.strip()
    user_id = message.from_user.id

    if not text:
        bot.send_message(chat_id, "❌ Пожалуйста, введите корректное название города:")
        return

    handle_city_selection(message, text)

def handle_city_selection(message: Message, city_name: str):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Очищаем название города от лишних символов
    clean_city_name = city_name.replace("📍", "").strip()
    
    if not clean_city_name:
        bot.send_message(chat_id, "❌ Пожалуйста, введите корректное название города:")
        return

    # Проверяем город через API
    weather_client = WeatherAPIClient(api_key=settings.OPENWEATHER_API_KEY)
    if not weather_client.is_city_valid(clean_city_name):
        bot.send_message(chat_id, 
            f"❌ *Город '{clean_city_name}' не найден*\n\n"
            "Пожалуйста, проверьте написание и введите город еще раз:\n"
            "_Убедитесь, что город находится в России_",
            parse_mode='Markdown',
            reply_markup=create_city_keyboard()
        )
        return

    # Сохраняем город в базу
    with SubscriberDBConnection() as db:
        db.update_user_city(user_id, clean_city_name)

    if chat_id in pending_city_input:
        del pending_city_input[chat_id]
    
    bot.send_message(
        chat_id,
        f"✅ *Отлично! Город '{clean_city_name}' сохранен!*\n\n"
        "📧 Вы будете получать ежедневные уведомления с прогнозом погоды "
        "и рекомендациями по мойке автомобиля.\n\n"
        "*🚀 Используйте кнопки ниже для быстрого доступа:*",
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
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
    temp = day_data.get('temp', {}).get('day', 0) if isinstance(day_data.get('temp'), dict) else day_data.get('temp', 0)
    weather = day_data.get('weather', [{}])[0].get('description', 'Неизвестно') if day_data.get('weather') else 'Неизвестно'
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
    print("🚀 ClearyFi Telegram Bot запущен с улучшенным UX!")
    print("📋 Доступны текстовые команды и интерактивные кнопки")
    bot.infinity_polling(timeout=60, skip_pending=True)
