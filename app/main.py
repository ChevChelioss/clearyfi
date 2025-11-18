#!/usr/bin/env python3
"""
Главный файл приложения ClearyFi
"""

from core.logger import logger
from app.config import Config
from locales.manager import LocaleManager
from core.database import Database
from bots.telegram_bot import ClearyFiBot

# Импортируем сервисы
from services.weather.openweather import OpenWeatherService
from services.recommendations.wash import WashRecommendationService
from services.recommendations.tires import TireRecommendationService
from services.recommendations.roads import RoadConditionService
from services.recommendations.maintenance import MaintenanceService
from services.recommendations.extended_weather import ExtendedWeatherService
from services.subscription.subscription_service import SubscriptionService


class ClearyFiApp:
    """Главный класс приложения ClearyFi"""
    
    def __init__(self):
        """Инициализирует приложение"""
        logger.info("🚀 Инициализация ClearyFi приложения...")
        
        try:
            # Загружаем конфигурацию
            self.config = Config()
            logger.info("✅ Конфигурация загружена")
            
            # Загружаем локализацию
            self.locale = LocaleManager("ru")
            logger.info("✅ Локализация загружена")
            
            # Инициализируем базу данных
            self.database = Database(self.config.database.path)
            logger.info("✅ База данных инициализирована")
            
            # Инициализируем сервисы
            self._init_services()
            
            # Инициализируем бота
            self.bot = ClearyFiBot(
                token=self.config.bot.token,
                database=self.database,
                locale_manager=self.locale,
                services=self.services
            )
            logger.info("✅ Telegram бот инициализирован")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            raise
    
    def _init_services(self):
        """Инициализирует все сервисы приложения"""
        self.services = {}
        
        # Сервис погоды
        self.services['weather'] = OpenWeatherService(self.config.weather.api_key)
        logger.info("✅ Погодный сервис инициализирован")
        
        # Сервисы рекомендаций
        self.services['wash'] = WashRecommendationService(
            self.services['weather'],
            self.locale,
            self.config.ai.deepseek_api_key  # Передаем API ключ для AI
        )
        logger.info("✅ Сервис рекомендаций по мойке инициализирован")
        
        if self.config.ai.enabled:
            logger.info("🤖 AI-рекомендации активированы")
        
        # ... остальные сервисы ...
        
    def run(self):
        """Запускает приложение"""
        try:
            logger.info("🎯 Запуск ClearyFi...")
            
            # Запускаем бота (блокирующий вызов)
            self.bot.run()
            
        except KeyboardInterrupt:
            logger.info("🛑 Приложение остановлено пользователем")
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске: {e}")
            raise


def main():
    """Точка входа в приложение"""
    app = ClearyFiApp()
    app.run()


if __name__ == "__main__":
    main()
