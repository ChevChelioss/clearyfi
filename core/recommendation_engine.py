# core/recommendation_engine.py
from typing import List, Dict, Any, TypedDict, Optional


class ForecastSummary(TypedDict):
    wash_advice: str
    mud_risk: str
    alerts: List[str]
    best_days: List[str]
    day_summaries: Dict[str, str]


class DayData(TypedDict, total=False):
    date: str
    temp: float
    humidity: float
    conditions: List[str]
    rain_prob: float
    mud_flag: bool
    dry_window: bool
    temp_drop: bool
    confidence: float
    dry_hours: float
    wind_speed: float
    sunny_hours: float
    pollen_level: float


class RecommendationEngine:
    """
    RecommendationEngine — формирует человекочитаемые рекомендации
    из нормализованных данных (days) и списка событий per day.
    """

    def __init__(self):
        pass

    def build_forecast_summary(
        self,
        days: List[DayData],
        events_by_day: Dict[str, List[Dict[str, Any]]]
    ) -> ForecastSummary:
        summary: ForecastSummary = {
            "wash_advice": "",
            "mud_risk": "",
            "alerts": [],
            "best_days": [],
            "day_summaries": {}
        }

        summary["wash_advice"] = self._build_wash_advice(days, events_by_day)
        summary["mud_risk"] = self._build_mud_risk(days, events_by_day)
        summary["alerts"] = self._build_alerts(days, events_by_day)
        summary["best_days"] = self._find_best_wash_days(days, events_by_day)

        for d in days:
            date = d.get("date", "unknown")
            evs = events_by_day.get(date, [])
            summary["day_summaries"][date] = self._build_day_text(d, evs)

        return summary

    # ------------------------------------------------------------------
    # Washing advice with prioritization
    # ------------------------------------------------------------------
    def _build_wash_advice(self, days: List[DayData], events: Dict[str, List[Dict[str, Any]]]) -> str:
        excellent_days: List[str] = []
        good_days: List[str] = []
        acceptable_days: List[str] = []

        for day in days:
            date = day.get("date", "")
            dry_window = bool(day.get("dry_window", False))
            rain_prob = float(day.get("rain_prob", 0))
            mud_flag = bool(day.get("mud_flag", False))
            confidence = float(day.get("confidence", 1.0))
            dry_hours = float(day.get("dry_hours", 0))

            # Excellent: clearly dry, no mud, high confidence
            if dry_window and rain_prob == 0 and not mud_flag and confidence > 0.8:
                excellent_days.append(date)
            # Good: dry window and low rain prob (<=0.2) and no mud
            elif dry_window and rain_prob <= 0.2 and not mud_flag:
                good_days.append(date)
            # Acceptable: low rain prob and some dry hours
            elif rain_prob <= 0.3 and not mud_flag and dry_hours >= 6:
                acceptable_days.append(date)

        # Формируем текст
        if excellent_days:
            if len(excellent_days) == 1:
                return f"Идеальный день для мойки: {excellent_days[0]}. Полностью сухие условия."
            return f"Лучшие дни для мойки: {', '.join(excellent_days[:2])}. Гарантированно сухая погода."
        if good_days:
            return f"Хорошие дни для мойки: {', '.join(good_days[:2])}. Низкая вероятность осадков."
        if acceptable_days:
            return f"Возможна мойка {acceptable_days[0]}, но есть некоторый риск. Рекомендуется утренняя мойка."
        # Анализ причин (почему нет подходящих дней)
        reasons = []
        if any(float(d.get("rain_prob", 0)) > 0.5 for d in days):
            reasons.append("ожидаются осадки")
        if any(bool(d.get("mud_flag", False)) for d in days):
            reasons.append("есть риск грязи")
        if not any(bool(d.get("dry_window", False)) for d in days):
            reasons.append("нет сухих периодов")
        reason_text = ", ".join(reasons) if reasons else "неблагоприятные условия"
        return f"Мойку лучше отложить: {reason_text}."

    # ------------------------------------------------------------------
    # Mud risk analysis with gradation
    # ------------------------------------------------------------------
    def _build_mud_risk(self, days: List[DayData], events: Dict[str, List[Dict[str, Any]]]) -> str:
        high_risk: List[str] = []
        medium_risk: List[str] = []
        low_risk: List[str] = []

        for d in days:
            date = d.get("date", "")
            mud_flag = bool(d.get("mud_flag", False))
            rain_prob = float(d.get("rain_prob", 0))

            if mud_flag and rain_prob >= 0.7:
                high_risk.append(f"{date} (сильный риск)")
            elif mud_flag and rain_prob >= 0.3:
                medium_risk.append(f"{date} (умеренный риск)")
            elif mud_flag:
                low_risk.append(f"{date} (низкий риск)")

        if high_risk:
            return f"ВЫСОКИЙ риск грязи: {', '.join(high_risk)}. Избегайте поездок в эти дни."
        if medium_risk:
            return f"Умеренный риск грязи: {', '.join(medium_risk)}. Будьте осторожны на грунтовых дорогах."
        if low_risk:
            return f"Минимальный риск грязи: {', '.join(low_risk)}. Обычные меры предосторожности."
        return "Грязевых участков не ожидается. Дороги в хорошем состоянии."

    # ------------------------------------------------------------------
    # Alerts with priorities (critical / important / info)
    # ------------------------------------------------------------------
    def _build_alerts(self, days: List[DayData], events: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        alerts: List[str] = []
        for d in days:
            date = d.get("date", "")
            # Critical
            if bool(d.get("ice_risk", False)):
                alerts.append(f"🚨 {date}: ОБЛЕДЕНЕНИЕ ДОРОГ! Крайне опасно!")
            if bool(d.get("storm_risk", False)):
                alerts.append(f"🚨 {date}: ШТОРМОВОЕ ПРЕДУПРЕЖДЕНИЕ!")

            # Important
            temp_drop = bool(d.get("temp_drop", False))
            temp = d.get("temp", None)
            if temp_drop and temp is not None and float(temp) < 0:
                alerts.append(f"⚠️ {date}: Резкое похолодание до {temp}°C — риск гололеда!")
            elif temp_drop:
                alerts.append(f"⚠️ {date}: Резкое похолодание (изменение температуры).")

            if float(d.get("rain_prob", 0)) == 1 and any("snow" in c.lower() for c in d.get("conditions", [])):
                alerts.append(f"⚠️ {date}: Мокрый снег. Ухудшение видимости и сцепления.")

            # Informational
            if float(d.get("humidity", 0)) > 90:
                alerts.append(f"ℹ️ {date}: Очень высокая влажность ({d.get('humidity')}%).")
            if float(d.get("wind_speed", d.get("wind", 0))) > 15:
                alerts.append(f"ℹ️ {date}: Сильный ветер ({d.get('wind_speed', d.get('wind', 0))} м/с).")
        return alerts

    # ------------------------------------------------------------------
    # Find best days using scoring
    # ------------------------------------------------------------------
    def _find_best_wash_days(self, days: List[DayData], events: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        scored_days: List[tuple] = []

        for d in days:
            date = d.get("date", "")
            score = 0
            # Basic criteria
            if d.get("dry_window", False):
                score += 3
            rp = float(d.get("rain_prob", 0))
            if rp == 0:
                score += 2
            elif rp <= 0.1:
                score += 1
            if not d.get("mud_flag", False):
                score += 2

            # Bonus factors
            if float(d.get("wind_speed", d.get("wind", 0))) < 5:
                score += 1
            if float(d.get("sunny_hours", 0)) > 6:
                score += 1
            temp = d.get("temp", 0)
            if isinstance(temp, (int, float)) and 15 <= temp <= 25:
                score += 1

            # Penalties
            if float(d.get("humidity", 0)) > 85:
                score -= 1
            if float(d.get("pollen_level", 0)) > 7:
                score -= 1

            if score >= 5:
                scored_days.append((date, score))

        scored_days.sort(key=lambda x: x[1], reverse=True)
        return [date for date, _ in scored_days[:3]]

    # ------------------------------------------------------------------
    # Build detailed day text
    # ------------------------------------------------------------------
    def _build_day_text(self, day: DayData, evs: List[Dict[str, Any]]) -> str:
        date = day.get("date", "")
        temp = day.get("temp", "N/A")
        hum = day.get("humidity", "N/A")
        cond = ", ".join(day.get("conditions", []))
        mud_flag = bool(day.get("mud_flag", False))
        rain_prob = day.get("rain_prob", 0)
        rain_text = f"{int(rain_prob*100)}%" if isinstance(rain_prob, (int, float)) and rain_prob <= 1 else str(rain_prob)

        # Risk label
        if mud_flag and isinstance(rain_prob, (int, float)) and rain_prob > 0.5:
            risk = "Высокий"
        elif mud_flag:
            risk = "Умеренный"
        else:
            risk = "Низкий"

        wash_conditions = []
        if day.get("dry_window", False):
            wash_conditions.append("есть сухое окно")
        if rain_prob == 0:
            wash_conditions.append("без осадков")
        if not mud_flag:
            wash_conditions.append("нет грязи")

        wash_status = "Подходит для мойки" if wash_conditions else "Не подходит для мойки"
        wash_details = f" ({', '.join(wash_conditions)})" if wash_conditions else ""

        ev_texts = [e.get("message") or e.get("name") for e in evs] if evs else []
        ev_summary = " | ".join(ev_texts) if ev_texts else "нет особых событий"

        return (f"{date}: {cond}, {temp}°C, влажность: {hum}%, осадки: {rain_text}, "
                f"грязевой риск: {risk}. {wash_status}{wash_details}. События: {ev_summary}")
