#!/usr/bin/env python3
"""
Обработчик команды /start
"""

from telegram import Update
from telegram.ext import ContextTypes

from .base import BaseHandler
from core.logger import logger


class StartHandler(BaseHandler):
    """Обработчик для команды /start"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /start"""
        user = update.effective_user
        user_id = user.id
        
        logger.info(f"👋 Новый пользователь: {user.first_name} (ID: {user_id})")
        
        # Регистрируем пользователя в базе данных
        self.database.add_user(user_id, user.first_name)
        
        # Отправляем приветственное сообщение
        welcome_message = self.locale.get_message("welcome", user_name=user.first_name)
        
        await self.send_response(
            update,
            welcome_message,
            reply_markup=self.get_main_keyboard(),
            parse_mode='Markdown'
        )
