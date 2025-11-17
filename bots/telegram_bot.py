#!/usr/bin/env python3
"""
Умный автомобильный помощник ClearyFi
"""

logger = logging.getLogger(__name__)

import logging
import sqlite3
import asyncio
from core.database import Database
from datetime import datetime
from typing import Dict, List, Optional, Any

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ContextTypes, ConversationHandler, filters
)

from services.weather.weather_service import WeatherService
from services.notifications.recommendation_builder import RecommendationBuilder
from services.location.city_normalizer import CityNormalizer
from utils.date_utils import format_date_short

# Настройка логирования
logger = logging.getLogger('TelegramBot')

# Состояния для ConversationHandler
CITY_SELECTION, NOTIFICATION_TIME = range(2)

# Основная клавиатура
main_keyboard = ReplyKeyboardMarkup([
    ['🚗 Рекомендация мойки', '🛞 Шины и шиномонтаж'],
    ['🛣 Дорожные условия', '⏰ Управление подпиской'],
    ['❓ Помощь', '⚙️ Настройки']
], resize_keyboard=True)

# Клавиатура подписки
subscription_keyboard = ReplyKeyboardMarkup([
    ['✅ Подписаться на уведомления', '❌ Отписаться от уведомлений'],
    ['🔙 Назад']
], resize_keyboard=True)

back_keyboard = ReplyKeyboardMarkup([
    ['🔙 Назад']
], resize_keyboard=True)


