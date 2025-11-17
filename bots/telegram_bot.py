#!/usr/bin/env python3
"""
Главный класс Telegram бота ClearyFi
"""

from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters

from core.logger import logger
from .handlers.start import StartHandler
from .handlers.help import HelpHandler
from .handlers.wash import WashHandler
from .handlers.tires import TiresHandler
from .handlers.roads import RoadsHandler
from .handlers.subscription import SubscriptionHandler
from .handlers.settings import SettingsHandler, CITY_SELECTION


class ClearyFiBot:
    """Главный класс Telegram бота ClearyFi"""
    
    def __init__(self, token: str, database, locale_manager, services):
        self.token = token
        self.database = database
        self.locale = locale_manager
        self.services = services
        
        # Создаем приложение Telegram
        self.application = Application.builder().token(token).build()
        
        # Инициализируем обработчики
        self._init_handlers()
        
        logger.info("✅ Telegram бот инициализирован")
    
    def _init_handlers(self):
        """Инициализирует и регистрирует все обработчики"""
        # Создаем экземпляры обработчиков
        start_handler = StartHandler(self.locale, self.database)
        help_handler = HelpHandler(self.locale, self.database)
        
        # Обработчики с сервисами рекомендаций
        wash_handler = WashHandler(
            self.locale, 
            self.database, 
            self.services['wash']  # Передаем сервис мойки
        )
        
        # Пока оставляем остальные обработчики без сервисов
        tires_handler = TiresHandler(self.locale, self.database)
        roads_handler = RoadsHandler(self.locale, self.database)
        subscription_handler = SubscriptionHandler(self.locale, self.database)
        settings_handler = SettingsHandler(self.locale, self.database)
        
        # ConversationHandler для настроек города
        conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex(f"^{self.locale.get_button('settings')}$"), 
                             settings_handler.handle_city_selection),
                CommandHandler("settings", settings_handler.handle_city_selection)
            ],
            states={
                CITY_SELECTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, 
                                 settings_handler.handle_city_input)
                ],
            },
            fallbacks=[
                CommandHandler("cancel", settings_handler.cancel)
            ],
            name="city_setup_conversation"
        )
        
        # Регистрируем обработчики команд
        self.application.add_handler(CommandHandler("start", start_handler.handle))
        self.application.add_handler(CommandHandler("help", help_handler.handle))
        
        # Регистрируем обработчики кнопок
        self.application.add_handler(MessageHandler(
            filters.Regex(f"^{self.locale.get_button('wash')}$"), 
            wash_handler.handle
        ))
        self.application.add_handler(MessageHandler(
            filters.Regex(f"^{self.locale.get_button('tires')}$"), 
            tires_handler.handle
        ))
        self.application.add_handler(MessageHandler(
            filters.Regex(f"^{self.locale.get_button('roads')}$"), 
            roads_handler.handle
        ))
        self.application.add_handler(MessageHandler(
            filters.Regex(f"^{self.locale.get_button('subscription')}$"), 
            subscription_handler.handle
        ))
        self.application.add_handler(MessageHandler(
            filters.Regex(f"^{self.locale.get_button('help')}$"), 
            help_handler.handle
        ))
        
        # Регистрируем ConversationHandler (должен быть после других обработчиков)
        self.application.add_handler(conv_handler)
        
        logger.info("✅ Обработчики бота зарегистрированы")
    
    def run(self):
        """Запускает бота"""
        logger.info("🤖 Запуск Telegram бота...")
        self.application.run_polling()
