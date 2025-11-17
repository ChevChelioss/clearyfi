#!/usr/bin/env python3
"""
Нормализация и управление городами для ClearyFi
"""

from telegram import ReplyKeyboardMarkup

class CityNormalizer:
    """Класс для работы с городами"""
    
    # Популярные города России с правильными названиями для API
    POPULAR_CITIES = {
        'Москва': 'Moscow',
        'Санкт-Петербург': 'Saint Petersburg',
        'Новосибирск': 'Novosibirsk',
        'Екатеринбург': 'Yekaterinburg',
        'Казань': 'Kazan',
        'Нижний Новгород': 'Nizhny Novgorod',
        'Челябинск': 'Chelyabinsk',
        'Самара': 'Samara',
        'Омск': 'Omsk',
        'Ростов-на-Дону': 'Rostov-on-Don',
        'Уфа': 'Ufa',
        'Красноярск': 'Krasnoyarsk',
        'Воронеж': 'Voronezh',
        'Пермь': 'Perm',
        'Волгоград': 'Volgograd'
    }
    
    @classmethod
    def get_popular_cities_keyboard(cls):
        """Возвращает клавиатуру с популярными городами"""
        cities = list(cls.POPULAR_CITIES.keys())
        keyboard = []
        
        # Создаем строки по 2 города
        for i in range(0, len(cities), 2):
            row = cities[i:i+2]
            keyboard.append(row)
        
        # Добавляем кнопку ручного ввода
        keyboard.append(['🎯 Ввести другой город'])
        keyboard.append(['🔙 Назад'])
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @classmethod
    def normalize_city_name(cls, city_name: str) -> str:
        """
        Нормализует название города для API.
        
        Args:
            city_name: Название города от пользователя
            
        Returns:
            Нормализованное название для API
        """
        # Если город в списке популярных, используем нормализованное имя
        if city_name in cls.POPULAR_CITIES:
            return cls.POPULAR_CITIES[city_name]
        
        # Иначе возвращаем как есть (API само нормализует)
        return city_name
    
    @classmethod
    def is_city_popular(cls, city_name: str) -> bool:
        """Проверяет, есть ли город в списке популярных"""
        return city_name in cls.POPULAR_CITIES
        
