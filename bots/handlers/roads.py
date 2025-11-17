#!/usr/bin/env python3
"""
Обработчик дорожных условий
"""

from telegram import Update
from telegram.ext import ContextTypes

from .base import BaseHandler
from utils.date_utils import get_current_timestamp


class RoadsHandler(BaseHandler):
    """Обработчик для дорожных условий"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает запрос дорожных условий"""
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
        
        # Формируем информацию о дорожных условиях
        timestamp = get_current_timestamp()
        road_conditions = self.locale.get_message(
            "road_conditions", 
            city=user_city,
            timestamp=timestamp
        )
        
        await self.send_response(
            update,
            road_conditions,
            reply_markup=self.get_main_keyboard(),
            parse_mode='Markdown'
        )
