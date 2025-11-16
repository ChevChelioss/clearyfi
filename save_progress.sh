#!/bin/bash
# Скрипт для быстрого сохранения прогресса

DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/data/data/com.termux/files/home/projects/clearyfi"
BACKUP_DIR="/data/data/com.termux/files/home/projects/clearyfi_backup_$DATE"

echo "💾 Сохранение прогресса ClearyFi..."
echo "📅 Временная метка: $DATE"

# Создаем резервную копию
echo "📦 Создаем резервную копию..."
cp -r "$PROJECT_DIR" "$BACKUP_DIR"

# Git коммит
echo "🔨 Создаем git коммит..."
cd "$PROJECT_DIR"
git add .
git commit -m "Checkpoint: $DATE - Сохранение прогресса рефакторинга"

# Сохраняем зависимости
echo "📋 Сохраняем зависимости..."
pip freeze > "requirements_$DATE.txt"

# Сохраняем структуру
echo "📁 Сохраняем структуру проекта..."
find . -name "*.py" -type f > "project_structure_$DATE.txt"

echo "✅ Прогресс сохранен!"
echo "📂 Резервная копия: $BACKUP_DIR"
echo "💿 Git коммит создан"
