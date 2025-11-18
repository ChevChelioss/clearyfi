#!/usr/bin/env python3
"""
Пакет утилит ClearyFi
"""

from .date_utils import get_current_timestamp, get_current_time, format_date_short, is_time_for_notification, get_time_until_notification
from .text_utils import (
    escape_markdown, truncate_text, capitalize_first, remove_extra_spaces, 
    format_percentage, format_temperature, translate_weather_conditions, 
    safe_get, format_wind_speed, format_precipitation,
    translate_comfort_level, translate_driving_conditions  # ДОБАВЛЕНЫ НОВЫЕ ФУНКЦИИ
)

__all__ = [
    'get_current_timestamp',
    'get_current_time',
    'format_date_short',
    'is_time_for_notification',
    'get_time_until_notification',
    'escape_markdown',
    'truncate_text',
    'capitalize_first',
    'remove_extra_spaces',
    'format_percentage',
    'format_temperature',
    'translate_weather_conditions',
    'safe_get',
    'format_wind_speed',
    'format_precipitation',
    'translate_comfort_level',      # ДОБАВЛЕНЫ
    'translate_driving_conditions'  # ДОБАВЛЕНЫ
]
