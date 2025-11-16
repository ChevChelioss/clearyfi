#!/usr/bin/env python3
"""
Telegram бот ClearyFi
Основной интерфейс для взаимодействия с пользователями через Telegram
"""

import logging
import sqlite3
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ContextTypes, ConversationHandler, filters
)

from services.weather.weather_service import WeatherService
from services.notifications.notification_daemon import NotificationDaemon
from services.notifications.message_builder import NotificationMessageBuilder
from utils.date_utils import format_date_russian

# Настройка логирования
logger = logging.getLogger('TelegramBot')

# Состояния для ConversationHandler
CITY_SELECTION, NOTIFICATION_TIME = range(2)

# Клавиатуры
main_keyboard = ReplyKeyboardMarkup([
    ['🌤 Текущая погода', '📊 Прогноз на 3 дня'],
    ['⏰ Настройка уведомлений', '🚗 Рекомендация мойки'],
    ['📈 Статистика', '❓ Помощь']
], resize_keyboard=True)

notification_keyboard = ReplyKeyboardMarkup([
    ['07:00', '08:00', '09:00'],
    ['10:00', '12:00', '14:00'],
    ['16:00', '18:00', '20:00'],
    ['🔙 Назад']
], resize_keyboard=True)

back_keyboard = ReplyKeyboardMarkup([
    ['🔙 Назад']
], resize_keyboard=True)


