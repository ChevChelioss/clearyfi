#!/usr/bin/env python3
"""
Пакет сервисов рекомендаций ClearyFi
"""

from .wash import WashRecommendationService
from .tires import TireRecommendationService
from .roads import RoadConditionService
from .maintenance import MaintenanceService
from .extended_weather import ExtendedWeatherService

__all__ = [
    'WashRecommendationService',
    'TireRecommendationService', 
    'RoadConditionService',
    'MaintenanceService',
    'ExtendedWeatherService'
]
