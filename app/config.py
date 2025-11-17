#!/usr/bin/env python3
"""
Конфигурация приложения ClearyFi
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class DatabaseConfig:
    """Конфигурация базы данных"""
    path: str = "clearyfi.db"


@dataclass
class BotConfig:
    """Конфигурация бота"""
    token: str
    admin_ids: list[int]


@dataclass
class WeatherConfig:
    """Конфигурация погодного сервиса"""
    api_key: str
    provider: str = "openweather"


class Config:
    """
    Главный класс конфигурации.
    Загружает все настройки из переменных окружения.
    """
    
    def __init__(self):
        # Загружаем переменные из .env файла
        load_dotenv()
        
        # Настройки бота
        self.bot = BotConfig(
            token=os.getenv("TELEGRAM_BOT_TOKEN"),
            admin_ids=self._parse_admin_ids(os.getenv("ADMIN_IDS", ""))
        )
        
        # Настройки базы данных
        self.database = DatabaseConfig(
            path=os.getenv("DATABASE_PATH", "clearyfi.db")
        )
        
        # Настройки погоды
        self.weather = WeatherConfig(
            api_key=os.getenv("WEATHER_API_KEY"),
            provider=os.getenv("WEATHER_PROVIDER", "openweather")
        )
        
        # Дополнительные настройки
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Проверяем обязательные настройки
        self._validate()
    
    def _parse_admin_ids(self, admin_ids_str: str) -> list[int]:
        """Преобразует строку с ID администраторов в список чисел"""
        if not admin_ids_str:
            return []
        
        try:
            return [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
        except ValueError:
            return []
    
    def _validate(self):
        """Проверяет, что все обязательные настройки установлены"""
        errors = []
        
        if not self.bot.token:
            errors.append("TELEGRAM_BOT_TOKEN не установлен в .env файле")
        
        if not self.weather.api_key:
            errors.append("WEATHER_API_KEY не установлен в .env файле")
        
        if errors:
            error_message = "\n".join(errors)
            raise ValueError(f"Ошибки конфигурации:\n{error_message}")
