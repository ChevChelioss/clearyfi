import difflib

POPULAR_CITIES = [
    "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург",
    "Казань", "Нижний Новгород", "Челябинск", "Самара",
    "Омск", "Ростов-на-Дону", "Уфа", "Красноярск"
]

def normalize_input(raw: str) -> str:
    """Простая нормализация регистра и пробелов."""
    if not raw:
        return ""
    s = raw.strip().lower()
    parts = [p.capitalize() for p in s.split()]
    return " ".join(parts)

def fuzzy_fix(city: str) -> str:
    """Лёгкая корректировка опечаток."""
    matches = difflib.get_close_matches(city, POPULAR_CITIES, n=1, cutoff=0.75)
    if matches:
        return matches[0]
    return city

def normalize_city(raw: str) -> str:
    cleaned = normalize_input(raw)
    fixed = fuzzy_fix(cleaned)
    return fixed
