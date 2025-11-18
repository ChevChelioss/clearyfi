#!/usr/bin/env python3
"""
Обработчик управления подпиской
"""

from telegram import Update
from telegram.ext import ContextTypes

from .base import BaseHandler


class SubscriptionHandler(BaseHandler):
    """Обработчик для управления подпиской"""
    
    def __init__(self, locale_manager, database, subscription_service):
        super().__init__(locale_manager, database)
        self.subscription_service = subscription_service
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает запрос управления подпиской"""
        user_id = update.effective_user.id
        
        # Получаем статус подписки
        status_result = self.subscription_service.get_user_subscription_status(user_id)
        
        if not status_result['success']:
            await self.send_response(
                update,
                status_result['message'],
                reply_markup=self.get_main_keyboard()
            )
            return
        
        # Создаем клавиатуру для управления подпиской
        subscription_keyboard = self.get_subscription_keyboard(status_result['subscribed'])
        
        # Формируем сообщение о статусе
        if status_result['subscribed']:
            message = self.locale.get_message(
                'subscription_active',
                city=status_result['city'],
                notification_time=status_result['notification_time']
            )
        else:
            message = self.locale.get_message(
                'subscription_inactive', 
                city=status_result['city']
            )
        
        await self.send_response(
            update,
            message,
            reply_markup=subscription_keyboard,
        )
    
    async def handle_subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает подписку на уведомления"""
        user_id = update.effective_user.id
        
        result = self.subscription_service.subscribe_user(user_id)
        
        await self.send_response(
            update,
            result['message'],
            reply_markup=self.get_main_keyboard(),
        )
    
    async def handle_unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает отписку от уведомлений"""
        user_id = update.effective_user.id
        
        result = self.subscription_service.unsubscribe_user(user_id)
        
        await self.send_response(
            update,
            result['message'],
            reply_markup=self.get_main_keyboard(),
        )
    
    async def handle_change_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает изменение времени уведомлений"""
        user_id = update.effective_user.id
        
        # Пока просто сообщение о том, что функция в разработке
        message = (
            "⏰ *Изменение времени уведомлений*\n\n"
            "Эта функция находится в разработке.\n"
            "Сейчас уведомления приходят в 09:00.\n\n"
            "Следите за обновлениями!"
        )
        
        await self.send_response(
            update,
            message,
            reply_markup=self.get_main_keyboard(),
        )
