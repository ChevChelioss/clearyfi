#!/usr/bin/env python3
"""
Пакет сервисов рекомендаций ClearyFi
"""

from .wash import WashRecommendationService
from .tires import TireRecommendationService
from .roads import RoadConditionService
from .maintenance import MaintenanceService           # НОВЫЙ ИМПОРТ
from .extended_weather import ExtendedWeatherService  # НОВЫЙ ИМПОРТ

__all__ = [
    'WashRecommendationService',
    'TireRecommendationService', 
    'RoadConditionService',
    'MaintenanceService',
    'ExtendedWeatherService'
]
