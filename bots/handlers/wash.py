#!/usr/bin/env python3
"""
Обработчик рекомендаций по мойке
"""

from telegram import Update
from telegram.ext import ContextTypes

from .base import BaseHandler


class WashHandler(BaseHandler):
    """Обработчик для рекомендаций по мойке"""
    
    def __init__(self, locale_manager, database, wash_service):
        super().__init__(locale_manager, database)
        self.wash_service = wash_service
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает запрос рекомендации по мойке"""
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
        
        # Показываем, что бот печатает
        await update.message.reply_chat_action(action='typing')
        
        # Получаем рекомендацию от сервиса
        result = self.wash_service.get_recommendation(user_city)
        
        # Отправляем рекомендацию
        if result["success"]:
            await self.send_response(
                update,
                result["recommendation"],
                reply_markup=self.get_main_keyboard(),
                parse_mode='Markdown'
            )
        else:
            # Если сервис вернул ошибку, отправляем сообщение об ошибке
            await self.send_response(
                update,
                result["recommendation"],
                reply_markup=self.get_main_keyboard()
            )
