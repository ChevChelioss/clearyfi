#!/usr/bin/env python3
"""
Построитель умных рекомендаций для автомобилистов
"""

from typing import Dict, List, Optional
from utils.date_utils import format_date_short, get_relative_day_label
from utils.text_utils import translate_weather_conditions, format_temperature, format_wind_speed


class RecommendationBuilder:
    """
    Строитель умных рекомендаций для автомобилистов на основе погодных данных.
    """
    
    @staticmethod
    def build_car_wash_recommendation(city: str, weather_data: Dict) -> str:
        """
        Строит рекомендацию по мойке автомобиля.
        
        Args:
            city: Название города
            weather_data: Данные о погоде
            
        Returns:
            Сообщение с рекомендацией
        """
        daily_summary = weather_data.get('daily_summary', [])
        best_day = weather_data.get('best_wash_day')
        
        if not daily_summary:
            return f"❌ Не удалось получить данные для {city}"
        
        message_lines = [
            "🚗 *ClearyFi - Рекомендации по мойке автомобиля*",
            "",
            f"📍 *Город:* {city}",
            ""
        ]
        
        # Главная рекомендация
        if best_day:
            day_label = get_relative_day_label(best_day['date'])
            message_lines.extend([
                "✅ *РЕКОМЕНДУЕМ ПОМЫТЬ АВТО:*",
                f"📅 *Когда:* {day_label}",
                f"🌡 *Температура:* {format_temperature(best_day['temp'])}",
                f"💧 *Влажность:* {best_day['humidity']:.0f}%", 
                f"💨 *Ветер:* {format_wind_speed(best_day['wind'])}",
                f"☁️ *Погода:* {translate_weather_conditions(best_day['conditions'])}",
                ""
            ])
        else:
            message_lines.extend([
                "⚠️ *Внимание:* Идеальных дней для мойки не найдено",
                "💡 *Совет:* Мойте авто в крытой мойке или отложите до улучшения погоды",
                ""
            ])
        
        # Детальные рекомендации на 3 дня
        message_lines.append("📊 *Прогноз для планирования мойки:*")
        message_lines.append("")
        
        for i, day in enumerate(daily_summary[:3]):
            day_label = get_relative_day_label(day['date'])
            wash_advice = RecommendationBuilder._get_wash_advice(day)
            
            message_lines.extend([
                f"{wash_advice['emoji']} *{day_label}*",
                f"   {wash_advice['text']}",
                f"   🌡 {format_temperature(day['temp'])} | 💧 {day['humidity']:.0f}% | 💨 {format_wind_speed(day['wind'])}",
                f"   ☁️ {translate_weather_conditions(day['conditions'])}",
                ""
            ])
        
        # Общие советы
        tips = RecommendationBuilder._get_wash_tips(daily_summary[:3])
        message_lines.append(tips)
        
        message_lines.extend([
            "---",
            "🚗 *ClearyFi* - умные рекомендации для вашего авто"
        ])
        
        return "\n".join(message_lines)
    
    @staticmethod
    def build_road_conditions_alert(city: str, weather_data: Dict) -> str:
        """
        Строит предупреждения о дорожных условиях.
        
        Args:
            city: Название города
            weather_data: Данные о погоде
            
        Returns:
            Сообщение с предупреждениями
        """
        daily_summary = weather_data.get('daily_summary', [])
        alerts = weather_data.get('alerts', [])
        
        message_lines = [
            "🛣 *ClearyFi - Дорожные условия и предупреждения*",
            "",
            f"📍 *Город:* {city}",
            ""
        ]
        
        # Критические предупреждения
        critical_alerts = []
        for i, day in enumerate(daily_summary[:2]):  # Сегодня и завтра
            day_label = "Сегодня" if i == 0 else "Завтра"
            day_alerts = RecommendationBuilder._get_road_alerts(day, day_label)
            critical_alerts.extend(day_alerts)
        
        if critical_alerts:
            message_lines.append("🚨 *КРИТИЧЕСКИЕ ПРЕДУПРЕЖДЕНИЯ:*")
            for alert in critical_alerts:
                message_lines.append(f"• {alert}")
            message_lines.append("")
        else:
            message_lines.append("✅ *Критических предупреждений нет*")
            message_lines.append("")
        
        # Рекомендации по вождению
        message_lines.append("🎯 *Рекомендации по вождению:*")
        driving_tips = RecommendationBuilder._get_driving_tips(daily_summary[:2])
        for tip in driving_tips:
            message_lines.append(f"• {tip}")
        message_lines.append("")
        
        # Прогноз условий на 3 дня
        message_lines.append("📊 *Прогноз дорожных условий:*")
        message_lines.append("")
        
        for i, day in enumerate(daily_summary[:3]):
            day_label = get_relative_day_label(day['date'])
            road_condition = RecommendationBuilder._get_road_condition(day)
            
            message_lines.extend([
                f"{road_condition['emoji']} *{day_label}*",
                f"   {road_condition['text']}",
                f"   🌡 {format_temperature(day['temp'])} | 💧 {day['humidity']:.0f}%",
                f"   💨 {format_wind_speed(day['wind'])} | ☁️ {translate_weather_conditions(day['conditions'])}",
                ""
            ])
        
        message_lines.extend([
            "---", 
            "🛣 *Ведите аккуратно!*"
        ])
        
        return "\n".join(message_lines)
    
    @staticmethod
    def build_tire_recommendation(city: str, weather_data: Dict) -> str:
        """
        Строит рекомендации по шинам и шиномонтажу.
        
        Args:
            city: Название города
            weather_data: Данные о погоде
            
        Returns:
            Сообщение с рекомендациями по шинам
        """
        daily_summary = weather_data.get('daily_summary', [])
        
        message_lines = [
            "🛞 *ClearyFi - Рекомендации по шинам*",
            "",
            f"📍 *Город:* {city}",
            ""
        ]
        
        # Анализ температуры для рекомендаций по шинам
        temp_analysis = RecommendationBuilder._analyze_temperature_trend(daily_summary)
        
        message_lines.append("🌡 *Анализ температурного режима:*")
        message_lines.append(f"• {temp_analysis['trend']}")
        message_lines.append(f"• {temp_analysis['recommendation']}")
        message_lines.append("")
        
        # Рекомендации по смене шин
        tire_recommendations = RecommendationBuilder._get_tire_recommendations(daily_summary)
        if tire_recommendations:
            message_lines.append("🛞 *Рекомендации по шиномонтажу:*")
            for rec in tire_recommendations:
                message_lines.append(f"• {rec}")
            message_lines.append("")
        
        # Подробный прогноз для планирования
        message_lines.append("📊 *Условия для работ с шинами:*")
        message_lines.append("")
        
        for i, day in enumerate(daily_summary[:3]):
            day_label = get_relative_day_label(day['date'])
            tire_advice = RecommendationBuilder._get_tire_day_advice(day)
            
            message_lines.extend([
                f"{tire_advice['emoji']} *{day_label}*",
                f"   {tire_advice['text']}",
                f"   🌡 {format_temperature(day['temp'])} | 💧 {day['humidity']:.0f}%",
                ""
            ])
        
        # Общие советы по шинам
        general_tips = [
            "💡 *Общие советы:*",
            "• Летняя резина теряет эластичность при температуре ниже +7°C",
            "• Зимняя резина изнашивается быстрее при температуре выше +10°C", 
            "• Оптимальная температура для шиномонтажа: от +5°C до +20°C",
            "• Избегайте мойки и шиномонтажа в дождливую погоду"
        ]
        
        message_lines.extend(general_tips)
        message_lines.extend(["---", "🛞 *Безопасных вам дорог!*"])
        
        return "\n".join(message_lines)
    
    @staticmethod
    def _get_wash_advice(day_data: Dict) -> Dict:
        """Возвращает совет по мойке для дня"""
        temp = day_data.get('temp', 0)
        rain_prob = day_data.get('rain_prob', 0)
        humidity = day_data.get('humidity', 0)
        wind = day_data.get('wind', 0)
        
        if rain_prob > 50:
            return {"emoji": "🌧️", "text": "Не мойте: сильный дождь"}
        elif rain_prob > 20:
            return {"emoji": "⚠️", "text": "Рискованно: возможен дождь"}
        elif temp < -5:
            return {"emoji": "🧊", "text": "Опасно: возможен лед на кузове"}
        elif temp < 0:
            return {"emoji": "❄️", "text": "Холодно: вода может замерзнуть"}
        elif temp > 25:
            return {"emoji": "☀️", "text": "Отлично: быстро высохнет"}
        elif wind > 10:
            return {"emoji": "💨", "text": "Ветрено: быстро появится пыль"}
        elif humidity > 85:
            return {"emoji": "💧", "text": "Влажно: будет долго сохнуть"}
        else:
            return {"emoji": "✅", "text": "Идеально для мойки"}
    
    @staticmethod
    def _get_road_alerts(day_data: Dict, day_label: str) -> List[str]:
        """Возвращает предупреждения о дорожных условиях"""
        alerts = []
        temp = day_data.get('temp', 0)
        rain_prob = day_data.get('rain_prob', 0)
        wind = day_data.get('wind', 0)
        
        if temp < -10:
            alerts.append(f"🚨 {day_label}: Экстремальный холод - риск обледенения")
        elif temp < 0:
            alerts.append(f"⚠️ {day_label}: Возможен гололед")
        
        if rain_prob > 70:
            alerts.append(f"🌧️ {day_label}: Сильный дождь - аквапланирование")
        elif rain_prob > 30:
            alerts.append(f"💧 {day_label}: Дождь - увеличить дистанцию")
        
        if wind > 15:
            alerts.append(f"💨 {day_label}: Ураганный ветер - осторожно на трассе")
        elif wind > 10:
            alerts.append(f"🌬️ {day_label}: Сильный ветер - особенно для высоких авто")
        
        return alerts
    
    @staticmethod
    def _get_driving_tips(days_forecast: List[Dict]) -> List[str]:
        """Возвращает советы по вождению"""
        tips = []
        
        for day in days_forecast:
            temp = day.get('temp', 0)
            rain_prob = day.get('rain_prob', 0)
            
            if temp < 0:
                tips.append("Проверьте наличие омывающей жидкости с антифризом")
                tips.append("Держите в багажнике скребок и щетку для стекол")
                break
        
        if any(day.get('rain_prob', 0) > 30 for day in days_forecast):
            tips.append("Проверьте состояние дворников и резинок")
            tips.append("Увеличьте дистанцию до впереди идущего транспорта")
        
        if any(day.get('wind', 0) > 10 for day in days_forecast):
            tips.append("Будьте осторожны при обгоне высоких авто и фур")
        
        # Убираем дубликаты
        return list(set(tips))
    
    @staticmethod
    def _get_road_condition(day_data: Dict) -> Dict:
        """Возвращает оценку дорожных условий"""
        temp = day_data.get('temp', 0)
        rain_prob = day_data.get('rain_prob', 0)
        wind = day_data.get('wind', 0)
        
        if rain_prob > 50 and temp > 0:
            return {"emoji": "🌧️", "text": "Мокрая дорога - осторожно!"}
        elif rain_prob > 50 and temp <= 0:
            return {"emoji": "🧊", "text": "Гололед - крайняя осторожность!"}
        elif temp < -5:
            return {"emoji": "❄️", "text": "Обледенение - опасно!"}
        elif temp < 0:
            return {"emoji": "⚠️", "text": "Возможен гололед"}
        elif wind > 15:
            return {"emoji": "💨", "text": "Сильный ветер - сложно управлять"}
        else:
            return {"emoji": "✅", "text": "Нормальные условия"}
    
    @staticmethod
    def _analyze_temperature_trend(daily_summary: List[Dict]) -> Dict:
        """Анализирует температурный тренд для рекомендаций по шинам"""
        if not daily_summary:
            return {"trend": "Недостаточно данных", "recommendation": "Проверьте позже"}
        
        today_temp = daily_summary[0].get('temp', 0)
        avg_temp = sum(day.get('temp', 0) for day in daily_summary) / len(daily_summary)
        
        if avg_temp < 5:
            return {
                "trend": "Устойчивые холода",
                "recommendation": "Пора переходить на зимнюю резину"
            }
        elif avg_temp > 10:
            return {
                "trend": "Стабильное тепло", 
                "recommendation": "Можно использовать летнюю резину"
            }
        else:
            return {
                "trend": "Переходный период",
                "recommendation": "Рассмотрите всесезонную резину"
            }
    
    @staticmethod
    def _get_tire_recommendations(daily_summary: List[Dict]) -> List[str]:
        """Возвращает рекомендации по шинам"""
        recommendations = []
        temps = [day.get('temp', 0) for day in daily_summary]
        avg_temp = sum(temps) / len(temps)
        
        if avg_temp < 5 and all(temp < 7 for temp in temps):
            recommendations.append("СРОЧНО перейдите на зимнюю резину")
        elif avg_temp > 10 and all(temp > 7 for temp in temps):
            recommendations.append("Можно установить летнюю резину")
        
        if any(day.get('rain_prob', 0) > 50 for day in daily_summary):
            recommendations.append("Проверьте глубину протектора (дождь)")
        
        return recommendations
    
    @staticmethod
    def _get_tire_day_advice(day_data: Dict) -> Dict:
        """Возвращает совет по шинам для дня"""
        temp = day_data.get('temp', 0)
        rain_prob = day_data.get('rain_prob', 0)
        
        if temp < -10:
            return {"emoji": "🧊", "text": "Очень холодно - только зимняя резина"}
        elif temp < 0:
            return {"emoji": "❄️", "text": "Холодно - рекомендуется зимняя резина"}
        elif temp < 7:
            return {"emoji": "⚠️", "text": "Прохладно - летняя резина опасна"}
        elif rain_prob > 50:
            return {"emoji": "🌧️", "text": "Дождь - проверьте протектор"}
        else:
            return {"emoji": "✅", "text": "Хорошие условия для шиномонтажа"}
    
    @staticmethod
    def _get_wash_tips(days_forecast: List[Dict]) -> str:
        """Возвращает советы по мойке"""
        tips = []
        
        # Анализ ближайших дней
        good_days = [day for day in days_forecast if day.get('rain_prob', 0) == 0]
        
        if len(good_days) >= 2:
            tips.append("🌟 Отличные дни для комплексного ухода за авто!")
        elif good_days:
            tips.append("✅ Есть подходящий день для мойки")
        else:
            tips.append("💡 Рекомендуем крытую мойку или отложить")
        
        # Анализ температуры
        cold_days = [day for day in days_forecast if day.get('temp', 0) < 0]
        if cold_days:
            tips.append("🧊 В холодные дни мойте авто в отапливаемой мойке")
        
        return "💡 *Совет:* " + " | ".join(tips)
