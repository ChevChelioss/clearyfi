#!/usr/bin/env python3
"""
Тестовый скрипт для проверки DeepSeek интеграции
"""

import os
import sys
from dotenv import load_dotenv

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_deepseek_integration():
    """Тестирует интеграцию с DeepSeek"""
    load_dotenv()
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    print("🔧 Тестирование DeepSeek интеграции...")
    print(f"API ключ: {'✅ Указан' if api_key else '❌ Отсутствует'}")
    
    if not api_key:
        print("\n❌ API ключ DeepSeek не найден в .env файле")
        print("Добавьте в .env файл:")
        print("DEEPSEEK_API_KEY=your_actual_deepseek_api_key_here")
        return False
    
    try:
        from services.ai.deepseek_service import DeepSeekService
        
        print("✅ Модуль DeepSeekService загружен успешно")
        
        # Инициализируем сервис
        deepseek = DeepSeekService(api_key)
        print("✅ DeepSeekService инициализирован")
        
        # Тестируем соединение
        if deepseek.test_connection():
            print("✅ Соединение с DeepSeek API установлено")
            
            # Тестируем получение рекомендации
            test_data = {
                'city': 'Москва',
                'current': {
                    'temperature': 15,
                    'condition': 'Clear',
                    'precipitation': 0,
                    'wind_speed': 3
                },
                'forecast': [
                    {'day': 0, 'condition': 'Clear', 'temperature': 15, 'precipitation': 0},
                    {'day': 1, 'condition': 'Cloudy', 'temperature': 12, 'precipitation': 0},
                    {'day': 2, 'condition': 'Rain', 'temperature': 10, 'precipitation': 5}
                ]
            }
            
            recommendation = deepseek.get_recommendation(test_data, "car_wash")
            if recommendation:
                print("✅ Получена рекомендация от DeepSeek:")
                print("-" * 50)
                print(recommendation[:200] + "..." if len(recommendation) > 200 else recommendation)
                print("-" * 50)
            else:
                print("❌ Не удалось получить рекомендацию")
                
            return True
        else:
            print("❌ Не удалось установить соединение с DeepSeek API")
            print("Проверьте:")
            print("1. Правильность API ключа")
            print("2. Доступность API DeepSeek")
            print("3. Интернет-соединение")
            return False
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь, что файл services/ai/deepseek_service.py существует")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

if __name__ == "__main__":
    test_deepseek_integration()
