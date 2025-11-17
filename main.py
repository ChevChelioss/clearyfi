#!/usr/bin/env python3
"""
ClearyFi - Финальная версия с правильным запуском компонентов
"""

import asyncio
import logging
import os
import sys
import threading
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clearyfi.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('ClearyFi')

class ClearyFiApplication:
    """
    Финальная версия приложения с правильным запуском компонентов
    """
    
    def __init__(self):
        self.is_running = False
        self.start_time = None
        self.daemon_thread = None
        
        logger.info("ClearyFiApplication инициализирован")

    def initialize_components(self):
        """Инициализирует все компоненты приложения"""
        try:
            logger.info("Инициализация компонентов...")
            
            # Проверяем конфигурацию
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            weather_key = os.getenv('WEATHER_API_KEY')
            
            if not bot_token or not weather_key:
                logger.error("❌ Не найдены обязательные переменные окружения")
                return False
            
            # Инициализируем базу данных
            from core.database import DatabaseManager
            db = DatabaseManager('clearyfi.db')
            
            # Инициализируем бота (будет использоваться в основном потоке)
            from bots.telegram_bot import create_bot
            self.telegram_bot = create_bot(bot_token, 'clearyfi.db', weather_key)
            
            logger.info("✅ Все компоненты инициализированы")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            return False

    def run_notification_daemon(self):
        """Запускает демон уведомлений в отдельном потоке"""
        try:
            import asyncio
            
            # Создаем новый event loop для этого потока
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            from services.notifications.notification_daemon import NotificationDaemon
            from telegram import Bot
            
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            weather_key = os.getenv('WEATHER_API_KEY')
            
            # Создаем отдельный экземпляр бота для демона
            bot_instance = Bot(token=bot_token)
            daemon = NotificationDaemon(bot_instance, 'clearyfi.db', weather_key)
            
            logger.info("🔔 Демон уведомлений запущен в фоновом режиме")
            
            # Запускаем демон в бесконечном цикле
            async def daemon_loop():
                while self.is_running:
                    try:
                        await daemon.process_scheduled_notifications()
                        await asyncio.sleep(60)  # Проверка каждую минуту
                    except Exception as e:
                        logger.error(f"Ошибка в демоне: {e}")
                        await asyncio.sleep(60)
            
            loop.run_until_complete(daemon_loop())
            
        except Exception as e:
            logger.error(f"❌ Ошибка демона уведомлений: {e}")

    def run_telegram_bot(self):
        """Запускает Telegram бота в основном потоке"""
        try:
            logger.info("🤖 Запуск Telegram бота в основном потоке...")
            self.telegram_bot.run()
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")

    def run(self):
        """Основной метод запуска приложения"""
        try:
            self.is_running = True
            self.start_time = datetime.now()
            
            logger.info("🚀 Запуск ClearyFi приложения...")
            
            # Инициализируем компоненты
            if not self.initialize_components():
                logger.error("❌ Не удалось инициализировать компоненты")
                return
            
            # Запускаем демон уведомлений в отдельном потоке
            self.daemon_thread = threading.Thread(
                target=self.run_notification_daemon,
                daemon=True  # Поток завершится при завершении main
            )
            self.daemon_thread.start()
            logger.info("✅ Демон уведомлений запущен в фоне")
            
            # Запускаем Telegram бота в основном потоке (блокирующий вызов)
            self.run_telegram_bot()
            
        except KeyboardInterrupt:
            logger.info("Приложение остановлено пользователем")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
        finally:
            self.shutdown()

    def shutdown(self):
        """Корректное завершение работы"""
        self.is_running = False
        logger.info("🛑 Остановка ClearyFi приложения...")
        
        # Демон поток завершится автоматически (daemon=True)
        logger.info("✅ Приложение корректно остановлено")


def main():
    """Основная функция"""
    app = ClearyFiApplication()
    app.run()


if __name__ == "__main__":
    main()
