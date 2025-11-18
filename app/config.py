#!/usr/bin/env python3
"""
Конфигурация приложения ClearyFi
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class DatabaseConfig:
    path: str = "clearyfi.db"


@dataclass
class BotConfig:
    token: str
    admin_ids: list[int]


@dataclass
class WeatherConfig:
    api_key: str
    provider: str = "openweather"


@dataclass
class AIConfig:
    """Конфигурация AI сервисов"""
    deepseek_api_key: str = None
    enabled: bool = False


class Config:
    """Централизованная конфигурация приложения"""
    
    def __init__(self):
        load_dotenv()
        self.bot = BotConfig(
            token=os.getenv("TELEGRAM_BOT_TOKEN"),
            admin_ids=[int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
        )
        self.database = DatabaseConfig(
            path=os.getenv("DATABASE_PATH", "clearyfi.db")
        )
        self.weather = WeatherConfig(
            api_key=os.getenv("WEATHER_API_KEY"),
            provider=os.getenv("WEATHER_PROVIDER", "openweather")
        )
        self.ai = AIConfig(
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
            enabled=bool(os.getenv("DEEPSEEK_API_KEY"))
        )
        
        self._validate()
    
    def _validate(self):
        """Проверка обязательных настроек"""
        if not self.bot.token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not self.weather.api_key:
            raise ValueError("WEATHER_API_KEY is required")
