# utils/text_utils.py
from typing import List

def translate_weather_conditions(conditions: List[str]) -> str:
    """
    Переводит английские названия погодных условий на русский язык.
    
    Args:
        conditions: Список погодных условий от API (на английском)
        
    Returns:
        Строка с перечислением условий на русском языке
    """
    translation_map = {
        'Clear': 'Ясно',
        'Clouds': 'Облачно',
        'Rain': 'Дождь',
        'Drizzle': 'Морось',
        'Thunderstorm': 'Гроза',
        'Snow': 'Снег',
        'Mist': 'Туман',
        'Fog': 'Туман',
        'Haze': 'Дымка'
    }
    
    translated = []
    for condition in conditions:
        # Используем перевод если доступен, иначе оставляем оригинал
        translated_condition = translation_map.get(condition, condition)
        translated.append(translated_condition)
    
    return ', '.join(translated) if translated else 'Ясно'

def format_temperature(temp: float) -> str:
    """
    Форматирует температуру с учетом знака.
    
    Args:
        temp: Температура в градусах Цельсия
        
    Returns:
        Отформатированная строка температуры
    """
    return f"{temp:+.0f}°C"

def format_wind_speed(speed: float) -> str:
    """
    Форматирует скорость ветра.
    
    Args:
        speed: Скорость ветра в м/с
        
    Returns:
        Отформатированная строка скорости ветра
    """
    return f"{speed:.1f} м/с"
