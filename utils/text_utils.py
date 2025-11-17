#!/usr/bin/env python3
"""
Утилиты для работы с текстом
"""

import re
from typing import Dict, Any


def escape_markdown(text: str) -> str:
    """
    Экранирует символы Markdown для Telegram
    """
    if not text:
        return ""
    
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


def truncate_text(text: str, max_length: int = 4000) -> str:
    """
    Обрезает текст до максимальной длины, добавляя многоточие
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


def capitalize_first(text: str) -> str:
    """
    Делает первую букву строки заглавной
    """
    if not text:
        return ""
    
    return text[0].upper() + text[1:]


def remove_extra_spaces(text: str) -> str:
    """
    Удаляет лишние пробелы из текста
    """
    if not text:
        return ""
    
    return re.sub(r'\s+', ' ', text).strip()


def format_percentage(value: float) -> str:
    """
    Форматирует проценты
    """
    return f"{value:.0%}"


def format_temperature(temp: float) -> str:
    """
    Форматирует температуру
    """
    return f"{temp:.1f}°C"


def translate_weather_conditions(condition: str) -> str:
    """
    Переводит погодные условия с английского на русский
    """
    if not condition:
        return "неизвестно"
    
    translation_map = {
        # Ясные условия
        "Clear": "ясно",
        "Sunny": "солнечно",
        
        # Облачность
        "Partly cloudy": "переменная облачность",
        "Cloudy": "облачно",
        "Overcast": "пасмурно",
        
        # Осадки
        "Light rain": "небольшой дождь",
        "Rain": "дождь",
        "Heavy rain": "сильный дождь",
        "Light snow": "небольшой снег",
        "Snow": "снег",
        "Heavy snow": "сильный снег",
        "Sleet": "мокрый снег",
        "Freezing rain": "ледяной дождь",
        "Drizzle": "морось",
        
        # Грозы
        "Thunderstorm": "гроза",
        
        # Туман
        "Fog": "туман",
        "Mist": "дымка",
        
        # Ветрено
        "Windy": "ветрено",
    }
    
    # Приводим к нижнему регистру для поиска
    condition_lower = condition.lower()
    
    # Ищем точное совпадение
    if condition in translation_map:
        return translation_map[condition]
    
    # Ищем частичное совпадение
    for key, value in translation_map.items():
        if key.lower() in condition_lower:
            return value
    
    # Если не нашли, возвращаем оригинал
    return condition


def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
    """Безопасное получение значения из словаря"""
    if not dictionary:
        return default
    return dictionary.get(key, default)


def format_wind_speed(speed: float) -> str:
    """Форматирует скорость ветра"""
    return f"{speed:.1f} м/с"


def format_precipitation(amount: float) -> str:
    """Форматирует количество осадков"""
    if amount == 0:
        return "нет осадков"
    return f"{amount:.1f} мм"
