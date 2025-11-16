#!/usr/bin/env python3
import sys
import os

print("=== ДИАГНОСТИКА ИМПОРТОВ ===")
print(f"Текущая директория: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Проверим существование папки services
services_path = os.path.join(os.getcwd(), 'services')
print(f"Папка services существует: {os.path.exists(services_path)}")
print(f"Содержимое services: {os.listdir(services_path) if os.path.exists(services_path) else 'НЕТУ!'}")

# Проверим существование subscriber_db
subscriber_path = os.path.join(services_path, 'storage', 'subscriber_db.py')
print(f"Файл subscriber_db.py существует: {os.path.exists(subscriber_path)}")

# Попробуем добавить текущую директорию в путь
sys.path.insert(0, os.getcwd())

print("\n=== ПОПЫТКА ИМПОРТА ===")
try:
    from services.storage.subscriber_db import SubscriberDBConnection
    print("✅ Импорт SubscriberDBConnection УСПЕШЕН!")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print(f"Детали: {e.__class__.__name__}: {e}")

print("\n=== ПРОВЕРКА СИСТЕМНЫХ ПУТЕЙ ===")
# Проверим все возможные пути
for path in sys.path:
    test_path = os.path.join(path, 'services')
    if os.path.exists(test_path):
        print(f"✅ Найден services в: {path}")
        break
else:
    print("❌ services не найден ни в одном пути sys.path")
