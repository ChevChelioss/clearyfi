#!/usr/bin/env python3
"""
Обработчик настроек (выбор города)
"""

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from .base import BaseHandler
from core.logger import logger

# Состояния для ConversationHandler - выносим в константы модуля
CITY_SELECTION = 1


class SettingsHandler(BaseHandler):
    """Обработчик для настроек (выбор города)"""
    
    # Добавляем константу состояния как атрибут класса
    CITY_SELECTION = CITY_SELECTION
    
    async def handle_city_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начинает процесс выбора города"""
        city_selection_message = self.locale.get_message("city_selection")
        
        # Создаем клавиатуру с популярными городами
        popular_cities = [
            [self.locale.get_button("MOSCOW"), self.locale.get_button("SAINT_PETERSBURG")],
            [self.locale.get_button("EKATERINBURG"), self.locale.get_button("NOVOSIBIRSK")],
            [self.locale.get_button("KAZAN"), self.locate.get_button("TYUMEN")],
            [self.locale.get_button("other_city"), self.locale.get_button("back")]
        ]
        
        keyboard = ReplyKeyboardMarkup(popular_cities, resize_keyboard=True)
        
        await self.send_response(
            update,
            city_selection_message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        return CITY_SELECTION
    
    async def handle_city_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает ввод города пользователем"""
        user_id = update.effective_user.id
        city_input = update.message.text
        
        # Обработка специальных кнопок
        if city_input == self.locale.get_button("back"):
            await self.send_response(
                update,
                "Возвращаемся в главное меню...",
                reply_markup=self.get_main_keyboard()
            )
            return ConversationHandler.END
        
        if city_input == self.locale.get_button("other_city"):
            city_input_message = self.locale.get_message("city_input")
            await self.send_response(
                update,
                city_input_message,
                reply_markup=ReplyKeyboardMarkup([[self.locale.get_button("back")]], resize_keyboard=True),
                parse_mode='Markdown'
            )
            return CITY_SELECTION
        
        # Сохраняем город в базу данных
        success = self.database.update_user_city(user_id, city_input)
        
        if success:
            city_set_message = self.locale.get_message("city_set_success", city=city_input)
            await self.send_response(
                update,
                city_set_message,
                reply_markup=self.get_main_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await self.send_response(
                update,
                "❌ Ошибка сохранения города. Попробуйте позже.",
                reply_markup=self.get_main_keyboard()
            )
        
        return ConversationHandler.END
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /settings"""
        await self.handle_city_selection(update, context)
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отменяет процесс настройки"""
        await self.send_response(
            update,
            "Настройка отменена.",
            reply_markup=self.get_main_keyboard()
        )
        return ConversationHandler.END
