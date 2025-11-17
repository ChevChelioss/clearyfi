#!/usr/bin/env python3
"""
Обработчик управления подпиской
"""

from telegram import Update
from telegram.ext import ContextTypes

from .base import BaseHandler


class SubscriptionHandler(BaseHandler):
    """Обработчик для управления подпиской"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает запрос управления подпиской"""
        user_id = update.effective_user.id
        
        # Получаем информацию о пользователе
        user_city = self.database.get_user_city(user_id)
        is_subscribed = self.database.is_user_subscribed(user_id)
        
        if user_city:
            if is_subscribed:
                message = self.locale.get_message("subscription_active", city=user_city)
            else:
                message = self.locale.get_message("subscription_inactive", city=user_city)
        else:
            message = self.locale.get_message("subscription_management")
        
        await self.send_response(
            update,
            message,
            reply_markup=self.get_main_keyboard(),
            parse_mode='Markdown'
        )
