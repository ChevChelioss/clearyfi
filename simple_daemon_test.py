#!/usr/bin/env python3
import sys
import os
import time

# Добавляем корень проекта
sys.path.insert(0, '/data/data/com.termux/files/home/projects/clearyfi')

print("=== ТЕСТ ДЕМОНА ===")

try:
    from services.storage.subscriber_db import SubscriberDBConnection
    print("✅ SubscriberDBConnection - OK")
    
    from services.weather.weather_api_client import WeatherAPIClient
    print("✅ WeatherAPIClient - OK")
    
    from core.weather_analyzer import WeatherAnalyzer
    print("✅ WeatherAnalyzer - OK")
    
    from core.recommendation_engine import RecommendationEngine
    print("✅ RecommendationEngine - OK")
    
    import telebot
    print("✅ telebot - OK")
    
    from config.settings import TELEGRAM_BOT_TOKEN
    print("✅ TELEGRAM_BOT_TOKEN - OK")
    
    from services.daemon.daemon_manager import DaemonManager
    print("✅ DaemonManager - OK")
    
    print("🎉 ВСЕ ИМПОРТЫ УСПЕШНЫ!")
    
    # Простой цикл демона
    print("🚀 Демон запущен (тестовая версия)")
    while True:
        print("🔍 Работаю...")
        time.sleep(10)
        
except ImportError as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
