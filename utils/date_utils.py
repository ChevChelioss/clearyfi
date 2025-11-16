# utils/date_utils.py
from datetime import datetime
from typing import Optional

def format_date_russian(date_str: str) -> str:
    """
    Преобразует дату в формате YYYY-MM-DD в красивый русский формат.
    Пример: '2025-11-21' -> '21 ноября, пятница'
    
    Args:
        date_str: Строка с датой в формате ГГГГ-ММ-ДД
        
    Returns:
        Отформатированная строка даты на русском языке
    """
    try:
        # Парсим дату из строки
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Словари для преобразования месяцев и дней недели
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
        
        # Получаем компоненты даты
        day = date_obj.day
        month = months.get(date_obj.month, '')
        english_day = date_obj.strftime('%A')
        day_of_week = days_of_week.get(english_day, '')
        
        return f"{day} {month}, {day_of_week}"
        
    except (ValueError, TypeError) as e:
        # В случае ошибки возвращаем оригинальную дату
        return date_str

def get_relative_day_label(date_str: str, base_date: Optional[str] = None) -> str:
    """
    Возвращает метку дня: 'Сегодня', 'Завтра' или отформатированную дату.
    
    Args:
        date_str: Строка с датой в формате ГГГГ-ММ-ДД
        base_date: Базовая дата для сравнения (по умолчанию сегодня)
        
    Returns:
        Строка с меткой дня
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
            return format_date_russian(date_str)
            
    except (ValueError, TypeError):
        return date_str
