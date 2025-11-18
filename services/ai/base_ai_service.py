#!/usr/bin/env python3
"""
Базовый класс для всех AI сервисов ClearyFi
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.logger import logger


class BaseAIService(ABC):
    """Базовый класс для AI сервисов"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    @abstractmethod
    def get_recommendation(self, weather_data: Dict[str, Any], context: str) -> Optional[str]:
        """Получает рекомендацию от AI сервиса"""
        pass
    
    @abstractmethod
    def _build_prompt(self, weather_data: Dict[str, Any], context: str) -> str:
        """Строит промпт для AI"""
        pass
    
    def is_available(self) -> bool:
        """Проверяет, доступен ли сервис"""
        return bool(self.api_key and self.base_url)
