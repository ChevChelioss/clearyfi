#!/usr/bin/env python3
"""
Сервис управления подпиской и уведомлениями
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, time
import sqlite3

from core.logger import logger
from utils.date_utils import get_current_timestamp, is_time_for_notification
from services.weather.openweather import OpenWeatherService
from services.recommendations.wash import WashRecommendationService
from services.recommendations.tires import TireRecommendationService
from services.recommendations.roads import RoadConditionService


class SubscriptionService:
    """Сервис для управления подпиской и уведомлениями пользователей"""
    
    def __init__(self, database, weather_service: OpenWeatherService, 
                 wash_service: WashRecommendationService,
                 tires_service: TireRecommendationService,
                 roads_service: RoadConditionService,
                 locale_manager):
        self.database = database
        self.weather_service = weather_service
        self.wash_service = wash_service
        self.tires_service = tires_service
        self.roads_service = roads_service
        self.locale = locale_manager
        
        logger.info("✅ SubscriptionService инициализирован")
    
    def subscribe_user(self, user_id: int, notification_time: str = "09:00") -> Dict[str, Any]:
        """
        Подписывает пользователя на ежедневные уведомления
        
        Args:
            user_id: ID пользователя Telegram
            notification_time: Время уведомления в формате HH:MM
            
        Returns:
            Результат операции
        """
        try:
            success = self.database.update_user_subscription(
                user_id=user_id,
                notifications_enabled=True,
                notification_time=notification_time
            )
            
            if success:
                logger.info(f"✅ Пользователь {user_id} подписан на уведомления")
                return {
                    'success': True,
                    'message': self.locale.get_message('subscription_activated'),
                    'notification_time': notification_time
                }
            else:
                return {
                    'success': False,
                    'message': self.locale.get_message('subscription_error')
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка подписки пользователя {user_id}: {e}")
            return {
                'success': False,
                'message': self.locale.get_message('service_unavailable')
            }
    
    def unsubscribe_user(self, user_id: int) -> Dict[str, Any]:
        """
        Отписывает пользователя от уведомлений
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            Результат операции
        """
        try:
            success = self.database.update_user_subscription(
                user_id=user_id,
                notifications_enabled=False
            )
            
            if success:
                logger.info(f"✅ Пользователь {user_id} отписан от уведомлений")
                return {
                    'success': True,
                    'message': self.locale.get_message('subscription_deactivated')
                }
            else:
                return {
                    'success': False,
                    'message': self.locale.get_message('subscription_error')
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка отписки пользователя {user_id}: {e}")
            return {
                'success': False,
                'message': self.locale.get_message('service_unavailable')
            }
    
    def get_user_subscription_status(self, user_id: int) -> Dict[str, Any]:
        """
        Возвращает статус подписки пользователя
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            Статус подписки
        """
        try:
            user_data = self.database.get_user_by_id(user_id)
            
            if not user_data:
                return {
                    'success': False,
                    'subscribed': False,
                    'message': self.locale.get_message('user_not_found')
                }
            
            subscribed = bool(user_data.get('notifications_enabled', False))
            notification_time = user_data.get('notification_time', '09:00')
            city = user_data.get('city', 'Не установлен')
            
            return {
                'success': True,
                'subscribed': subscribed,
                'notification_time': notification_time,
                'city': city,
                'user_data': user_data
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса подписки {user_id}: {e}")
            return {
                'success': False,
                'subscribed': False,
                'message': self.locale.get_message('service_unavailable')
            }
    
    def update_notification_time(self, user_id: int, new_time: str) -> Dict[str, Any]:
        """
        Обновляет время уведомлений для пользователя
        
        Args:
            user_id: ID пользователя Telegram
            new_time: Новое время в формате HH:MM
            
        Returns:
            Результат операции
        """
        try:
            # Проверяем формат времени
            datetime.strptime(new_time, '%H:%M')
            
            success = self.database.update_user_subscription(
                user_id=user_id,
                notification_time=new_time
            )
            
            if success:
                logger.info(f"✅ Время уведомлений пользователя {user_id} обновлено на {new_time}")
                return {
                    'success': True,
                    'message': self.locale.get_message('notification_time_updated'),
                    'notification_time': new_time
                }
            else:
                return {
                    'success': False,
                    'message': self.locale.get_message('subscription_error')
                }
                
        except ValueError:
            return {
                'success': False,
                'message': self.locale.get_message('invalid_time_format')
            }
        except Exception as e:
            logger.error(f"❌ Ошибка обновления времени уведомлений {user_id}: {e}")
            return {
                'success': False,
                'message': self.locale.get_message('service_unavailable')
            }
    
    def get_users_for_notification(self) -> List[Dict[str, Any]]:
        """
        Возвращает список пользователей, которым нужно отправить уведомления
        
        Returns:
            Список пользователей для уведомления
        """
        try:
            current_time = datetime.now().strftime('%H:%M')
            users = self.database.get_users_with_notifications()
            
            users_to_notify = []
            for user in users:
                if user.get('notifications_enabled') and user.get('city'):
                    if is_time_for_notification(user.get('notification_time', '09:00')):
                        users_to_notify.append(user)
            
            logger.info(f"📨 Найдено пользователей для уведомления: {len(users_to_notify)}")
            return users_to_notify
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения пользователей для уведомления: {e}")
            return []
    
    def generate_daily_notification(self, user_data: Dict[str, Any]) -> str:
        """
        Генерирует ежедневное уведомление для пользователя
        
        Args:
            user_data: Данные пользователя
            
        Returns:
            Текст уведомления
        """
        try:
            user_id = user_data['user_id']
            city = user_data['city']
            
            # Получаем рекомендации от всех сервисов
            wash_result = self.wash_service.get_recommendation(city)
            tires_result = self.tires_service.get_recommendation(city)
            roads_result = self.roads_service.get_recommendation(city)
            
            # Формируем общее уведомление
            notification_parts = []
            
            if wash_result['success']:
                wash_text = wash_result['recommendation'].split('\n\n')[0]  # Берем первую часть
                notification_parts.append(f"🧼 {wash_text}")
            
            if tires_result['success']:
                tires_text = tires_result['recommendation'].split('\n\n')[0]
                notification_parts.append(f"🛞 {tires_text}")
            
            if roads_result['success']:
                roads_text = roads_result['recommendation'].split('\n\n')[0]
                notification_parts.append(f"🛣 {roads_text}")
            
            if notification_parts:
                notification = "📅 *Ежедневный авто-дайджест*\n\n" + "\n\n".join(notification_parts)
                notification += f"\n\n_Обновлено: {get_current_timestamp()}_"
                return notification
            else:
                return self.locale.get_message('daily_notification_fallback')
                
        except Exception as e:
            logger.error(f"❌ Ошибка генерации уведомления для {user_id}: {e}")
            return self.locale.get_message('notification_generation_error')
