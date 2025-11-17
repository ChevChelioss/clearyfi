#!/usr/bin/env python3
"""
Обработчик команды /help и кнопки помощи
"""

from telegram import Update
from telegram.ext import ContextTypes

from .base import BaseHandler


class HelpHandler(BaseHandler):
    """Обработчик для команды /help и кнопки помощи"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /help"""
        help_message = self.locale.get_message("help")
        
        await self.send_response(
            update,
            help_message,
            reply_markup=self.get_main_keyboard(),
            parse_mode='Markdown'
        )
