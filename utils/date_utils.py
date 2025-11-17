#!/usr/bin/env python3
"""
Утилиты для работы с датами в ClearyFi
"""

from datetime import datetime
from typing import Optional

def format_date_russian(date_str: str) -> str:
    """
    Преобразует дату в формате YYYY-MM-DD в красивый русский формат.
    Пример: '2025-11-21' -> '21 ноября, пятница'
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        months = {
            1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
            5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
            9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
        }
        
        days_of_week = {
            'Monday': 'понедельник',
            'Tuesday': 'вторник', 
            'Wednesday': 'среда',
            'Thursday': 'четверг',
            'Friday': 'пятница',
            'Saturday': 'суббота',
            'Sunday': 'воскресенье'
        }
        
        day = date_obj.day
        month = months.get(date_obj.month, '')
        english_day = date_obj.strftime('%A')
        day_of_week = days_of_week.get(english_day, '')
        
        return f"{day} {month}, {day_of_week}"
        
    except (ValueError, TypeError) as e:
        return date_str

def format_date_short(date_str: str) -> str:
    """
    Форматирует дату в короткий формат: 'Пн, 17.11'
    
    Args:
        date_str: Строка с датой в формате ГГГГ-ММ-ДД
        
    Returns:
        Строка в формате 'Пн, 17.11'
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Сокращенные названия дней недели
        short_days = {
            'Monday': 'Пн',
            'Tuesday': 'Вт', 
            'Wednesday': 'Ср',
            'Thursday': 'Чт',
            'Friday': 'Пт',
            'Saturday': 'Сб',
            'Sunday': 'Вс'
        }
        
        english_day = date_obj.strftime('%A')
        day_of_week = short_days.get(english_day, '')
        day_month = date_obj.strftime('%d.%m')
        
        return f"{day_of_week}, {day_month}"
        
    except (ValueError, TypeError):
        return date_str

def get_relative_day_label(date_str: str, base_date: Optional[str] = None) -> str:
    """
    Возвращает метку дня: 'Сегодня', 'Завтра' или отформатированную дату.
    """
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        if base_date:
            base = datetime.strptime(base_date, '%Y-%m-%d')
        else:
            base = datetime.now()
        
        delta = (target_date - base).days
        
        if delta == 0:
            return "Сегодня"
        elif delta == 1:
            return "Завтра"
        else:
            return format_date_short(date_str)
            
    except (ValueError, TypeError):
        return date_str

def get_current_date_str() -> str:
    """Возвращает текущую дату в формате YYYY-MM-DD"""
    return datetime.now().strftime('%Y-%m-%d')
