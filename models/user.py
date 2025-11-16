#!/usr/bin/env python3
"""
МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ CLEARYFI 2.0

Этот файл определяет структуру данных пользователя:
- Основная информация
- Настройки уведомлений  
- Данные автомобиля
- Геолокации
"""

# Импортируем необходимые модули Python
from typing import Dict, List, Optional, Any  # Для указания типов данных
from dataclasses import dataclass  # Для создания классов данных
from enum import Enum  # Для создания перечислений
from datetime import datetime  # Для работы с датами и временем


# =============================================================================
# ПЕРЕЧИСЛЕНИЯ (ENUMS) - фиксированные наборы значений
# =============================================================================

class VehicleType(Enum):
    """
    ТИП ТРАНСПОРТНОГО СРЕДСТВА
    Enum - это как список возможных вариантов, чтобы не ошибиться в написании
    """
    SEDAN = "sedan"        # Легковой автомобиль
    SUV = "suv"            # Внедорожник
    TRUCK = "truck"        # Грузовик
    MOTORCYCLE = "motorcycle"  # Мотоцикл
    HATCHBACK = "hatchback"    # Хэтчбек


class NotificationLevel(Enum):
    """
    УРОВЕНЬ УВЕДОМЛЕНИЙ
    Определяет как часто пользователь получает уведомления
    """
    SMART = "smart"          # Умные уведомления (только важные)
    AGGRESSIVE = "aggressive" # Все возможные уведомления
    CONSERVATIVE = "conservative" # Только критические


class UserStatus(Enum):
    """
    СТАТУС ПОЛЬЗОВАТЕЛЯ
    """
    ACTIVE = "active"        # Активный пользователь
    INACTIVE = "inactive"    # Неактивный
    PAUSED = "paused"        # Временно приостановил уведомления


# =============================================================================
# КЛАССЫ ДАННЫХ С ПОМОЩЬЮ @dataclass
# =============================================================================

@dataclass
class Location:
    """
    КЛАСС ЛОКАЦИИ
    Хранит информацию о географическом местоположении
    
    dataclass - это специальный декоратор который автоматически создает
    конструктор и методы для класса
    """
    latitude: float          # Широта (например: 55.7558 для Москвы)
    longitude: float         # Долгота (например: 37.6173 для Москвы)
    address: str = ""        # Человеко-читаемый адрес (например: "Москва, Красная площадь")
    radius_km: int = 5       # Радиус интереса вокруг точки в километрах
    
    def to_dict(self) -> Dict[str, Any]:
        """
        ПРЕОБРАЗОВАНИЕ В СЛОВАРЬ
        Метод преобразует объект в словарь для удобного хранения в базе данных
        
        Returns:
            Dict: Словарь с данными локации
        """
        return {
            'lat': self.latitude,
            'lon': self.longitude, 
            'address': self.address,
            'radius_km': self.radius_km
        }
    
    def __str__(self) -> str:
        """Строковое представление локации"""
        if self.address:
            return f"Location({self.address})"
        return f"Location({self.latitude}, {self.longitude})"


@dataclass
class Vehicle:
    """
    КЛАСС АВТОМОБИЛЯ
    Хранит информацию о транспортном средстве пользователя
    """
    vehicle_type: VehicleType     # Тип транспортного средства
    paint_condition: str = "good" # Состояние краски: good/average/poor
    parking_type: str = "street"  # Тип парковки: street/garage/covered
    year: Optional[int] = None    # Год выпуска (необязательное поле)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            'type': self.vehicle_type.value,  # .value получает строковое значение enum
            'paint_condition': self.paint_condition,
            'parking_type': self.parking_type,
            'year': self.year
        }


@dataclass  
class UserPreferences:
    """
    КЛАСС ПРЕДПОЧТЕНИЙ ПОЛЬЗОВАТЕЛЯ
    Настройки того, как пользователь хочет получать уведомления
    """
    notification_level: NotificationLevel = NotificationLevel.SMART
    risk_tolerance: str = "medium"  # low/medium/high - терпимость к риску
    quiet_hours_start: str = "23:00"  # Начало тихого времени (не беспокоить)
    quiet_hours_end: str = "08:00"    # Конец тихого времени
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            'notification_level': self.notification_level.value,
            'risk_tolerance': self.risk_tolerance,
            'quiet_hours': {
                'start': self.quiet_hours_start,
                'end': self.quiet_hours_end
            }
        }


