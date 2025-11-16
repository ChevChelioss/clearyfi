#!/usr/bin/env python3
"""
Анализатор погодных данных ClearyFi
Анализирует прогноз погоды и предоставляет рекомендации по мойке автомобиля
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# Настройка логирования
logger = logging.getLogger('WeatherAnalyzer')


@dataclass
class WeatherDay:
    """Класс для хранения структурированных данных о погоде за день"""
    date: str
    temperature_avg: float
    temperature_min: float
    temperature_max: float
    humidity_avg: float
    wind_speed_avg: float
    conditions: List[str]
    rain_probability: float
    wash_score: float = 0.0
    wash_recommendation: str = ""


class WeatherAnalyzer:
    """
    Анализатор погодных данных для определения оптимальных дней для мойки автомобиля.
    Использует улучшенные алгоритмы оценки погодных условий.
    """
    
    def __init__(self, weather_data: Dict[str, Any]):
        """
        Инициализация анализатора с данными о погоде.
        
        Args:
            weather_data: Словарь с данными о погоде от WeatherAPIClient
        """
        self.raw_data = weather_data
        self.daily_data: List[WeatherDay] = []
        self.current_weather: Dict[str, Any] = {}
        
        # Параметры для оценки условий мойки (можно настраивать)
        self.wash_thresholds = {
            'min_temperature': -2.0,      # Минимальная температура для мойки
            'max_humidity': 90.0,         # Максимальная влажность
            'max_wind_speed': 12.0,       # Максимальная скорость ветра
            'max_rain_probability': 0.0,  # Максимальная вероятность дождя
            'ideal_temperature_min': 10.0, # Идеальный диапазон температур
            'ideal_temperature_max': 25.0,
            'ideal_humidity_max': 75.0,   # Идеальная максимальная влажность
        }
        
        self._process_weather_data()
        logger.info(f"WeatherAnalyzer инициализирован с данными для {len(self.daily_data)} дней")

    def _process_weather_data(self) -> None:
        """
        Обрабатывает сырые данные погоды и преобразует их в структурированный формат.
        """
        try:
            # Обрабатываем ежедневные данные
            if 'daily_data' in self.raw_data:
                for day_data in self.raw_data['daily_data']:
                    weather_day = WeatherDay(
                        date=day_data.get('date', ''),
                        temperature_avg=day_data.get('temp_avg', 0),
                        temperature_min=day_data.get('temp_min', 0),
                        temperature_max=day_data.get('temp_max', 0),
                        humidity_avg=day_data.get('humidity_avg', 0),
                        wind_speed_avg=day_data.get('wind_avg', 0),
                        conditions=day_data.get('conditions', []),
                        rain_probability=day_data.get('rain_probability', 0)
                    )
                    
                    # Рассчитываем оценку для мойки
                    weather_day.wash_score = self._calculate_wash_score(weather_day)
                    weather_day.wash_recommendation = self._get_wash_recommendation_text(weather_day)
                    
                    self.daily_data.append(weather_day)
            
            # Обрабатываем текущую погоду
            self._process_current_weather()
            
            logger.debug(f"Обработано {len(self.daily_data)} дней погодных данных")
            
        except Exception as e:
            logger.error(f"Ошибка обработки погодных данных: {e}")

    def _process_current_weather(self) -> None:
        """
        Обрабатывает данные о текущей погоде.
        """
        try:
            # Если есть данные о текущей погоде, обрабатываем их
            if 'current_weather' in self.raw_data:
                self.current_weather = self.raw_data['current_weather']
            else:
                # Создаем текущую погоду на основе первого дня прогноза
                if self.daily_data:
                    today = self.daily_data[0]
                    self.current_weather = {
                        'temperature': today.temperature_avg,
                        'feels_like': today.temperature_avg,
                        'humidity': today.humidity_avg,
                        'pressure': 1013.25,  # Стандартное давление
                        'wind_speed': today.wind_speed_avg,
                        'weather': ', '.join(today.conditions),
                        'city': self.raw_data.get('city', 'Unknown'),
                        'timestamp': datetime.now().timestamp()
                    }
                    
        except Exception as e:
            logger.error(f"Ошибка обработки текущей погоды: {e}")

    def _calculate_wash_score(self, day: WeatherDay) -> float:
        """
        Рассчитывает оценку пригодности дня для мойки автомобиля (0-100).
        
        Args:
            day: Данные о погоде за день
            
        Returns:
            Оценка от 0 (плохо) до 100 (отлично)
        """
        try:
            score = 100.0  # Начинаем с идеального счета
            
            # 1. Штраф за вероятность дождя (самый важный фактор)
            rain_penalty = day.rain_probability * 2.0  # Усиленный штраф за дождь
            score -= min(rain_penalty, 100)  # Максимальный штраф 100
            
            if score <= 0:
                return 0.0
            
            # 2. Штраф за низкую температуру
            if day.temperature_avg < self.wash_thresholds['min_temperature']:
                score -= 80  # Сильный штраф за мороз
            elif day.temperature_avg < 0:
                score -= 60
            elif day.temperature_avg < 5:
                score -= 30
            elif day.temperature_avg < 10:
                score -= 15
            
            if score <= 0:
                return 0.0
            
            # 3. Штраф за высокую влажность
            if day.humidity_avg > self.wash_thresholds['max_humidity']:
                score -= 50
            elif day.humidity_avg > 85:
                score -= 25
            elif day.humidity_avg > 75:
                score -= 10
            
            if score <= 0:
                return 0.0
            
            # 4. Штраф за сильный ветер
            if day.wind_speed_avg > self.wash_thresholds['max_wind_speed']:
                score -= 40
            elif day.wind_speed_avg > 8:
                score -= 20
            elif day.wind_speed_avg > 5:
                score -= 5
            
            # 5. Бонус за идеальные условия
            ideal_conditions = (
                day.temperature_avg >= self.wash_thresholds['ideal_temperature_min'] and
                day.temperature_avg <= self.wash_thresholds['ideal_temperature_max'] and
                day.humidity_avg <= self.wash_thresholds['ideal_humidity_max'] and
                day.wind_speed_avg < 5 and
                day.rain_probability == 0
            )
            
            if ideal_conditions:
                score = min(score + 10, 100)  # Бонус за идеальные условия
            
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            logger.error(f"Ошибка расчета оценки мойки: {e}")
            return 0.0

    def _get_wash_recommendation_text(self, day: WeatherDay) -> str:
        """
        Генерирует текстовую рекомендацию для дня на основе оценки.
        
        Args:
            day: Данные о погоде за день
            
        Returns:
            Текстовая рекомендация
        """
        score = day.wash_score
        
        if score >= 90:
            return "Идеальный день для мойки"
        elif score >= 75:
            return "Отличный день для мойки"
        elif score >= 60:
            return "Хороший день для мойки"
        elif score >= 40:
            return "Условно подходит для мойки"
        elif score >= 20:
            return "Не рекомендуется для мойки"
        else:
            return "Не подходит для мойки"

    def get_daily_summary(self) -> List[Dict[str, Any]]:
        """
        Возвращает сводку погоды по дням в формате для построителя сообщений.
        
        Returns:
            Список словарей с ежедневной сводкой
        """
        summary = []
        
        for day in self.daily_data:
            day_summary = {
                'date': day.date,
                'temp': day.temperature_avg,
                'temp_min': day.temperature_min,
                'temp_max': day.temperature_max,
                'humidity': day.humidity_avg,
                'wind': day.wind_speed_avg,
                'conditions': day.conditions,
                'rain_prob': day.rain_probability,
                'wash_score': day.wash_score,
                'wash_recommendation': day.wash_recommendation
            }
            summary.append(day_summary)
        
        logger.debug(f"Сгенерирована сводка для {len(summary)} дней")
        return summary

    def get_best_wash_day(self) -> Optional[Dict[str, Any]]:
        """
        Находит лучший день для мойки автомобиля на основе оценок.
        
        Returns:
            Словарь с данными лучшего дня или None, если подходящих дней нет
        """
        try:
            if not self.daily_data:
                return None
            
            # Фильтруем дни с минимальным порогом оценки
            suitable_days = [
                day for day in self.daily_data 
                if day.wash_score >= 40  # Минимальный порог для рекомендации
            ]
            
            if not suitable_days:
                logger.info("Не найдено подходящих дней для мойки")
                return None
            
            # Выбираем день с наивысшей оценкой
            best_day = max(suitable_days, key=lambda x: x.wash_score)
            
            # Если лучшая оценка слишком низкая, не рекомендуем
            if best_day.wash_score < 50:
                logger.info(f"Лучший день имеет низкую оценку: {best_day.wash_score}")
                return None
            
            best_day_data = {
                'date': best_day.date,
                'temp': best_day.temperature_avg,
                'humidity': best_day.humidity_avg,
                'wind': best_day.wind_speed_avg,
                'conditions': best_day.conditions,
                'rain_prob': best_day.rain_probability,
                'wash_score': best_day.wash_score,
                'recommendation': best_day.wash_recommendation
            }
            
            logger.info(f"Найден лучший день для мойки: {best_day.date} (оценка: {best_day.wash_score})")
            return best_day_data
            
        except Exception as e:
            logger.error(f"Ошибка поиска лучшего дня для мойки: {e}")
            return None

    def get_current_weather(self) -> Dict[str, Any]:
        """
        Возвращает данные о текущей погоде.
        
        Returns:
            Словарь с данными текущей погоды
        """
        return self.current_weather

    def get_weather_alerts(self) -> List[str]:
        """
        Анализирует погодные данные и возвращает предупреждения.
        
        Returns:
            Список строк с предупреждениями
        """
        alerts = []
        
        try:
            # Проверяем текущую погоду и ближайшие дни
            for i, day in enumerate(self.daily_data[:2]):  # Сегодня и завтра
                day_label = "Сегодня" if i == 0 else "Завтра"
                
                # Предупреждение о дожде
                if day.rain_probability > 50:
                    alerts.append(f"⚠️ {day_label} ожидается сильный дождь ({day.rain_probability}%)")
                elif day.rain_probability > 20:
                    alerts.append(f"🌧️ {day_label} возможен дождь ({day.rain_probability}%)")
                
                # Предупреждение о низкой температуре
                if day.temperature_min < -5:
                    alerts.append(f"🧊 {day_label} сильный мороз до {day.temperature_min:.0f}°C")
                elif day.temperature_min < 0:
                    alerts.append(f"❄️ {day_label} возможны заморозки до {day.temperature_min:.0f}°C")
                
                # Предупреждение о сильном ветре
                if day.wind_speed_avg > 15:
                    alerts.append(f"💨 {day_label} очень сильный ветер {day.wind_speed_avg:.1f} м/с")
                elif day.wind_speed_avg > 10:
                    alerts.append(f"💨 {day_label} сильный ветер {day.wind_speed_avg:.1f} м/с")
                
                # Предупреждение о высокой влажности
                if day.humidity_avg > 90:
                    alerts.append(f"💧 {day_label} очень высокая влажность {day.humidity_avg:.0f}%")
            
            # Уникальные предупреждения
            alerts = list(set(alerts))
            logger.debug(f"Сгенерировано {len(alerts)} предупреждений")
            
        except Exception as e:
            logger.error(f"Ошибка генерации предупреждений: {e}")
        
        return alerts

    def get_today_forecast(self) -> Dict[str, Any]:
        """
        Возвращает детальный прогноз на сегодня.
        
        Returns:
            Словарь с прогнозом на сегодня
        """
        if not self.daily_data:
            return {}
        
        today = self.daily_data[0]
        return {
            'date': today.date,
            'temperature': today.temperature_avg,
            'temperature_range': f"{today.temperature_min:.0f}...{today.temperature_max:.0f}°C",
            'humidity': today.humidity_avg,
            'wind_speed': today.wind_speed_avg,
            'conditions': today.conditions,
            'rain_probability': today.rain_probability,
            'wash_recommendation': today.wash_recommendation
        }

    def get_wash_analysis(self) -> Dict[str, Any]:
        """
        Возвращает детальный анализ условий для мойки.
        
        Returns:
            Словарь с анализом условий мойки
        """
        analysis = {
            'best_day': self.get_best_wash_day(),
            'daily_scores': [],
            'overall_conditions': 'unknown',
            'recommendation_period': None
        }
        
        # Анализируем оценки по дням
        scores = [day.wash_score for day in self.daily_data]
        
        if scores:
            analysis['average_score'] = sum(scores) / len(scores)
            analysis['max_score'] = max(scores)
            analysis['min_score'] = min(scores)
            
            # Определяем общие условия
            if analysis['max_score'] >= 80:
                analysis['overall_conditions'] = 'excellent'
            elif analysis['max_score'] >= 60:
                analysis['overall_conditions'] = 'good'
            elif analysis['max_score'] >= 40:
                analysis['overall_conditions'] = 'fair'
            else:
                analysis['overall_conditions'] = 'poor'
            
            # Рекомендуемый период для мойки
            good_days = [day for day in self.daily_data if day.wash_score >= 60]
            if len(good_days) >= 2:
                analysis['recommendation_period'] = 'extended'
            elif good_days:
                analysis['recommendation_period'] = 'single'
            else:
                analysis['recommendation_period'] = 'none'
        
        # Детальные оценки по дням
        for day in self.daily_data:
            day_analysis = {
                'date': day.date,
                'wash_score': day.wash_score,
                'recommendation': day.wash_recommendation,
                'factors': self._analyze_wash_factors(day)
            }
            analysis['daily_scores'].append(day_analysis)
        
        return analysis

    def _analyze_wash_factors(self, day: WeatherDay) -> List[str]:
        """
        Анализирует факторы, влияющие на оценку мойки для дня.
        
        Args:
            day: Данные о погоде за день
            
        Returns:
            Список факторов с описанием
        """
        factors = []
        
        # Анализ температуры
        if day.temperature_avg >= self.wash_thresholds['ideal_temperature_min']:
            factors.append("✅ Идеальная температура")
        elif day.temperature_avg >= 5:
            factors.append("⚠️ Прохладно, но можно мыть")
        else:
            factors.append("❌ Слишком холодно для мойки")
        
        # Анализ влажности
        if day.humidity_avg <= self.wash_thresholds['ideal_humidity_max']:
            factors.append("✅ Нормальная влажность")
        elif day.humidity_avg <= 85:
            factors.append("⚠️ Повышенная влажность")
        else:
            factors.append("❌ Высокая влажность")
        
        # Анализ ветра
        if day.wind_speed_avg < 5:
            factors.append("✅ Слабый ветер")
        elif day.wind_speed_avg < 10:
            factors.append("⚠️ Умеренный ветер")
        else:
            factors.append("❌ Сильный ветер")
        
        # Анализ осадков
        if day.rain_probability == 0:
            factors.append("✅ Без осадков")
        else:
            factors.append(f"❌ Вероятность дождя {day.rain_probability}%")
        
        return factors

    def update_thresholds(self, new_thresholds: Dict[str, float]) -> None:
        """
        Обновляет пороговые значения для оценки условий мойки.
        
        Args:
            new_thresholds: Словарь с новыми пороговыми значениями
        """
        self.wash_thresholds.update(new_thresholds)
        logger.info("Обновлены пороговые значения анализатора")
        
        # Пересчитываем оценки для всех дней
        for day in self.daily_data:
            day.wash_score = self._calculate_wash_score(day)
            day.wash_recommendation = self._get_wash_recommendation_text(day)


# Утилитарные функции для обратной совместимости
def create_weather_analyzer(weather_data: Dict) -> WeatherAnalyzer:
    """
    Создает экземпляр WeatherAnalyzer с данными о погоде.
    
    Args:
        weather_data: Данные о погоде от WeatherAPIClient
        
    Returns:
        Экземпляр WeatherAnalyzer
    """
    return WeatherAnalyzer(weather_data)


if __name__ == "__main__":
    # Пример использования
    print("Это модуль WeatherAnalyzer. Запустите main.py для запуска приложения.")