class ClearyFiTelegramBot:
    """
    Умный автомобильный помощник ClearyFi.
    """
    
    def __init__(self, token: str, db_path: str, weather_api_key: str):
        self.token = token
        self.db_path = db_path
        self.weather_service = WeatherService(weather_api_key)
        self.notification_daemon = None
        
        # Создаем приложение Telegram
        self.application = Application.builder().token(token).build()
        
        # Регистрируем обработчики
        self._setup_handlers()
        
        logger.info("ClearyFiTelegramBot инициализирован")

    def _setup_handlers(self) -> None:
        """Настраивает обработчики команд"""

        # Conversation Handler для настройки города - ДОЛЖЕН БЫТЬ ПЕРВЫМ!
        conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex('^⚙️ Настройки$'), self._setup_city_start),
                CommandHandler("settings", self._setup_city_start)
            ],
            states={
                CITY_SELECTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._setup_city_process)
                ],
            },
            fallbacks=[
                MessageHandler(filters.Regex('^🔙 Назад$'), self._cancel_setup),
                CommandHandler("cancel", self._cancel_setup)
            ],
            name="city_setup",
            persistent=False,
            allow_reentry=True
        )

        self.application.add_handler(conv_handler)

        # Основные команды
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("subscribe", self._subscribe_command))
        self.application.add_handler(CommandHandler("unsubscribe", self._unsubscribe_command))
        # Убираем дублирующий settings, т.к. он уже в ConversationHandler

        # Обработчики кнопок главного меню
        self.application.add_handler(MessageHandler(
            filters.Regex('^🚗 Рекомендация мойки$'),
            self._wash_recommendation_handler
        ))
        self.application.add_handler(MessageHandler(
            filters.Regex('^🛞 Шины и шиномонтаж$'),
            self._tire_recommendation_handler
        ))
        self.application.add_handler(MessageHandler(
            filters.Regex('^🛣 Дорожные условия$'),
            self._road_conditions_handler
        ))
        self.application.add_handler(MessageHandler(
            filters.Regex('^⏰ Управление подпиской$'),
            self._subscription_management_handler
        ))
        self.application.add_handler(MessageHandler(
            filters.Regex('^❓ Помощь$'),
            self._help_command
        ))
        # Убираем обработчик "⚙️ Настройки" из главного меню, т.к. он уже в ConversationHandler

        # Обработчики подписки
        self.application.add_handler(MessageHandler(
            filters.Regex('^✅ Подписаться на уведомления$'),
            self._subscribe_handler
        ))
        self.application.add_handler(MessageHandler(
            filters.Regex('^❌ Отписаться от уведомлений$'),
            self._unsubscribe_handler
        ))

        # Обработчик назад
        self.application.add_handler(MessageHandler(
            filters.Regex('^🔙 Назад$'),
            self._back_handler
        ))

        logger.debug("Обработчики настроены")

        # === ОБРАБОТЧИКИ ДЛЯ КНОПОК ГЛАВНОГО МЕНЮ ===

        # Обработчик для "🚗 Рекомендация мойки"
        application.add_handler(MessageHandler(
            filters.Regex("^🚗 Рекомендация мойки$"), 
            handle_wash_recommendation
        ))

        # Обработчик для "🛞 Шины и шиномонтаж"  
        application.add_handler(MessageHandler(
            filters.Regex("^🛞 Шины и шиномонтаж$"),
            handle_tire_recommendation
        ))

        # Обработчик для "🛣 Дорожные условия"
        application.add_handler(MessageHandler(
            filters.Regex("^🛣 Дорожные условия$"),
            handle_road_conditions
        ))

        # Обработчик для "⏰ Управление подпиской"
        application.add_handler(MessageHandler(
            filters.Regex("^⏰ Управление подпиской$"), 
            handle_subscription_management
        ))

        # Обработчик для "❓ Помощь"
        application.add_handler(MessageHandler(
            filters.Regex("^❓ Помощь$"),
            help_command
        ))

        # Обработчик для "⚙️ Настройки" - теперь через ConversationHandler
        application.add_handler(MessageHandler(
            filters.Regex("^⚙️ Настройки$"),
            settings_command
        ))

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        user = update.effective_user
        user_id = user.id
        
        logger.info(f"Новый пользователь: {user.first_name} (ID: {user_id})")
        
        # Регистрируем пользователя
        await self._register_user(user_id, user.first_name)
        
        welcome_message = (
            f"👋 Привет, {user.first_name}!\n\n"
            f"🚗 *ClearyFi* - ваш умный автомобильный помощник\n\n"
            f"✨ *Я анализирую погоду и даю рекомендации по:*\n"
            f"• 🧼 *Мойке автомобиля* - когда лучше помыть\n"
            f"• 🛞 *Шинам и шиномонтажу* - время для смены резины\n"
            f"• 🛣 *Дорожным условиям* - предупреждения о гололеде, дожде\n"
            f"• ⏰ *Авто-процедурам* - напоминания о подходящих днях\n\n"
            f"📝 *Как начать:*\n"
            f"1. Установите город через '⚙️ Настройки'\n"
            f"2. Подпишитесь на уведомления\n"
            f"3. Получайте умные рекомендации!\n\n"
            f"Используйте кнопки ниже для навигации:"
        )
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=main_keyboard,
            parse_mode='Markdown'
        )

    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /help"""
        help_message = (
            "📖 *ClearyFi - Умный автомобильный помощник*\n\n"
            
            "🚗 *Основные функции:*\n"
            "• *Рекомендация мойки* - лучшее время для мойки авто\n"
            "• *Шины и шиномонтаж* - когда менять резину\n"
            "• *Дорожные условия* - предупреждения и советы\n"
            "• *Управление подпиской* - настройка уведомлений\n\n"
            
            "⚙️ *Команды:*\n"
            "`/start` - начать работу с ботом\n"
            "`/subscribe` - подписаться на уведомления\n"
            "`/unsubscribe` - отписаться от уведомлений\n"
            "`/settings` - настройки города\n"
            "`/help` - эта справка\n\n"
            
            "💡 *Советы:*\n"
            "• Установите город для точных рекомендаций\n"
            "• Подпишитесь на уведомления в удобное время\n"
            "• Проверяйте рекомендации перед поездкой\n\n"
            
            "🚗 *Безопасных вам дорог!*"
        )
        
        await update.message.reply_text(
            help_message,
            reply_markup=main_keyboard,
            parse_mode='Markdown'
        )

    async def _subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /subscribe"""
        await self._subscription_management_handler(update, context)

    async def _unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /unsubscribe"""
        await self._subscription_management_handler(update, context)

    async def _settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /settings"""
        await self._show_city_selection(update, context)

    async def _wash_recommendation_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик рекомендаций по мойке"""
        user_id = update.effective_user.id
        city = await self._get_user_city(user_id)
        
        if not city:
            await update.message.reply_text(
                "📍 Сначала установите город через '⚙️ Настройки'",
                reply_markup=main_keyboard
            )
            return
        
        await update.message.reply_chat_action(action='typing')
        
        try:
            weather_data = self.weather_service.get_city_forecast(city, days=3)
            if weather_data:
                message = RecommendationBuilder.build_car_wash_recommendation(city, weather_data)
                await update.message.reply_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text(
                    f"❌ Не удалось получить данные для {city}",
                    reply_markup=main_keyboard
                )
        except Exception as e:
            logger.error(f"Ошибка рекомендации мойки: {e}")
            await update.message.reply_text(
                "❌ Ошибка при получении рекомендаций",
                reply_markup=main_keyboard
            )

    async def _tire_recommendation_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик рекомендаций по шинам"""
        user_id = update.effective_user.id
        city = await self._get_user_city(user_id)
        
        if not city:
            await update.message.reply_text(
                "📍 Сначала установите город через '⚙️ Настройки'",
                reply_markup=main_keyboard
            )
            return
        
        await update.message.reply_chat_action(action='typing')
        
        try:
            weather_data = self.weather_service.get_city_forecast(city, days=3)
            if weather_data:
                message = RecommendationBuilder.build_tire_recommendation(city, weather_data)
                await update.message.reply_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text(
                    f"❌ Не удалось получить данные для {city}",
                    reply_markup=main_keyboard
                )
        except Exception as e:
            logger.error(f"Ошибка рекомендации шин: {e}")
            await update.message.reply_text(
                "❌ Ошибка при получении рекомендаций",
                reply_markup=main_keyboard
            )

    async def _road_conditions_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик дорожных условий"""
        user_id = update.effective_user.id
        city = await self._get_user_city(user_id)
        
        if not city:
            await update.message.reply_text(
                "📍 Сначала установите город через '⚙️ Настройки'",
                reply_markup=main_keyboard
            )
            return
        
        await update.message.reply_chat_action(action='typing')
        
        try:
            weather_data = self.weather_service.get_city_forecast(city, days=3)
            if weather_data:
                message = RecommendationBuilder.build_road_conditions_alert(city, weather_data)
                await update.message.reply_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text(
                    f"❌ Не удалось получить данные для {city}",
                    reply_markup=main_keyboard
                )
        except Exception as e:
            logger.error(f"Ошибка дорожных условий: {e}")
            await update.message.reply_text(
                "❌ Ошибка при получении рекомендаций",
                reply_markup=main_keyboard
            )

    async def _subscription_management_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает меню управления подпиской"""
        user_id = update.effective_user.id
        user_settings = await self._get_user_settings(user_id)
        
        status = "✅ Подписан" if user_settings['notifications_enabled'] else "❌ Не подписан"
        city_status = user_settings['city'] or "Не установлен"
        
        message = (
            "⏰ *Управление подпиской*\n\n"
            f"• *Статус:* {status}\n"
            f"• *Город:* {city_status}\n"
            f"• *Время уведомлений:* {user_settings['notification_time']}\n\n"
            "Выберите действие:"
        )
        
        await update.message.reply_text(
            message,
            reply_markup=subscription_keyboard,
            parse_mode='Markdown'
        )

    async def _subscribe_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик подписки на уведомления"""
        user_id = update.effective_user.id
        user_settings = await self._get_user_settings(user_id)
        
        if not user_settings['city']:
            await update.message.reply_text(
                "📍 Сначала установите город через '⚙️ Настройки'",
                reply_markup=main_keyboard
            )
            return
        
        success = await self._update_user_settings(
            user_id=user_id,
            city=user_settings['city'],
            notification_time=user_settings['notification_time'],
            notifications_enabled=True
        )
        
        if success:
            await update.message.reply_text(
                "✅ Вы успешно подписались на уведомления!\n\n"
                f"📅 Каждый день в {user_settings['notification_time']} "
                f"вы будете получать умные рекомендации для {user_settings['city']}",
                reply_markup=main_keyboard
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка при подписке. Попробуйте позже.",
                reply_markup=main_keyboard
            )

    async def _unsubscribe_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик отписки от уведомлений"""
        user_id = update.effective_user.id
        user_settings = await self._get_user_settings(user_id)
        
        success = await self._update_user_settings(
            user_id=user_id,
            city=user_settings['city'],
            notification_time=user_settings['notification_time'],
            notifications_enabled=False
        )
        
        if success:
            await update.message.reply_text(
                "❌ Вы отписались от уведомлений.\n\n"
                "Чтобы снова получать рекомендации, используйте '✅ Подписаться на уведомления'",
                reply_markup=main_keyboard
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка при отписке. Попробуйте позже.",
                reply_markup=main_keyboard
            )

    async def _setup_city_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начинает процесс настройки города"""
        await self._show_city_selection(update, context)
        return CITY_SELECTION

    async def _show_city_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает выбор города"""
        from services.location.city_normalizer import CityNormalizer
        
        keyboard = CityNormalizer.get_popular_cities_keyboard()
        
        await update.message.reply_text(
            "📍 *Выберите ваш город:*\n\n"
            "Используйте кнопки ниже для выбора популярных городов "
            "или введите название своего города:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

    async def _setup_city_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обрабатывает выбор города"""
        city_input = update.message.text
        user_id = update.effective_user.id
        
        logger.info(f"Пользователь {user_id} выбрал город: {city_input}")
        
        # Обработка кнопки "Ввести другой город"
        if city_input == '🎯 Ввести другой город':
            await update.message.reply_text(
                "🏙️ *Введите название вашего города:*\n\n"
                "Пример: `Краснодар` или `Владивосток`",
                reply_markup=back_keyboard,
                parse_mode='Markdown'
            )
            return CITY_SELECTION
        
        # Обработка кнопки "Назад"
        if city_input == '🔙 Назад':
            await update.message.reply_text(
                "Возвращаемся в главное меню...",
                reply_markup=main_keyboard
            )
            return ConversationHandler.END
        
        # Проверяем валидность города
        from services.location.city_normalizer import CityNormalizer
        normalized_city = CityNormalizer.normalize_city_name(city_input)
        
        logger.info(f"Проверяем город: {city_input} -> {normalized_city}")
        
        is_valid = await self.weather_service.validate_city(normalized_city)
        
        if is_valid:
            # Сохраняем настройки
            success = await self._update_user_settings(
                user_id=user_id,
                city=city_input,  # Сохраняем оригинальное название для отображения
                notification_time='09:00',
                notifications_enabled=False  # По умолчанию выключаем уведомления
            )
            
            if success:
                await update.message.reply_text(
                    f"✅ Город установлен: *{city_input}*\n\n"
                    "Теперь вы можете получать умные рекомендации для вашего города!",
                    reply_markup=main_keyboard,
                    parse_mode='Markdown'
                )
                logger.info(f"Город {city_input} успешно установлен для пользователя {user_id}")
            else:
                await update.message.reply_text(
                    "❌ Ошибка сохранения настроек. Попробуйте позже.",
                    reply_markup=main_keyboard
                )
                logger.error(f"Ошибка сохранения города {city_input} для пользователя {user_id}")
            
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                f"❌ Город `{city_input}` не найден.\n\n"
                "Проверьте написание и попробуйте еще раз:",
                reply_markup=CityNormalizer.get_popular_cities_keyboard(),
                parse_mode='Markdown'
            )
            logger.warning(f"Город {city_input} не найден для пользователя {user_id}")
            
            return CITY_SELECTION
        
        # Обработка кнопки "Назад"
        if city_input == '🔙 Назад':
            await update.message.reply_text(
                "Возвращаемся в главное меню...",
                reply_markup=main_keyboard
            )
            return ConversationHandler.END
        
        # Проверяем валидность города
        normalized_city = CityNormalizer.normalize_city_name(city_input)
        is_valid = self.weather_service.validate_city(normalized_city)
        
        if is_valid:
            # Сохраняем настройки
            success = await self._update_user_settings(
                user_id=user_id,
                city=city_input,  # Сохраняем оригинальное название для отображения
                notification_time='09:00',
                notifications_enabled=False  # По умолчанию выключаем уведомления
            )
            
            if success:
                await update.message.reply_text(
                    f"✅ Город установлен: *{city_input}*\n\n"
                    "Теперь вы можете получать умные рекомендации для вашего города!",
                    reply_markup=main_keyboard,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ Ошибка сохранения настроек. Попробуйте позже.",
                    reply_markup=main_keyboard
                )
            
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                f"❌ Город `{city_input}` не найден.\n\n"
                "Проверьте написание и попробуйте еще раз:",
                reply_markup=CityNormalizer.get_popular_cities_keyboard(),
                parse_mode='Markdown'
            )
            
            return CITY_SELECTION

    async def _back_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик кнопки Назад"""
        await update.message.reply_text(
            "Возвращаемся в главное меню...",
            reply_markup=main_keyboard
        )

    async def _cancel_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отменяет настройку"""
        await update.message.reply_text(
            "Настройка отменена.",
            reply_markup=main_keyboard
        )
        return ConversationHandler.END

    async def handle_wash_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик для кнопки '🚗 Рекомендация мойки'"""
        try:
            user_id = update.effective_user.id
            
            # Получаем город из базы данных
            db = Database()
            user_city = db.get_user_city(user_id)
            db.close()
            
            # Проверяем установлен ли город
            if not user_city:
                await update.message.reply_text(
                    "❌ Сначала установите город в настройках",
                    reply_markup=main_menu_keyboard()
                )
                return
            
            # Получаем рекомендацию по мойке
            from services.notifications.recommendation_builder import RecommendationBuilder
            recommendation = RecommendationBuilder.build_wash_recommendation(user_city)
            
            # Отправляем рекомендацию
            if recommendation:
                await update.message.reply_text(
                    recommendation,
                    reply_markup=main_menu_keyboard(),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ Не удалось получить рекомендацию по мойке",
                    reply_markup=main_menu_keyboard()
                )
                
        except Exception as e:
            logger.error(f"Ошибка в handle_wash_recommendation: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при получении рекомендации",
                reply_markup=main_menu_keyboard()
            )


    async def handle_tire_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик для кнопки '🛞 Шины и шиномонтаж'"""
        try:
            user_id = update.effective_user.id
            
            # Получаем город из базы данных
            db = Database()
            user_city = db.get_user_city(user_id)
            db.close()
            
            # Проверяем установлен ли город
            if not user_city:
                await update.message.reply_text(
                    "❌ Сначала установите город в настройках",
                    reply_markup=main_menu_keyboard()
                )
                return
            
            # Получаем рекомендацию по шинам
            from services.notifications.recommendation_builder import RecommendationBuilder
            recommendation = RecommendationBuilder.build_tire_recommendation(user_city)
            
            # Отправляем рекомендацию
            if recommendation:
                await update.message.reply_text(
                    recommendation,
                    reply_markup=main_menu_keyboard(),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ Не удалось получить рекомендацию по шинам",
                    reply_markup=main_menu_keyboard()
                )
                
        except Exception as e:
            logger.error(f"Ошибка в handle_tire_recommendation: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при получении рекомендации по шинам",
                reply_markup=main_menu_keyboard()
            )


    async def handle_road_conditions(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик для кнопки '🛣 Дорожные условия'"""
        try:
            user_id = update.effective_user.id
            
            # Получаем город из базы данных
            db = Database()
            user_city = db.get_user_city(user_id)
            db.close()
            
            # Проверяем установлен ли город
            if not user_city:
                await update.message.reply_text(
                    "❌ Сначала установите город в настройках",
                    reply_markup=main_menu_keyboard()
                )
                return
            
            # Получаем дорожные условия
            from services.notifications.recommendation_builder import RecommendationBuilder
            conditions = RecommendationBuilder.build_road_conditions(user_city)
            
            # Отправляем дорожные условия
            if conditions:
                await update.message.reply_text(
                    conditions,
                    reply_markup=main_menu_keyboard(),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ Не удалось получить дорожные условия",
                    reply_markup=main_menu_keyboard()
                )
                
        except Exception as e:
            logger.error(f"Ошибка в handle_road_conditions: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при получении дорожных условий",
                reply_markup=main_menu_keyboard()
            )


    async def handle_subscription_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик для кнопки '⏰ Управление подпиской'"""
        try:
            user_id = update.effective_user.id
            
            # Получаем информацию о подписке
            db = Database()
            is_subscribed = db.is_user_subscribed(user_id)
            db.close()
            
            # Формируем сообщение
            if is_subscribed:
                message = (
                    "✅ Вы подписаны на ежедневные уведомления\n\n"
                    "Используйте команды:\n"
                    "/unsubscribe - отписаться от уведомлений\n"
                    "/settings - изменить настройки"
                )
            else:
                message = (
                    "❌ Вы не подписаны на уведомления\n\n"
                    "Используйте команды:\n"  
                    "/subscribe - подписаться на уведомления\n"
                    "/settings - изменить настройки"
                )
            
            await update.message.reply_text(
                message,
                reply_markup=main_menu_keyboard()
            )
                
        except Exception as e:
            logger.error(f"Ошибка в handle_subscription_management: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка",
                reply_markup=main_menu_keyboard()
            )

    # Методы работы с базой данных
    async def _register_user(self, user_id: int, username: str) -> bool:
        """Регистрирует пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
            if cursor.fetchone():
                conn.close()
                return False
            
            cursor.execute('''
                INSERT INTO users (user_id, username, created_at)
                VALUES (?, ?, datetime('now'))
            ''', (user_id, username))
            
            conn.commit()
            conn.close()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка регистрации пользователя: {e}")
            return False

    async def _get_user_city(self, user_id: int) -> Optional[str]:
        """Получает город пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT city FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            
            conn.close()
            return result[0] if result else None
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения города: {e}")
            return None

    async def _get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Получает настройки пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT city, notification_time, notifications_enabled FROM users WHERE user_id = ?',
                (user_id,)
            )
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                return {
                    'city': result[0],
                    'notification_time': result[1] or '09:00',
                    'notifications_enabled': bool(result[2])
                }
            else:
                return {
                    'city': None,
                    'notification_time': '09:00',
                    'notifications_enabled': False
                }
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения настроек: {e}")
            return {
                'city': None,
                'notification_time': '09:00',
                'notifications_enabled': False
            }

    async def _update_user_settings(self, user_id: int, city: str, 
                                  notification_time: str, notifications_enabled: bool) -> bool:
        """Обновляет настройки пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET city = ?, notification_time = ?, notifications_enabled = ?, updated_at = datetime('now')
                WHERE user_id = ?
            ''', (city, notification_time, int(notifications_enabled), user_id))
            
            conn.commit()
            conn.close()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления настроек: {e}")
            return False

    def set_notification_daemon(self, daemon) -> None:
        """Устанавливает демон уведомлений"""
        self.notification_daemon = daemon
        logger.info("Демон уведомлений установлен")

    def run(self) -> None:
        """Запускает бота"""
        logger.info("Запуск Telegram бота...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def stop(self) -> None:
        """Останавливает бота"""
        logger.info("Остановка Telegram бота...")
        await self.application.stop()
        await self.application.shutdown()


def create_bot(token: str, db_path: str, weather_api_key: str) -> ClearyFiTelegramBot:
    """Создает экземпляр бота"""
    return ClearyFiTelegramBot(token, db_path, weather_api_key)
