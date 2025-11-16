#!/usr/bin/env python3
"""
ClearyFi - Умный помощник для ухода за автомобилем
Основной файл приложения, запускающий все компоненты системы
"""

import asyncio
import logging
import signal
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional

# ✅ ДОБАВЛЯЕМ ЗАГРУЗКУ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
from dotenv import load_dotenv
load_dotenv()  # Загружаем переменные из .env файла

# Добавляем пути для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bots.telegram_bot import ClearyFiTelegramBot, create_bot
from services.notifications.notification_daemon import NotificationDaemon, run_notification_daemon
from core.database import DatabaseManager

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
    Основной класс приложения ClearyFi.
    Управляет всеми компонентами системы и их жизненным циклом.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация приложения.
        
        Args:
            config: Словарь с конфигурацией приложения
        """
        self.config = config
        self.is_running = False
        self.start_time = None
        
        # Компоненты системы
        self.database = None
        self.telegram_bot = None
        self.notification_daemon = None
        
        # Задачи asyncio
        self.tasks = []
        
        # Обработчики сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("ClearyFiApplication инициализирован")

    async def initialize(self) -> bool:
        """
        Инициализирует все компоненты приложения.
        
        Returns:
            True если инициализация успешна, иначе False
        """
        try:
            logger.info("Запуск инициализации приложения...")
            
            # 1. Инициализация базы данных
            if not await self._initialize_database():
                logger.error("Не удалось инициализировать базу данных")
                return False
            
            # 2. Инициализация Telegram бота
            if not await self._initialize_telegram_bot():
                logger.error("Не удалось инициализировать Telegram бота")
                return False
            
            # 3. Инициализация демона уведомлений
            if not await self._initialize_notification_daemon():
                logger.error("Не удалось инициализировать демон уведомлений")
                return False
            
            logger.info("✅ Все компоненты приложения успешно инициализированы")
            return True
            
        except Exception as e:
            logger.error(f"Критическая ошибка инициализации: {e}")
            return False

    async def _initialize_database(self) -> bool:
        """
        Инициализирует базу данных.
        
        Returns:
            True если успешно, иначе False
        """
        try:
            db_path = self.config.get('database_path', 'clearyfi.db')
            self.database = DatabaseManager(db_path)
            
            if await self.database.initialize():
                logger.info(f"✅ База данных инициализирована: {db_path}")
                return True
            else:
                logger.error("❌ Ошибка инициализации базы данных")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            return False

    async def _initialize_telegram_bot(self) -> bool:
        """
        Инициализирует Telegram бота.
        
        Returns:
            True если успешно, иначе False
        """
        try:
            bot_token = self.config.get('telegram_bot_token')
            weather_api_key = self.config.get('weather_api_key')
            db_path = self.config.get('database_path', 'clearyfi.db')
            
            if not bot_token:
                logger.error("❌ Не указан токен Telegram бота")
                return False
            
            if not weather_api_key:
                logger.error("❌ Не указан API ключ погодного сервиса")
                return False
            
            self.telegram_bot = create_bot(bot_token, db_path, weather_api_key)
            logger.info("✅ Telegram бот инициализирован")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации Telegram бота: {e}")
            return False

    async def _initialize_notification_daemon(self) -> bool:
        """
        Инициализирует демон уведомлений.
        
        Returns:
            True если успешно, иначе False
        """
        try:
            if not self.telegram_bot:
                logger.error("❌ Telegram бот не инициализирован для демона")
                return False
            
            weather_api_key = self.config.get('weather_api_key')
            db_path = self.config.get('database_path', 'clearyfi.db')
            
            self.notification_daemon = NotificationDaemon(
                telegram_bot=self.telegram_bot.bot,
                db_path=db_path,
                weather_api_key=weather_api_key
            )
            
            # Связываем демон с ботом
            self.telegram_bot.set_notification_daemon(self.notification_daemon)
            
            logger.info("✅ Демон уведомлений инициализирован")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации демона уведомлений: {e}")
            return False

    async def run(self) -> None:
        """
        Запускает основное выполнение приложения.
        """
        try:
            self.is_running = True
            self.start_time = datetime.now()
            
            logger.info("🚀 Запуск ClearyFi приложения...")
            logger.info(f"📅 Время запуска: {self.start_time}")
            
            # Запускаем все компоненты асинхронно
            await self._run_components()
            
        except Exception as e:
            logger.error(f"Критическая ошибка во время выполнения: {e}")
        finally:
            await self.shutdown()

    async def _run_components(self) -> None:
        """
        Запускает все компоненты системы асинхронно.
        """
        try:
            # Создаем задачи для всех компонентов
            tasks = []
            
            # Задача для Telegram бота (если он поддерживает асинхронность)
            if self.telegram_bot:
                # В текущей реализации бот запускается синхронно через run_polling
                # В будущем можно переделать на асинхронную версию
                pass
            
            # Задача для демона уведомлений
            if self.notification_daemon:
                daemon_task = asyncio.create_task(
                    run_notification_daemon(
                        self.telegram_bot.bot if self.telegram_bot else None,
                        self.config.get('database_path', 'clearyfi.db'),
                        self.config.get('weather_api_key')
                    )
                )
                tasks.append(daemon_task)
                logger.info("✅ Демон уведомлений запущен")
            
            # Задача для мониторинга здоровья системы
            health_task = asyncio.create_task(self._health_monitor())
            tasks.append(health_task)
            logger.info("✅ Мониторинг здоровья запущен")
            
            # Сохраняем задачи
            self.tasks = tasks
            
            # Запускаем Telegram бота (блокирующий вызов)
            if self.telegram_bot:
                logger.info("✅ Запуск Telegram бота...")
                self.telegram_bot.run()
            
            # Ожидаем завершения всех задач (не должно произойти, так как бот блокирующий)
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
        except Exception as e:
            logger.error(f"Ошибка запуска компонентов: {e}")

    async def _health_monitor(self) -> None:
        """
        Мониторинг здоровья системы и периодическая логировка состояния.
        """
        try:
            while self.is_running:
                # Логируем состояние системы каждые 5 минут
                await asyncio.sleep(300)  # 5 минут
                
                if self.is_running:
                    uptime = datetime.now() - self.start_time
                    hours, remainder = divmod(uptime.total_seconds(), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    logger.info(
                        f"📊 Состояние системы: "
                        f"работает {int(hours)}ч {int(minutes)}м {int(seconds)}с, "
                        f"активных задач: {len([t for t in self.tasks if not t.done()])}"
                    )
                    
        except asyncio.CancelledError:
            logger.info("Мониторинг здоровья остановлен")
        except Exception as e:
            logger.error(f"Ошибка мониторинга здоровья: {e}")

    async def shutdown(self) -> None:
        """
        Корректно останавливает приложение и все компоненты.
        """
        try:
            self.is_running = False
            logger.info("🛑 Остановка ClearyFi приложения...")
            
            # Отменяем все задачи
            for task in self.tasks:
                if not task.done():
                    task.cancel()
            
            # Останавливаем компоненты
            if self.telegram_bot:
                await self.telegram_bot.stop()
                logger.info("✅ Telegram бот остановлен")
            
            if self.database:
                await self.database.close()
                logger.info("✅ База данных закрыта")
            
            # Ждем завершения всех задач
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)
            
            uptime = datetime.now() - self.start_time if self.start_time else None
            if uptime:
                hours, remainder = divmod(uptime.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                logger.info(f"📅 Время работы: {int(hours)}ч {int(minutes)}м {int(seconds)}с")
            
            logger.info("✅ ClearyFi приложение корректно остановлено")
            
        except Exception as e:
            logger.error(f"Ошибка при остановке приложения: {e}")
        finally:
            # Завершаем event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.stop()

    def _signal_handler(self, signum, frame) -> None:
        """
        Обработчик сигналов для graceful shutdown.
        """
        logger.info(f"Получен сигнал {signum}, инициируем остановку...")
        asyncio.create_task(self.shutdown())


def load_config() -> Dict[str, Any]:
    """
    Загружает конфигурацию приложения из переменных окружения и файлов.
    
    Returns:
        Словарь с конфигурацией
    """
    # ✅ Убедимся, что переменные загружены
    from dotenv import load_dotenv
    load_dotenv()
    
    config = {
        'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
        'weather_api_key': os.getenv('WEATHER_API_KEY'),
        'database_path': os.getenv('DATABASE_PATH', 'clearyfi.db'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO')
    }
    
    # Проверяем обязательные параметры
    missing_configs = []
    if not config['telegram_bot_token']:
        missing_configs.append('TELEGRAM_BOT_TOKEN')
    if not config['weather_api_key']:
        missing_configs.append('WEATHER_API_KEY')
    
    if missing_configs:
        logger.error(f"❌ Отсутствуют обязательные параметры конфигурации: {', '.join(missing_configs)}")
        logger.info("💡 Установите переменные окружения:")
        logger.info("   export TELEGRAM_BOT_TOKEN=your_telegram_bot_token")
        logger.info("   export WEATHER_API_KEY=your_weather_api_key")
        
        # ✅ Дополнительная диагностика
        logger.info("🔍 Проверка .env файла:")
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        logger.info(f"   Путь к .env: {env_path}")
        logger.info(f"   Файл .env существует: {os.path.exists(env_path)}")
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                content = f.read()
                logger.info(f"   Содержимое .env: {content}")
        
        sys.exit(1)
    
    return config


async def main():
    """
    Основная функция запуска приложения.
    """
    try:
        # Загружаем конфигурацию
        config = load_config()
        
        # Создаем и инициализируем приложение
        app = ClearyFiApplication(config)
        
        if await app.initialize():
            # Запускаем приложение
            await app.run()
        else:
            logger.error("❌ Не удалось инициализировать приложение")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Запускаем приложение
    asyncio.run(main())
