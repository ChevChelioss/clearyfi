#!/usr/bin/env python3
"""
Пакет AI сервисов ClearyFi
Интеграция искусственного интеллекта для улучшения рекомендаций
"""

from .deepseek_service import DeepSeekService
from .base_ai_service import BaseAIService

__all__ = [
    'DeepSeekService',
    'BaseAIService'
]
