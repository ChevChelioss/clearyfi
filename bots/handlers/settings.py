#!/usr/bin/env python3
"""
Обработчик настроек пользователя
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from .base import BaseHandler

# Состояния для ConversationHandler
CITY_SELECTION = 1


class SettingsHandler(BaseHandler):
    """Обработчик для настроек пользователя"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Основной метод обработки - перенаправляет в меню настроек города"""
        return await self.handle_city_selection(update, context)
    
    async def handle_city_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начинает процесс настройки города"""
        city_selection_message = self.locale.get_message("city_selection")
        
        await self.send_response(
            update,
            city_selection_message,
            reply_markup=self.get_city_selection_keyboard(),
            parse_mode='Markdown'
        )
        
        return CITY_SELECTION
    
    async def handle_city_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает ввод города пользователем"""
        user_id = update.effective_user.id
        city = update.message.text
        
        # Проверяем, является ли город одним из популярных
        popular_cities = [
            self.locale.get_button('MOSCOW'),
            self.locale.get_button('SAINT_PETERSBURG'),
            self.locale.get_button('EKATERINBURG'),
            self.locale.get_button('NOVOSIBIRSK'),
            self.locale.get_button('KAZAN'),
            self.locale.get_button('TYUMEN')
        ]
        
        if city in popular_cities or city == self.locale.get_button('OTHER_CITY'):
            if city == self.locale.get_button('OTHER_CITY'):
                await update.message.reply_text(
                    self.locale.get_message("city_input"),
                    parse_mode='Markdown'
                )
                return CITY_SELECTION
            else:
                # Сохраняем выбранный город
                success = self.database.update_user_city(user_id, city)
                
                if success:
                    await update.message.reply_text(
                        self.locale.get_message("city_set_success", city=city),
                        reply_markup=self.get_main_keyboard(),
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        "❌ Ошибка сохранения города",
                        reply_markup=self.get_main_keyboard()
                    )
                
                return ConversationHandler.END
        else:
            # Пользователь ввел название города вручную
            success = self.database.update_user_city(user_id, city)
            
            if success:
                await update.message.reply_text(
                    self.locale.get_message("city_set_success", city=city),
                    reply_markup=self.get_main_keyboard(),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ Ошибка сохранения города",
                    reply_markup=self.get_main_keyboard()
                )
            
            return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отменяет процесс настройки"""
        await update.message.reply_text(
            "Настройки отменены",
            reply_markup=self.get_main_keyboard()
        )
        
        return ConversationHandler.END
