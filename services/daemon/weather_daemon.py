#!/usr/bin/env python3
import sys
import os
import time
import logging
import traceback

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
    from config.settings import TELEGRAM_BOT_TOKEN
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

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def send_recommendation(chat_id: int, city: str):
    """Отправка рекомендации пользователю с обработкой ошибок"""
    try:
        logging.info(f"📨 Отправляем уведомление для {city} (chat_id: {chat_id})")
        
        # Получаем прогноз
        from config.settings import OPENWEATHER_API_KEY
        weather_client = WeatherAPIClient(api_key=OPENWEATHER_API_KEY)
        forecast = weather_client.get_forecast(city)
        
        if not forecast:
            logging.warning(f"Не удалось получить прогноз для {city}")
            return False
            
        # Анализируем и получаем рекомендацию - используем новый метод
        analyzer = WeatherAnalyzer(forecast)
        recommendation = analyzer.get_detailed_recommendation()
        
        # Формируем сообщение
        message = (
            f"🌤 *Ежедневный прогноз для {city}:*\n\n"
            f"{recommendation}"
        )
        
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
