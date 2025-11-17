#!/usr/bin/env python3
"""
Базовый класс для всех обработчиков бота
"""

from abc import ABC, abstractmethod
from telegram import Update
from telegram.ext import ContextTypes

from core.logger import logger


class BaseHandler(ABC):
    """Базовый класс для всех обработчиков сообщений бота"""
    
    def __init__(self, locale_manager, database):
        self.locale = locale_manager
        self.database = database
    
    @abstractmethod
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Основной метод обработки сообщения.
        Должен быть реализован в каждом обработчике.
        """
        pass
    
    async def send_response(self, update: Update, text: str, **kwargs):
        """
        Универсальный метод для отправки ответа.
        
        Args:
            update: Объект Update от Telegram
            text: Текст для отправки
            **kwargs: Дополнительные параметры (reply_markup, parse_mode и т.д.)
        """
        try:
            await update.message.reply_text(text, **kwargs)
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
    
    def get_main_keyboard(self):
        """Возвращает основную клавиатуру меню"""
        return self.locale.get_main_keyboard()
