#!/usr/bin/env python3
"""
Демон уведомлений ClearyFi
Отвечает за отправку регулярных уведомлений о погоде и рекомендаций по мойке автомобиля
"""

import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from services.weather.weather_service import WeatherService
from services.notifications.message_builder import NotificationMessageBuilder
from utils.date_utils import format_date_russian

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clearyfi_notifications.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('NotificationDaemon')


class NotificationDaemon:
    """
    Демон для управления уведомлениями пользователей.
    Отправляет регулярные прогнозы и рекомендации по мойке автомобиля.
    """
    
    def __init__(self, telegram_bot, db_path: str = 'clearyfi.db', weather_api_key: str = None):
        """
        Инициализация демона уведомлений.
        
        Args:
            telegram_bot: Экземпляр Telegram бота для отправки сообщений
            db_path: Путь к базе данных SQLite
            weather_api_key: API ключ для сервиса погоды
        """
        self.bot = telegram_bot
        self.db_path = db_path
        self.weather_service = WeatherService(weather_api_key)
        
        # Статистика работы демона
        self.stats = {
            'notifications_sent': 0,
            'errors': 0,
            'last_run': None
        }
        
        logger.info("NotificationDaemon инициализирован")

    def _get_subscribed_users(self) -> List[Dict]:
        """
        Получает список пользователей, подписанных на уведомления.
        
        Returns:
            Список словарей с данными пользователей
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, city, notification_time, timezone 
                FROM users 
                WHERE notifications_enabled = 1
            ''')
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'user_id': row[0],
                    'city': row[1],
                    'notification_time': row[2],
                    'timezone': row[3]
                })
            
            conn.close()
            logger.info(f"Найдено {len(users)} подписанных пользователей")
            return users
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка базы данных при получении пользователей: {e}")
            return []

    def _should_send_notification(self, user: Dict) -> bool:
        """
        Проверяет, нужно ли отправлять уведомление пользователю в текущий момент.
        
        Args:
            user: Данные пользователя
            
        Returns:
            True если уведомление нужно отправить, иначе False
        """
        try:
            # Получаем текущее время с учетом часового пояса пользователя
            if user.get('timezone'):
                # Простая реализация - в продакшене используйте pytz
                from datetime import timezone
                user_time = datetime.now(timezone.utc).astimezone(
                    timezone(timedelta(hours=user['timezone']))
                )
            else:
                user_time = datetime.now()
            
            # Преобразуем время уведомления пользователя в объект time
            notification_time = datetime.strptime(
                user['notification_time'], '%H:%M'
            ).time()
            
            # Проверяем, совпадает ли текущее время с временем уведомления
            current_time = user_time.time()
            
            # Допускаем отклонение +/- 5 минут для гибкости
            time_diff = abs(
                (current_time.hour * 60 + current_time.minute) - 
                (notification_time.hour * 60 + notification_time.minute)
            )
            
            should_send = time_diff <= 5
            if should_send:
                logger.info(f"Уведомление для пользователя {user['user_id']} должно быть отправлено")
            
            return should_send
            
        except Exception as e:
            logger.error(f"Ошибка проверки времени уведомления: {e}")
            return False

    async def _send_weather_notification(self, user: Dict) -> bool:
        """
        Отправляет уведомление о погоде конкретному пользователю.
        
        Args:
            user: Данные пользователя
            
        Returns:
            True если уведомление отправлено успешно, иначе False
        """
        try:
            user_id = user['user_id']
            city = user['city']
            
            logger.info(f"Подготовка уведомления для {user_id} в городе {city}")
            
            # Получаем данные о погоде
            weather_data = self.weather_service.get_city_forecast(city, days=3)
            
            if not weather_data:
                error_msg = f"Не удалось получить данные о погоде для {city}"
                logger.error(error_msg)
                await self.bot.send_message(
                    user_id, 
                    f"❌ {error_msg}. Проверьте название города."
                )
                return False
            
            # Формируем сообщение
            message = NotificationMessageBuilder.build_weather_notification(
                city=city,
                daily_summary=weather_data['daily_summary'],
                best_day=weather_data.get('best_wash_day')
            )
            
            # Отправляем сообщение
            await self.bot.send_message(user_id, message, parse_mode='Markdown')
            
            # Обновляем статистику
            self.stats['notifications_sent'] += 1
            logger.info(f"Уведомление отправлено пользователю {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления пользователю {user['user_id']}: {e}")
            self.stats['errors'] += 1
            return False

    async def _send_immediate_forecast(self, user_id: int, city: str) -> bool:
        """
        Отправляет немедленный прогноз погоды по запросу пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            city: Город для прогноза
            
        Returns:
            True если сообщение отправлено, иначе False
        """
        try:
            logger.info(f"Подготовка немедленного прогноза для {user_id} в {city}")
            
            # Получаем текущую погоду
            weather_data = self.weather_service.get_immediate_forecast(city)
            
            if not weather_data:
                await self.bot.send_message(
                    user_id, 
                    f"❌ Не удалось получить данные о погоде в {city}"
                )
                return False
            
            # Формируем и отправляем сообщение
            message = NotificationMessageBuilder.build_current_weather_message(
                city=city,
                current_weather=weather_data.get('current_weather', {})
            )
            
            await self.bot.send_message(user_id, message, parse_mode='Markdown')
            logger.info(f"Немедленный прогноз отправлен пользователю {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки немедленного прогноза: {e}")
            return False

    async def process_scheduled_notifications(self):
        """
        Обрабатывает запланированные уведомления для всех пользователей.
        """
        logger.info("Запуск обработки запланированных уведомлений")
        
        try:
            # Получаем всех подписанных пользователей
            users = self._get_subscribed_users()
            
            if not users:
                logger.info("Нет подписанных пользователей для уведомлений")
                return
            
            # Отправляем уведомления нужным пользователям
            tasks = []
            for user in users:
                if self._should_send_notification(user):
                    task = self._send_weather_notification(user)
                    tasks.append(task)
            
            # Выполняем все задачи асинхронно
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                successful = sum(1 for r in results if r is True)
                logger.info(f"Успешно отправлено {successful} из {len(tasks)} уведомлений")
            else:
                logger.info("Нет уведомлений для отправки в этот момент")
            
            # Обновляем время последнего запуска
            self.stats['last_run'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Критическая ошибка в процессе уведомлений: {e}")
            self.stats['errors'] += 1

    async def send_test_notification(self, user_id: int, city: str):
        """
        Отправляет тестовое уведомление пользователю.
        
        Args:
            user_id: ID пользователя Telegram
            city: Город для тестового уведомления
        """
        try:
            logger.info(f"Отправка тестового уведомления для {user_id} в {city}")
            
            # Создаем временного пользователя для теста
            test_user = {
                'user_id': user_id,
                'city': city
            }
            
            success = await self._send_weather_notification(test_user)
            
            if success:
                await self.bot.send_message(
                    user_id, 
                    "✅ Тестовое уведомление отправлено успешно!"
                )
            else:
                await self.bot.send_message(
                    user_id, 
                    "❌ Не удалось отправить тестовое уведомление. Проверьте логи."
                )
                
        except Exception as e:
            logger.error(f"Ошибка тестового уведомления: {e}")
            await self.bot.send_message(
                user_id, 
                f"❌ Ошибка тестового уведомления: {str(e)}"
            )

    def get_daemon_stats(self) -> Dict:
        """
        Возвращает статистику работы демона.
        
        Returns:
            Словарь со статистикой
        """
        return {
            **self.stats,
            'active_users': len(self._get_subscribed_users()),
            'weather_service_available': self.weather_service is not None
        }


async def run_notification_daemon(bot, db_path: str, weather_api_key: str):
    """
    Запускает демон уведомлений в бесконечном цикле.
    
    Args:
        bot: Экземпляр Telegram бота
        db_path: Путь к базе данных
        weather_api_key: API ключ погодного сервиса
    """
    daemon = NotificationDaemon(bot, db_path, weather_api_key)
    
    logger.info("Демон уведомлений запущен")
    
    while True:
        try:
            # Обрабатываем запланированные уведомления
            await daemon.process_scheduled_notifications()
            
            # Ждем 1 минуту перед следующей проверкой
            await asyncio.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("Демон уведомлений остановлен по запросу пользователя")
            break
        except Exception as e:
            logger.error(f"Неожиданная ошибка в демоне: {e}")
            await asyncio.sleep(60)  # Ждем перед повторной попыткой


if __name__ == "__main__":
    # Тестовый запуск демона
    print("Это модуль демона уведомлений. Запустите main.py для запуска приложения.")
