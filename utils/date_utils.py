#!/usr/bin/env python3
"""
Утилиты для работы с датами и временем
"""

from datetime import datetime, timedelta


def get_current_timestamp() -> str:
    """
    Возвращает текущую дату и время в формате для отображения.
    
    Returns:
        Строка с датой и временем
    """
    return datetime.now().strftime('%d.%m.%Y %H:%M')


def get_current_time() -> str:
    """
    Возвращает текущее время в формате HH:MM.
    
    Returns:
        Строка с временем
    """
    return datetime.now().strftime('%H:%M')


def format_date_short(date_string: str) -> str:
    """
    Форматирует дату в короткий формат (день.месяц).
    
    Args:
        date_string: Строка с датой в формате YYYY-MM-DD
        
    Returns:
        Отформатированная дата
    """
    try:
        date_obj = datetime.strptime(date_string, '%Y-%m-%d')
        return date_obj.strftime('%d.%m')
    except (ValueError, TypeError):
        return date_string


def is_time_for_notification(notification_time: str) -> bool:
    """
    Проверяет, наступило ли время для отправки уведомления.
    
    Args:
        notification_time: Время уведомления в формате HH:MM
        
    Returns:
        True если текущее время совпадает с временем уведомления
    """
    try:
        current_time = datetime.now().strftime('%H:%M')
        return current_time == notification_time
    except Exception:
        return False


def get_time_until_notification(notification_time: str) -> str:
    """
    Вычисляет сколько времени осталось до уведомления.
    
    Args:
        notification_time: Время уведомления в формате HH:MM
        
    Returns:
        Строка с оставшимся временем
    """
    try:
        now = datetime.now()
        notify_time = datetime.strptime(notification_time, '%H:%M').replace(
            year=now.year, month=now.month, day=now.day
        )
        
        if notify_time < now:
            notify_time += timedelta(days=1)
        
        time_left = notify_time - now
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        
        return f"{hours:02d}:{minutes:02d}"
    except Exception:
        return "??:??"
