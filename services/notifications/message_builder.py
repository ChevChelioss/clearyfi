# services/notifications/message_builder.py
from typing import Dict, List, Tuple, Optional
from utils.date_utils import format_date_russian, get_relative_day_label
from utils.text_utils import translate_weather_conditions, format_temperature, format_wind_speed

class NotificationMessageBuilder:
    """
    Строитель сообщений для уведомлений.
    Отвечает за формирование красивых и информативных сообщений.
    """
    
    @staticmethod
    def build_weather_notification(city: str, daily_summary: List[Dict], 
                                 best_day: Optional[Dict] = None) -> str:
        """
        Строит основное уведомление о погоде с рекомендациями по мойке.
        
        Args:
            city: Название города
            daily_summary: Сводка по дням
            best_day: Лучший день для мойки (опционально)
            
        Returns:
            Готовое сообщение в формате Markdown
        """
        message_lines = [
            "🚗 *ClearyFi - Ваш персональный автоассистент*",
            "",
            f"📍 *Город:* {city}",
            ""
        ]
        
        # Главная рекомендация
        if best_day:
            formatted_date = format_date_russian(best_day['date'])
            message_lines.extend([
                "✅ *РЕКОМЕНДУЕМ ПОМЫТЬ АВТО:*",
                f"📅 *Когда:* {formatted_date}",
                f"🌡 *Температура:* {format_temperature(best_day['temp'])}",
                f"💧 *Влажность:* {best_day['humidity']:.0f}%",
                f"💨 *Ветер:* {format_wind_speed(best_day['wind'])}",
                f"☁️ *Погода:* {translate_weather_conditions(best_day['conditions'])}",
                ""
            ])
        else:
            message_lines.extend([
                "⚠️ *Внимание:* Идеальных дней для мойки не найдено",
                ""
            ])
        
        # Детальный прогноз на 3 дня
        message_lines.append("📊 *Прогноз на 3 дня:*")
        message_lines.append("")
        
        for i, day in enumerate(daily_summary[:3]):
            day_label = get_relative_day_label(day['date'])
            wash_status, wash_description = NotificationMessageBuilder._get_wash_recommendation(day)
            
            message_lines.extend([
                f"{wash_status} *{day_label}*",
                f"   {wash_description}",
                f"   🌡 {format_temperature(day['temp'])} | 💧 {day['humidity']:.0f}% | 💨 {format_wind_speed(day['wind'])}",
                f"   ☁️ {translate_weather_conditions(day['conditions'])}",
                ""
            ])

        # Полезные советы
        tips = NotificationMessageBuilder._get_weather_tips(daily_summary[:3])
        if tips:
            message_lines.append(tips)
        
        # Подпись
        message_lines.extend([
            "---",
            "🚗 *ClearyFi* - умные уведомления для вашего авто"
        ])
        
        return "\n".join(message_lines)
    
    @staticmethod
    def build_current_weather_message(city: str, current_weather: Dict) -> str:
        """
        Строит сообщение с текущей погодой.
        
        Args:
            city: Название города
            current_weather: Данные текущей погоды
            
        Returns:
            Сообщение о текущей погоде
        """
        if not current_weather:
            return f"❌ Не удалось получить данные о погоде в {city}"
        
        message_lines = [
            f"🌤 *Погода сейчас в {city}:*",
            "",
            f"🌡 *Температура:* {format_temperature(current_weather['temperature'])}",
            f"🎯 *Ощущается как:* {format_temperature(current_weather['feels_like'])}",
            f"💧 *Влажность:* {current_weather['humidity']}%",
            f"📊 *Давление:* {current_weather['pressure']:.0f} мм рт. ст.",
            f"💨 *Ветер:* {format_wind_speed(current_weather['wind_speed'])}",
            f"☁️ *Состояние:* {current_weather['weather'].capitalize()}",
            "",
            "_Обновлено: сейчас_"
        ]
        
        return "\n".join(message_lines)
    
    @staticmethod
    def build_alerts_message(city: str, alerts: List[str]) -> str:
        """
        Строит сообщение с погодными предупреждениями.
        
        Args:
            city: Название города
            alerts: Список предупреждений
            
        Returns:
            Сообщение с предупреждениями
        """
        if not alerts:
            return f"✅ *В {city} особых предупреждений нет*\n\n_Погодные условия стабильные_"
        
        message_lines = [f"⚠️ *Погодные предупреждения для {city}:*", ""]
        message_lines.extend(alerts)
        
        return "\n".join(message_lines)
    
    @staticmethod
    def _get_wash_recommendation(day_data: Dict) -> Tuple[str, str]:
        """
        Определяет рекомендацию по мойке для дня на основе погодных данных.
        
        Args:
            day_data: Данные о погоде за день
            
        Returns:
            Кортеж (эмодзи-статус, текстовое описание)
        """
        temp = day_data.get('temp', 0)
        rain_prob = day_data.get('rain_prob', 0)
        humidity = day_data.get('humidity', 0)
        wind = day_data.get('wind', 0)
        
        # 🔄 СМЯГЧЕННЫЕ КРИТЕРИИ ОЦЕНКИ:
        
        # 1. ОТЛИЧНЫЕ условия
        if rain_prob == 0 and temp >= 10 and humidity <= 75 and wind < 8:
            return "🌟", "Идеальный день для мойки"
        elif rain_prob == 0 and temp >= 3 and humidity <= 85 and wind < 12:
            return "✅", "Хороший день для мойки"
        
        # 2. УСЛОВНО ПОДХОДЯЩИЕ условия
        elif rain_prob == 0 and temp >= -2 and humidity <= 90:
            if temp < 3:
                return "⚠️", "Можно помыть, но будет прохладно"
            elif humidity > 85:
                return "⚠️", "Можно помыть, но сохнуть будет дольше"
            elif wind >= 8:
                return "⚠️", "Можно помыть, но ветрено"
            else:
                return "⚠️", "Условно подходит для мойки"
        
        # 3. НЕРЕКОМЕНДУЕМЫЕ условия
        
        # Главный запрещающий фактор - осадки
        elif rain_prob > 0:
            precipitation_type = "дождь" if temp > 0 else "снег"
            return "❌", f"Не рекомендуется: ожидается {precipitation_type}"
        
        # Сильный ветер
        elif wind >= 12:
            return "❌", "Не рекомендуется: сильный ветер"
        
        # Очень высокая влажность
        elif humidity > 90:
            return "❌", "Не рекомендуется: очень высокая влажность"
        
        # Слишком холодно
        elif temp < -2:
            return "❌", "Не рекомендуется: возможен лед"
        
        # 4. НЕОПРЕДЕЛЕННЫЕ условия
        else:
            return "❓", "Сложные погодные условия"
    
    @staticmethod
    def _get_weather_tips(days_forecast: List[Dict]) -> str:
        """
        Генерирует полезные советы на основе прогноза погоды.
        
        Args:
            days_forecast: Прогноз на несколько дней
            
        Returns:
            Строка с советами или пустая строка
        """
        tips = []
        
        # Паттерн 1: Дождливые дни
        rainy_days = [day for day in days_forecast if day.get('rain_prob', 0) > 0]
        if rainy_days:
            rainy_count = len(rainy_days)
            if rainy_count >= 2:
                tips.append("🌧️ *Совет:* Несколько дождливых дней - мойку лучше отложить")
            else:
                tips.append("🌧️ *Совет:* В дождливые дни мойку лучше отложить")
        
        # Паттерн 2: Холодные дни
        cold_days = [day for day in days_forecast if day.get('temp', 0) < -2]
        if cold_days:
            tips.append("🧊 *Совет:* При температуре ниже -2°C возможен лед на дорогах")
        
        # Паттерн 3: Ветреные дни
        windy_days = [day for day in days_forecast if day.get('wind', 0) >= 12]
        if windy_days:
            tips.append("💨 *Совет:* В сильный ветер машина быстро покрывается пылью")
        
        # Паттерн 4: Благоприятный период
        good_days = [day for day in days_forecast if 
                    day.get('rain_prob', 0) == 0 and 
                    day.get('temp', 0) >= 3 and
                    day.get('humidity', 0) <= 85 and
                    day.get('wind', 0) < 12]
        
        if len(good_days) >= 2:
            tips.append("👍 *Совет:* Отличные дни для ухода за автомобилем!")
        elif len(good_days) == 1:
            tips.append("👌 *Совет:* Есть подходящий день для мойки")
        
        # Паттерн 5: Высокая влажность
        humid_days = [day for day in days_forecast if day.get('humidity', 0) > 90]
        if humid_days:
            tips.append("💧 *Совет:* Высокая влажность - машина будет долго сохнуть")
        
        # Паттерн 6: Идеальные условия
        perfect_days = [day for day in days_forecast if 
                       day.get('rain_prob', 0) == 0 and 
                       day.get('temp', 0) >= 10 and
                       day.get('humidity', 0) <= 75 and
                       day.get('wind', 0) < 8]
        
        if perfect_days:
            tips.append("🌟 *Совет:* Идеальные условия для мойки и ухода за авто!")
        
        # Форматируем советы
        if tips:
            tips_text = "💡 *Полезные советы:*\n" + "\n".join(f"• {tip}" for tip in tips) + "\n"
            return tips_text
        else:
            return ""