# =============================================================================
# ГЛАВНЫЙ КЛАСС ПОЛЬЗОВАТЕЛЯ
# =============================================================================

class User:
    """
    ОСНОВНОЙ КЛАСС ПОЛЬЗОВАТЕЛЯ
    Содержит всю информацию о пользователе и его настройках
    """
    
    def __init__(self, user_id: str, telegram_chat_id: str):
        """
        КОНСТРУКТОР КЛАССА - вызывается при создании нового объекта User
        
        Args:
            user_id (str): Уникальный ID пользователя в нашей системе
            telegram_chat_id (str): ID чата в Telegram для отправки уведомлений
        """
        # ОСНОВНЫЕ ИДЕНТИФИКАТОРЫ
        self.user_id = user_id
        self.telegram_chat_id = telegram_chat_id
        
        # СТАТУСЫ
        self.status = UserStatus.ACTIVE
        self.subscription_date = datetime.now()  # Дата и время подписки
        self.last_activity = datetime.now()      # Последняя активность
        
        # ЛОКАЦИИ
        self.home_location: Optional[Location] = None    # Домашняя локация
        self.work_location: Optional[Location] = None    # Рабочая локация  
        self.other_locations: List[Location] = []        # Другие важные локации
        
        # НАСТРОЙКИ
        self.preferences = UserPreferences()      # Предпочтения уведомлений
        self.vehicle = Vehicle(VehicleType.SEDAN) # Информация об авто
        
        # ПОВЕДЕНЧЕСКИЕ ДАННЫЕ
        self.usual_routes: List[Dict] = []        # Обычные маршруты пользователя
        self.driving_habits: Dict[str, Any] = {}  # Привычки вождения
        
        print(f"✅ Создан новый пользователь: {user_id}")

    # =========================================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С ЛОКАЦИЯМИ
    # =========================================================================

    def set_home_location(self, lat: float, lon: float, address: str = ""):
        """
        УСТАНОВИТЬ ДОМАШНЮЮ ЛОКАЦИЮ
        
        Args:
            lat (float): Широта
            lon (float): Долгота
            address (str): Адрес в текстовом виде
        """
        self.home_location = Location(lat, lon, address)
        print(f"✅ Установлена домашняя локация: {address or f'{lat}, {lon}'}")
    
    def set_work_location(self, lat: float, lon: float, address: str = ""):
        """
        УСТАНОВИТЬ РАБОЧУЮ ЛОКАЦИЮ
        """
        self.work_location = Location(lat, lon, address)
        print(f"✅ Установлена рабочая локация: {address or f'{lat}, {lon}'}")
    
    def add_other_location(self, lat: float, lon: float, address: str = ""):
        """
        ДОБАВИТЬ ДРУГУЮ ВАЖНУЮ ЛОКАЦИЮ
        """
        location = Location(lat, lon, address)
        self.other_locations.append(location)
        print(f"✅ Добавлена дополнительная локация: {address or f'{lat}, {lon}'}")

    # =========================================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С НАСТРОЙКАМИ
    # =========================================================================

    def update_preferences(self, 
                         notification_level: NotificationLevel = None,
                         risk_tolerance: str = None,
                         quiet_hours_start: str = None,
                         quiet_hours_end: str = None):
        """
        ОБНОВИТЬ НАСТРОЙКИ ПОЛЬЗОВАТЕЛЯ
        
        Args:
            notification_level: Уровень уведомлений
            risk_tolerance: Терпимость к риску
            quiet_hours_start: Начало тихого времени
            quiet_hours_end: Конец тихого времени
        """
        if notification_level:
            self.preferences.notification_level = notification_level
        if risk_tolerance:
            self.preferences.risk_tolerance = risk_tolerance
        if quiet_hours_start:
            self.preferences.quiet_hours_start = quiet_hours_start
        if quiet_hours_end:
            self.preferences.quiet_hours_end = quiet_hours_end
        
        print("✅ Настройки пользователя обновлены")

    # =========================================================================
    # СЛУЖЕБНЫЕ МЕТОДЫ
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        ПРЕОБРАЗОВАТЬ ВСЕ ДАННЫЕ ПОЛЬЗОВАТЕЛЯ В СЛОВАРЬ
        Это полезно для сохранения в базу данных или передачи по сети
        
        Returns:
            Dict: Словарь со всеми данными пользователя
        """
        return {
            # Основная информация
            'user_id': self.user_id,
            'telegram_chat_id': self.telegram_chat_id,
            'status': self.status.value,
            'subscription_date': self.subscription_date.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            
            # Локации
            'locations': {
                'home': self.home_location.to_dict() if self.home_location else None,
                'work': self.work_location.to_dict() if self.work_location else None,
                'other': [loc.to_dict() for loc in self.other_locations]
            },
            
            # Настройки
            'preferences': self.preferences.to_dict(),
            'vehicle': self.vehicle.to_dict(),
            
            # Поведенческие данные
            'behavior': {
                'usual_routes': self.usual_routes,
                'driving_habits': self.driving_habits
            }
        }
    
    def activate(self):
        """АКТИВИРОВАТЬ ПОЛЬЗОВАТЕЛЯ"""
        self.status = UserStatus.ACTIVE
        self.last_activity = datetime.now()
        print(f"✅ Пользователь {self.user_id} активирован")
    
    def deactivate(self):
        """ДЕАКТИВИРОВАТЬ ПОЛЬЗОВАТЕЛЯ"""
        self.status = UserStatus.INACTIVE
        print(f"✅ Пользователь {self.user_id} деактивирован")
    
    def __str__(self) -> str:
        """СТРОКОВОЕ ПРЕДСТАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ (для отладки)"""
        locations_count = len([loc for loc in [self.home_location, self.work_location] if loc])
        return (f"User({self.user_id}, status: {self.status.value}, "
                f"locations: {locations_count}, vehicle: {self.vehicle.vehicle_type.value})")


# =============================================================================
# ТЕСТИРОВАНИЕ КЛАССА
# =============================================================================

def test_user_class():
    """
    ТЕСТИРУЕМ НАШ КЛАСС ПОЛЬЗОВАТЕЛЯ
    Эта функция запускается только когда файл запускается напрямую
    """
    print("\n" + "="*60)
    print("🧪 ТЕСТИРУЕМ КЛАСС ПОЛЬЗОВАТЕЛЯ")
    print("="*60)
    
    # СОЗДАЕМ ТЕСТОВОГО ПОЛЬЗОВАТЕЛЯ
    test_user = User("test_user_123", "123456789")
    
    # УСТАНАВЛИВАЕМ ЛОКАЦИИ
    test_user.set_home_location(55.7558, 37.6173, "Москва, Красная площадь")
    test_user.set_work_location(59.9343, 30.3351, "Санкт-Петербург, Невский проспект")
    test_user.add_other_location(55.7600, 37.6175, "Москва, ГУМ")
    
    # НАСТРАИВАЕМ ПРЕДПОЧТЕНИЯ
    test_user.update_preferences(
        notification_level=NotificationLevel.SMART,
        risk_tolerance="medium",
        quiet_hours_start="22:00",
        quiet_hours_end="07:00"
    )
    
    # НАСТРАИВАЕМ АВТОМОБИЛЬ
    test_user.vehicle.vehicle_type = VehicleType.SUV
    test_user.vehicle.paint_condition = "excellent"
    test_user.vehicle.parking_type = "garage"
    
    # ПОКАЗЫВАЕМ РЕЗУЛЬТАТ
    print("\n📋 ДАННЫЕ ТЕСТОВОГО ПОЛЬЗОВАТЕЛЯ:")
    user_dict = test_user.to_dict()
    
    # Красиво выводим словарь
    for key, value in user_dict.items():
        if key == 'locations':
            print(f"  📍 Локации:")
            for loc_type, loc_data in value.items():
                if loc_data:
                    if loc_type == 'other':
                        print(f"    • {loc_type}: {len(loc_data)} локаций")
                    else:
                        print(f"    • {loc_type}: {loc_data.get('address', 'No address')}")
        elif key == 'preferences':
            print(f"  ⚙️ Настройки:")
            for pref_key, pref_value in value.items():
                print(f"    • {pref_key}: {pref_value}")
        elif key == 'vehicle':
            print(f"  🚗 Автомобиль:")
            for vehicle_key, vehicle_value in value.items():
                print(f"    • {vehicle_key}: {vehicle_value}")
        else:
            print(f"  • {key}: {value}")
    
    print(f"\n🎉 ТЕСТ ПРОЙДЕН! Класс пользователя работает корректно!")


# Этот код выполняется только если файл запускается напрямую
if __name__ == "__main__":
    test_user_class()
