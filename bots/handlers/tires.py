#!/usr/bin/env python3
"""
Обработчик рекомендаций по шинам и шиномонтажу
"""

from telegram import Update
from telegram.ext import ContextTypes

from .base import BaseHandler


class TiresHandler(BaseHandler):
    """Обработчик для рекомендаций по шинам"""
    
    def __init__(self, locale_manager, database, tires_service):
        super().__init__(locale_manager, database)
        self.tires_service = tires_service
    
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
        
        # Показываем, что бот печатает
        await update.message.reply_chat_action(action='typing')
        
        # Получаем рекомендацию от сервиса
        result = self.tires_service.get_recommendation(user_city)
        
        # Отправляем рекомендацию
        if result["success"]:
            await self.send_response(
                update,
                result["recommendation"],
                reply_markup=self.get_main_keyboard(),
            )
        else:
            # Если сервис вернул ошибку, отправляем сообщение об ошибке
            await self.send_response(
                update,
                result["recommendation"],
                reply_markup=self.get_main_keyboard()
            )
