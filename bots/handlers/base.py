#!/usr/bin/env python3
"""
Базовый класс для всех обработчиков ClearyFi
"""

from abc import ABC, abstractmethod
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes


class BaseHandler(ABC):
    """Базовый класс для всех обработчиков"""
    
    def __init__(self, locale_manager, database):
        self.locale = locale_manager
        self.database = database
    
    @abstractmethod
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Основной метод обработки сообщения"""
        pass
    
    async def send_response(self, update: Update, text: str, 
                          reply_markup: ReplyKeyboardMarkup = None,
                          parse_mode: str = None):
        """Универсальный метод отправки ответа"""
        if update.message:
            await update.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        else:
            await update.callback_query.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
    
    def get_main_keyboard(self):
        """Возвращает главную клавиатуру используя тексты из локализации"""
        buttons = [
            [
                self.locale.get_button('wash'),
                self.locale.get_button('tires')
            ],
            [
                self.locale.get_button('roads'),
                self.locale.get_button('maintenance')
            ],
            [
                self.locale.get_button('extended_weather'),
                self.locale.get_button('subscription')
            ],
            [
                self.locale.get_button('help'),
                self.locale.get_button('settings')
            ]
        ]
        
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    def get_city_selection_keyboard(self):
        """Возвращает клавиатуру для выбора города"""
        buttons = [
            [
                self.locale.get_button('MOSCOW'),
                self.locale.get_button('SAINT_PETERSBURG')
            ],
            [
                self.locale.get_button('EKATERINBURG'),
                self.locale.get_button('NOVOSIBIRSK')
            ],
            [
                self.locale.get_button('KAZAN'),
                self.locale.get_button('TYUMEN')  # ДОБАВЛЕНА ТЮМЕНЬ
            ],
            [
                self.locale.get_button('OTHER_CITY')
            ],
            [
                self.locale.get_button('back')
            ]
        ]
        
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    def get_subscription_keyboard(self, is_subscribed: bool):
        """Возвращает клавиатуру для управления подпиской"""
        buttons = []
        
        if is_subscribed:
            buttons.append([self.locale.get_button('unsubscribe')])
            buttons.append([self.locale.get_button('change_notification_time')])
        else:
            buttons.append([self.locale.get_button('subscribe')])
        
        buttons.append([self.locale.get_button('back')])
        
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
