#!/usr/bin/env python3
"""
Обработчик команды /start
"""

from telegram import Update
from telegram.ext import ContextTypes

from .base import BaseHandler


class StartHandler(BaseHandler):
    """Обработчик для команды /start"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /start"""
        user = update.effective_user
        user_id = user.id
        username = user.username or user.first_name
        
        # Создаем пользователя в базе данных, если его нет
        self.database.create_user(user_id, username)
        
        welcome_message = self.locale.get_message("welcome", user_name=username)
        
        await self.send_response(
            update,
            welcome_message,
            reply_markup=self.get_main_keyboard(),
            parse_mode='Markdown'
        )