class ClearyFiTelegramBot:
    """
    Основной класс Telegram бота ClearyFi.
    Управляет всеми взаимодействиями с пользователями.
    """
    
    def __init__(self, token: str, db_path: str, weather_api_key: str):
        """
        Инициализация бота.
        
        Args:
            token: Токен Telegram бота
            db_path: Путь к базе данных
            weather_api_key: API ключ для погодного сервиса
        """
        self.token = token
        self.db_path = db_path
        self.weather_service = WeatherService(weather_api_key)
        self.bot = None
        self.notification_daemon = None
        
        # Создаем приложение Telegram
        self.application = Application.builder().token(token).build()
        
        # Регистрируем обработчики
        self._setup_handlers()
        
        # Статистика бота
        self.stats = {
            'users_count': 0,
            'commands_processed': 0,
            'weather_requests': 0,
            'start_time': datetime.now()
        }
        
        logger.info("ClearyFiTelegramBot инициализирован")

    def _setup_handlers(self) -> None:
        """Настраивает все обработчики команд и сообщений."""
        
        # Обработчики команд
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("weather", self._weather_command))
        self.application.add_handler(CommandHandler("forecast", self._forecast_command))
        self.application.add_handler(CommandHandler("wash", self._wash_recommendation_command))
        self.application.add_handler(CommandHandler("stats", self._stats_command))
        self.application.add_handler(CommandHandler("notifications", self._notifications_command))
        self.application.add_handler(CommandHandler("test", self._test_notification_command))
        
        # Обработчики сообщений с текстом
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self._handle_text_message
        ))
        
        # Conversation Handler для настройки уведомлений
        conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex('^⏰ Настройка уведомлений$'), self._setup_notifications_start)
            ],
            states={
                CITY_SELECTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._setup_notifications_city)
                ],
                NOTIFICATION_TIME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._setup_notifications_time)
                ],
            },
            fallbacks=[
                MessageHandler(filters.Regex('^🔙 Назад$'), self._cancel_setup)
            ],
        )
        
        self.application.add_handler(conv_handler)
        
        logger.debug("Обработчики бота настроены")

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработчик команды /start.
        Приветствует нового пользователя и регистрирует его в системе.
        """
        user = update.effective_user
        user_id = user.id
        
        logger.info(f"Новый пользователь: {user.first_name} (ID: {user_id})")
        
        # Регистрируем пользователя в базе данных
        if await self._register_user(user_id, user.first_name):
            welcome_message = (
                f"👋 Привет, {user.first_name}!\n\n"
                f"🚗 *ClearyFi* - ваш персональный помощник для ухода за автомобилем.\n\n"
                f"✨ *Что я умею:*\n"
                f"• 🌤 Показывать текущую погоду\n"
                f"• 📊 Давать прогноз на 3 дня\n"
                f"• 🚗 Рекомендовать лучшее время для мойки\n"
                f"• ⏰ Напоминать о подходящих днях\n\n"
                f"📝 *Как начать:*\n"
                f"1. Установите город командой /weather Город\n"
                f"2. Настройте уведомления через меню\n"
                f"3. Получайте рекомендации!\n\n"
                f"Используйте кнопки ниже или команды:\n"
                f"/weather - погода сейчас\n"
                f"/forecast - прогноз на 3 дня\n"
                f"/wash - рекомендация мойки\n"
                f"/help - справка"
            )
        else:
            welcome_message = (
                f"С возвращением, {user.first_name}!\n\n"
                f"Рад снова вас видеть! Чем могу помочь?"
            )
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=main_keyboard,
            parse_mode='Markdown'
        )
        
        self.stats['commands_processed'] += 1

    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработчик команды /help.
        Показывает справку по использованию бота.
        """
        help_message = (
            "📖 *Справка по ClearyFi*\n\n"
            
            "🌤 *Команды погоды:*\n"
            "`/weather [город]` - текущая погода\n"
            "`/forecast [город]` - прогноз на 3 дня\n"
            "Или используйте кнопку '🌤 Текущая погода'\n\n"
            
            "🚗 *Рекомендации мойки:*\n"
            "`/wash [город]` - лучшее время для мойки\n"
            "Или используйте кнопку '🚗 Рекомендация мойки'\n\n"
            
            "⏰ *Уведомления:*\n"
            "`/notifications` - настройка уведомлений\n"
            "Или используйте кнопку '⏰ Настройка уведомлений'\n\n"
            
            "📊 *Статистика:*\n"
            "`/stats` - ваша статистика\n\n"
            
            "🔧 *Тестирование:*\n"
            "`/test` - тестовое уведомление\n\n"
            
            "💡 *Советы:*\n"
            "• Установите город для быстрого доступа\n"
            "• Настройте уведомления в удобное время\n"
            "• Проверяйте прогноз перед мойкой\n\n"
            
            "❓ *Проблемы?*\n"
            "Если бот не отвечает, используйте /start"
        )
        
        await update.message.reply_text(
            help_message,
            reply_markup=main_keyboard,
            parse_mode='Markdown'
        )
        
        self.stats['commands_processed'] += 1

    async def _weather_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработчик команды /weather.
        Показывает текущую погоду в указанном городе.
        """
        user_id = update.effective_user.id
        
        # Получаем город из аргументов или из базы данных
        if context.args:
            city = ' '.join(context.args)
        else:
            city = await self._get_user_city(user_id)
            if not city:
                await update.message.reply_text(
                    "🌤 *Погода*\n\n"
                    "Укажите город:\n"
                    "`/weather Москва`\n\n"
                    "Или установите город через настройки уведомлений.",
                    parse_mode='Markdown'
                )
                return
        
        await self._send_weather_response(update, city, user_id)

    async def _forecast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработчик команды /forecast.
        Показывает прогноз погоды на 3 дня.
        """
        user_id = update.effective_user.id
        
        # Получаем город из аргументов или из базы данных
        if context.args:
            city = ' '.join(context.args)
        else:
            city = await self._get_user_city(user_id)
            if not city:
                await update.message.reply_text(
                    "📊 *Прогноз погоды*\n\n"
                    "Укажите город:\n"
                    "`/forecast Москва`\n\n"
                    "Или установите город через настройки уведомлений.",
                    parse_mode='Markdown'
                )
                return
        
        await self._send_forecast_response(update, city, user_id)

    async def _wash_recommendation_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработчик команды /wash.
        Показывает рекомендации по мойке автомобиля.
        """
        user_id = update.effective_user.id
        
        # Получаем город из аргументов или из базы данных
        if context.args:
            city = ' '.join(context.args)
        else:
            city = await self._get_user_city(user_id)
            if not city:
                await update.message.reply_text(
                    "🚗 *Рекомендация мойки*\n\n"
                    "Укажите город:\n"
                    "`/wash Москва`\n\n"
                    "Или установите город через настройки уведомлений.",
                    parse_mode='Markdown'
                )
                return
        
        await self._send_wash_recommendation(update, city, user_id)

    async def _stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработчик команды /stats.
        Показывает статистику пользователя и бота.
        """
        user_id = update.effective_user.id
        
        # Получаем статистику пользователя
        user_stats = await self._get_user_stats(user_id)
        bot_stats = self._get_bot_stats()
        
        stats_message = (
            "📊 *Статистика ClearyFi*\n\n"
            
            "👤 *Ваша статистика:*\n"
            f"• Запросов погоды: {user_stats['weather_requests']}\n"
            f"• Получено уведомлений: {user_stats['notifications_received']}\n"
            f"• Город: {user_stats['city'] or 'Не установлен'}\n"
            f"• Уведомления: {'✅ Вкл' if user_stats['notifications_enabled'] else '❌ Выкл'}\n\n"
            
            "🤖 *Статистика бота:*\n"
            f"• Пользователей: {bot_stats['users_count']}\n"
            f"• Команд обработано: {bot_stats['commands_processed']}\n"
            f"• Запросов погоды: {bot_stats['weather_requests']}\n"
            f"• Работает с: {bot_stats['uptime']}\n\n"
            
            "🚗 *Использование:*\n"
            "Продолжайте использовать бота для получения актуальных рекомендаций!"
        )
        
        await update.message.reply_text(
            stats_message,
            reply_markup=main_keyboard,
            parse_mode='Markdown'
        )
        
        self.stats['commands_processed'] += 1

    async def _notifications_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработчик команды /notifications.
        Показывает текущие настройки уведомлений.
        """
        user_id = update.effective_user.id
        user_settings = await self._get_user_settings(user_id)
        
        if user_settings['city']:
            status = "✅ Включены" if user_settings['notifications_enabled'] else "❌ Выключены"
            message = (
                "⏰ *Настройки уведомлений*\n\n"
                f"• Город: {user_settings['city']}\n"
                f"• Время уведомлений: {user_settings['notification_time']}\n"
                f"• Статус: {status}\n\n"
                "Используйте кнопку '⏰ Настройка уведомлений' для изменения."
            )
        else:
            message = (
                "⏰ *Настройки уведомлений*\n\n"
                "Уведомления не настроены.\n\n"
                "Используйте кнопку '⏰ Настройка уведомлений' для настройки."
            )
        
        await update.message.reply_text(
            message,
            reply_markup=main_keyboard,
            parse_mode='Markdown'
        )
        
        self.stats['commands_processed'] += 1

    async def _test_notification_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработчик команды /test.
        Отправляет тестовое уведомление.
        """
        user_id = update.effective_user.id
        city = await self._get_user_city(user_id)
        
        if not city:
            await update.message.reply_text(
                "❌ *Тестовое уведомление*\n\n"
                "Сначала установите город через настройки уведомлений.",
                parse_mode='Markdown'
            )
            return
        
        await update.message.reply_text(
            f"🧪 Отправляю тестовое уведомление для {city}...",
            reply_markup=main_keyboard
        )
        
        # Отправляем тестовое уведомление через демон
        if self.notification_daemon:
            await self.notification_daemon.send_test_notification(user_id, city)
        else:
            await update.message.reply_text(
                "❌ Демон уведомлений не активен.",
                reply_markup=main_keyboard
            )
        
        self.stats['commands_processed'] += 1

    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обрабатывает текстовые сообщения (кнопки главного меню).
        """
        text = update.message.text
        user_id = update.effective_user.id
        
        logger.info(f"Текстовое сообщение от {user_id}: {text}")
        
        if text == '🌤 Текущая погода':
            city = await self._get_user_city(user_id)
            if city:
                await self._send_weather_response(update, city, user_id)
            else:
                await update.message.reply_text(
                    "Сначала установите город через '⏰ Настройка уведомлений'",
                    reply_markup=main_keyboard
                )
                
        elif text == '📊 Прогноз на 3 дня':
            city = await self._get_user_city(user_id)
            if city:
                await self._send_forecast_response(update, city, user_id)
            else:
                await update.message.reply_text(
                    "Сначала установите город через '⏰ Настройка уведомлений'",
                    reply_markup=main_keyboard
                )
                
        elif text == '🚗 Рекомендация мойки':
            city = await self._get_user_city(user_id)
            if city:
                await self._send_wash_recommendation(update, city, user_id)
            else:
                await update.message.reply_text(
                    "Сначала установите город через '⏰ Настройка уведомлений'",
                    reply_markup=main_keyboard
                )
                
        elif text == '📈 Статистика':
            await self._stats_command(update, context)
            
        elif text == '❓ Помощь':
            await self._help_command(update, context)
            
        else:
            await update.message.reply_text(
                "Используйте кнопки меню или команды для взаимодействия с ботом.",
                reply_markup=main_keyboard
            )
        
        self.stats['commands_processed'] += 1

    async def _setup_notifications_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Начинает процесс настройки уведомлений.
        """
        await update.message.reply_text(
            "⏰ *Настройка уведомлений*\n\n"
            "Введите название вашего города:\n"
            "Пример: `Москва` или `Санкт-Петербург`",
            reply_markup=back_keyboard,
            parse_mode='Markdown'
        )
        
        return CITY_SELECTION

    async def _setup_notifications_city(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Обрабатывает ввод города для уведомлений.
        """
        city = update.message.text
        
        # Проверяем валидность города
        if await self._is_city_valid(city):
            context.user_data['city'] = city
            
            await update.message.reply_text(
                f"✅ Город `{city}` найден!\n\n"
                "Теперь выберите время для ежедневных уведомлений:",
                reply_markup=notification_keyboard,
                parse_mode='Markdown'
            )
            
            return NOTIFICATION_TIME
        else:
            await update.message.reply_text(
                f"❌ Город `{city}` не найден.\n\n"
                "Пожалуйста, проверьте написание и введите еще раз:",
                reply_markup=back_keyboard,
                parse_mode='Markdown'
            )
            
            return CITY_SELECTION

    async def _setup_notifications_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Обрабатывает выбор времени для уведомлений.
        """
        time_text = update.message.text
        city = context.user_data.get('city')
        user_id = update.effective_user.id
        
        if time_text in ['07:00', '08:00', '09:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00']:
            # Сохраняем настройки пользователя
            success = await self._update_user_settings(
                user_id=user_id,
                city=city,
                notification_time=time_text,
                notifications_enabled=True
            )
            
            if success:
                await update.message.reply_text(
                    f"✅ *Настройки сохранены!*\n\n"
                    f"• Город: `{city}`\n"
                    f"• Время уведомлений: `{time_text}`\n"
                    f"• Статус: `Включено`\n\n"
                    f"Ежедневно в {time_text} вы будете получать прогноз погоды "
                    f"и рекомендации по мойке автомобиля.",
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
                "Пожалуйста, выберите время из предложенных вариантов:",
                reply_markup=notification_keyboard
            )
            
            return NOTIFICATION_TIME

    async def _cancel_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Отменяет процесс настройки.
        """
        await update.message.reply_text(
            "Настройка уведомлений отменена.",
            reply_markup=main_keyboard
        )
        
        return ConversationHandler.END

    async def _send_weather_response(self, update: Update, city: str, user_id: int) -> None:
        """
        Отправляет ответ с текущей погодой.
        """
        try:
            await update.message.reply_chat_action(action='typing')
            
            # Получаем данные о погоде
            weather_data = self.weather_service.get_immediate_forecast(city)
            
            if weather_data and weather_data.get('current_weather'):
                message = NotificationMessageBuilder.build_current_weather_message(
                    city=city,
                    current_weather=weather_data['current_weather']
                )
                
                await update.message.reply_text(
                    message,
                    reply_markup=main_keyboard,
                    parse_mode='Markdown'
                )
                
                # Обновляем статистику
                await self._increment_weather_requests(user_id)
                self.stats['weather_requests'] += 1
                
            else:
                await update.message.reply_text(
                    f"❌ Не удалось получить данные о погоде в `{city}`.\n"
                    f"Проверьте название города и попробуйте еще раз.",
                    reply_markup=main_keyboard,
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Ошибка отправки погоды: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при получении данных о погоде.",
                reply_markup=main_keyboard
            )

    async def _send_forecast_response(self, update: Update, city: str, user_id: int) -> None:
        """
        Отправляет ответ с прогнозом на 3 дня.
        """
        try:
            await update.message.reply_chat_action(action='typing')
            
            # Получаем данные о погоде
            weather_data = self.weather_service.get_city_forecast(city, days=3)
            
            if weather_data:
                message = NotificationMessageBuilder.build_weather_notification(
                    city=city,
                    daily_summary=weather_data['daily_summary'],
                    best_day=weather_data.get('best_wash_day')
                )
                
                await update.message.reply_text(
                    message,
                    reply_markup=main_keyboard,
                    parse_mode='Markdown'
                )
                
                # Обновляем статистику
                await self._increment_weather_requests(user_id)
                self.stats['weather_requests'] += 1
                
            else:
                await update.message.reply_text(
                    f"❌ Не удалось получить прогноз для `{city}`.\n"
                    f"Проверьте название города и попробуйте еще раз.",
                    reply_markup=main_keyboard,
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Ошибка отправки прогноза: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при получении прогноза погоды.",
                reply_markup=main_keyboard
            )

    async def _send_wash_recommendation(self, update: Update, city: str, user_id: int) -> None:
        """
        Отправляет рекомендацию по мойке автомобиля.
        """
        try:
            await update.message.reply_chat_action(action='typing')
            
            # Получаем данные о погоде
            weather_data = self.weather_service.get_city_forecast(city, days=3)
            
            if weather_data:
                message = NotificationMessageBuilder.build_weather_notification(
                    city=city,
                    daily_summary=weather_data['daily_summary'],
                    best_day=weather_data.get('best_wash_day')
                )
                
                await update.message.reply_text(
                    message,
                    reply_markup=main_keyboard,
                    parse_mode='Markdown'
                )
                
                # Обновляем статистику
                await self._increment_weather_requests(user_id)
                self.stats['weather_requests'] += 1
                
            else:
                await update.message.reply_text(
                    f"❌ Не удалось получить данные для рекомендации в `{city}`.",
                    reply_markup=main_keyboard,
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Ошибка отправки рекомендации: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при формировании рекомендации.",
                reply_markup=main_keyboard
            )

    # Методы работы с базой данных
    async def _register_user(self, user_id: int, username: str) -> bool:
        """
        Регистрирует нового пользователя в базе данных.
        
        Args:
            user_id: ID пользователя Telegram
            username: Имя пользователя
            
        Returns:
            True если пользователь новый, False если уже существует
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем существование пользователя
            cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                conn.close()
                return False
            
            # Регистрируем нового пользователя
            cursor.execute('''
                INSERT INTO users (user_id, username, created_at, weather_requests)
                VALUES (?, ?, datetime('now'), 0)
            ''', (user_id, username))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Зарегистрирован новый пользователь: {username} (ID: {user_id})")
            self._update_users_count()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка регистрации пользователя: {e}")
            return False

    async def _get_user_city(self, user_id: int) -> Optional[str]:
        """
        Получает город пользователя из базы данных.
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            Название города или None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT city FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            
            conn.close()
            
            return result[0] if result else None
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения города пользователя: {e}")
            return None

    async def _get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """
        Получает настройки пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            Словарь с настройками пользователя
        """
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
            logger.error(f"Ошибка получения настроек пользователя: {e}")
            return {
                'city': None,
                'notification_time': '09:00',
                'notifications_enabled': False
            }

    async def _update_user_settings(self, user_id: int, city: str, 
                                  notification_time: str, notifications_enabled: bool) -> bool:
        """
        Обновляет настройки пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            city: Город
            notification_time: Время уведомлений
            notifications_enabled: Включены ли уведомления
            
        Returns:
            True если успешно, False при ошибке
        """
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
            
            logger.info(f"Обновлены настройки пользователя {user_id}: город={city}, время={notification_time}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления настроек пользователя: {e}")
            return False

    async def _get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Получает статистику пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            Словарь со статистикой пользователя
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT weather_requests, notifications_received, city, notifications_enabled FROM users WHERE user_id = ?',
                (user_id,)
            )
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                return {
                    'weather_requests': result[0] or 0,
                    'notifications_received': result[1] or 0,
                    'city': result[2],
                    'notifications_enabled': bool(result[3])
                }
            else:
                return {
                    'weather_requests': 0,
                    'notifications_received': 0,
                    'city': None,
                    'notifications_enabled': False
                }
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения статистики пользователя: {e}")
            return {
                'weather_requests': 0,
                'notifications_received': 0,
                'city': None,
                'notifications_enabled': False
            }

    async def _increment_weather_requests(self, user_id: int) -> None:
        """
        Увеличивает счетчик запросов погоды для пользователя.
        
        Args:
            user_id: ID пользователя Telegram
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET weather_requests = COALESCE(weather_requests, 0) + 1,
                    updated_at = datetime('now')
                WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления счетчика запросов: {e}")

    async def _is_city_valid(self, city: str) -> bool:
        """
        Проверяет валидность города через погодный сервис.
        
        Args:
            city: Название города для проверки
            
        Returns:
            True если город существует, False в противном случае
        """
        try:
            return self.weather_service.validate_city(city)
        except Exception as e:
            logger.error(f"Ошибка проверки города {city}: {e}")
            return False

    def _update_users_count(self) -> None:
        """Обновляет количество пользователей в статистике."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            result = cursor.fetchone()
            
            conn.close()
            
            self.stats['users_count'] = result[0] if result else 0
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка подсчета пользователей: {e}")

    def _get_bot_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику бота.
        
        Returns:
            Словарь со статистикой бота
        """
        uptime = datetime.now() - self.stats['start_time']
        hours, remainder = divmod(uptime.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return {
            'users_count': self.stats['users_count'],
            'commands_processed': self.stats['commands_processed'],
            'weather_requests': self.stats['weather_requests'],
            'uptime': f"{int(hours)}ч {int(minutes)}м {int(seconds)}с"
        }

    def set_notification_daemon(self, daemon) -> None:
        """
        Устанавливает демон уведомлений для бота.
        
        Args:
            daemon: Экземпляр NotificationDaemon
        """
        self.notification_daemon = daemon
        logger.info("Демон уведомлений установлен для бота")

    def run(self) -> None:
            """
            Запускает бота.
            """
            logger.info("Запуск Telegram бота...")
            
            # ✅ ИНИЦИАЛИЗИРУЕМ bot ПЕРЕД ЗАПУСКОМ
            self.bot = self.application.bot
            
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def stop(self) -> None:
        """
        Останавливает бота.
        """
        logger.info("Остановка Telegram бота...")
        await self.application.stop()
        await self.application.shutdown()



def create_bot(token: str, db_path: str, weather_api_key: str) -> ClearyFiTelegramBot:
    """
    Создает и возвращает экземпляр бота.
    
    Args:
        token: Токен Telegram бота
        db_path: Путь к базе данных
        weather_api_key: API ключ для погодного сервиса
        
    Returns:
        Экземпляр ClearyFiTelegramBot
    """
    return ClearyFiTelegramBot(token, db_path, weather_api_key)


if __name__ == "__main__":
    print("Это модуль Telegram бота. Запустите main.py для запуска приложения.")
