#!/usr/bin/env python3
"""
Менеджер локализации для ClearyFi
Централизованное управление всеми текстами бота
"""

import os
import importlib.util
from typing import Dict, Any
from core.logger import logger


class LocaleManager:
    """
    Загружает и управляет всеми текстами бота.
    Все тексты хранятся в отдельных файлах для легкого редактирования.
    """
    
    def __init__(self, locale: str = "ru"):
        self.locale = locale
        self.buttons = {}
        self.messages = {}
        self.errors = {}
        
        self._load_locale()
        logger.info(f"✅ Локализация загружена: {locale}")
    
    def _load_locale(self):
        """Загружает все файлы локализации для выбранного языка"""
        locale_path = f"locales/{self.locale}"
        
        # Загружаем кнопки
        self.buttons = self._load_module(f"{locale_path}/buttons.py")
        
        # Загружаем сообщения
        self.messages = self._load_module(f"{locale_path}/messages.py")
        
        # Загружаем ошибки
        self.errors = self._load_module(f"{locale_path}/errors.py")
    
    def _load_module(self, file_path: str) -> Dict[str, Any]:
        """
        Динамически загружает Python файл как модуль.
        Это позволяет хранить тексты в обычных .py файлах.
        """
        if not os.path.exists(file_path):
            logger.warning(f"Файл локализации не найден: {file_path}")
            return {}
        
        try:
            # Создаем спецификацию модуля из файла
            spec = importlib.util.spec_from_file_location("locale_module", file_path)
            module = importlib.util.module_from_spec(spec)
            
            # Выполняем модуль (загружаем переменные)
            spec.loader.exec_module(module)
            
            # Собираем все переменные, которые не начинаются с '_'
            result = {}
            for key, value in vars(module).items():
                if not key.startswith('_') and not callable(value):
                    result[key] = value
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка загрузки локализации {file_path}: {e}")
            return {}
    
    def get_button(self, key: str, default: str = None) -> str:
        """
        Возвращает текст кнопки по ключу.
        Если ключ не найден, возвращает default или сам ключ.
        """
        return self.buttons.get(key, default or key)
    
    def get_message(self, key: str, **kwargs) -> str:
        """
        Возвращает сообщение по ключу.
        Поддерживает подстановку значений через {переменные}.
        
        Пример:
            get_message("welcome", user_name="Иван") 
            заменит {user_name} на "Иван"
        """
        message = self.messages.get(key, key)
        
        try:
            # Заменяем {переменные} в тексте
            return message.format(**kwargs) if kwargs else message
        except KeyError as e:
            logger.warning(f"Не найдена переменная {e} в сообщении '{key}'")
            return message
    
    def get_error(self, key: str, **kwargs) -> str:
        """Возвращает текст ошибки по ключу"""
        error = self.errors.get(key, key)
        return error.format(**kwargs) if kwargs else error
    
    def get_main_keyboard(self):
        """
        Возвращает основную клавиатуру меню.
        Все кнопки берутся из файла локализации.
        """
        from telegram import ReplyKeyboardMarkup
        
        return ReplyKeyboardMarkup([
            [self.get_button("wash"), self.get_button("tires")],
            [self.get_button("roads"), self.get_button("subscription")],
            [self.get_button("help"), self.get_button("settings")]
        ], resize_keyboard=True)
