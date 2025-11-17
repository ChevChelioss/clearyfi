#!/usr/bin/env python3
"""
Обработчик рекомендаций по шинам
"""

from telegram import Update
from telegram.ext import ContextTypes

from .base import BaseHandler
from utils.date_utils import get_current_timestamp


class TiresHandler(BaseHandler):
    """Обработчик для рекомендаций по шинам"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает запрос рекомендации по шинам"""
        user_id = update.effective_user.id
        
        # Получаем город пользователя из базы данных
        user_city = self.database.get_user_city(user_id)
        
        if not user_city:
            # Если город не установлен, просим установить его
            city_not_set_message = self.locale.get_message("city_not_set")
            await self.send_response(
                update,
                city_not_set_message,
                reply_markup=self.get_main_keyboard()
            )
            return
        
        # Формируем рекомендацию
        timestamp = get_current_timestamp()
        tire_recommendation = self.locale.get_message(
            "tire_recommendation", 
            city=user_city,
            timestamp=timestamp
        )
        
        await self.send_response(
            update,
            tire_recommendation,
            reply_markup=self.get_main_keyboard(),
            parse_mode='Markdown'
        )
