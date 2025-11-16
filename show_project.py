#!/usr/bin/env python3
"""
ПРАВИЛЬНЫЙ СКРИПТ ДЛЯ ОТОБРАЖЕНИЯ СТРУКТУРЫ CLEARYFI
Использует правильную фильтрацию и не выходит за пределы проекта
"""

import os
from pathlib import Path

class ProjectVisualizer:
    def __init__(self, project_path):
        # Преобразуем в абсолютный путь и РЕШАЕМ проблему с символическими ссылками
        self.project_path = Path(project_path).resolve()  # .resolve() вместо .absolute()
        
        print(f"🔍 Путь проекта: {self.project_path}")
        print(f"🔍 Существует: {self.project_path.exists()}")
        
        # Более строгий список игнорируемых элементов
        self.ignore_dirs = {
            '.git', '__pycache__', '.pytest_cache', 'clearyfi_env',
            '.cache', 'pip', '.npm', '.android', '.termux',
            '.local', '.config', 'tmp', 'temp'
        }
        
        self.ignore_files = {
            '.DS_Store', '.gitignore', '*.body', '*.tmp', 
            '*.log', '*.bak', '*.swp'
        }

    def is_in_project_bounds(self, path):
        """
        ВАЖНО: Проверяем что путь находится ВНУТРИ нашего проекта
        а не в какой-то другой папке системы
        """
        try:
            # Преобразуем оба пути к абсолютным и сравниваем
            abs_path = Path(path).resolve()
            abs_project = self.project_path.resolve()
            
            # Проверяем что путь начинается с пути проекта
            return str(abs_path).startswith(str(abs_project))
        except:
            return False

    def should_ignore(self, path):
        """Проверяем нужно ли игнорировать путь"""
        if not self.is_in_project_bounds(path):
            return True
            
        name = path.name
        
        if name in self.ignore_dirs:
            return True
            
        # Игнорируем скрытые файлы и папки
        if name.startswith('.'):
            return True
            
        # Игнорируем файлы с определенными расширениями
        if any(name.endswith(ext) for ext in ['.body', '.tmp', '.log', '.bak']):
            return True
            
        return False

    def count_project_files(self):
        """
        ПРАВИЛЬНЫЙ подсчет файлов - только в границах проекта
        """
        py_files = []
        total_lines = 0
        folders = set()
        
        if not self.project_path.exists():
            return py_files, total_lines, folders
            
        # Используем os.walk с правильной фильтрацией
        for root, dirs, files in os.walk(self.project_path):
            # Фильтруем папки которые нужно игнорировать
            dirs[:] = [d for d in dirs if not self.should_ignore(Path(root) / d)]
            
            # Добавляем папку в счетчик
            rel_path = Path(root).relative_to(self.project_path) if root != str(self.project_path) else Path('.')
            if rel_path != Path('.'):
                folders.add(str(rel_path))
            
            # Обрабатываем файлы
            for file in files:
                file_path = Path(root) / file
                
                if self.should_ignore(file_path):
                    continue
                    
                if file.endswith('.py'):
                    py_files.append(file_path)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            total_lines += len(f.readlines())
                    except Exception as e:
                        print(f"⚠️ Ошибка чтения {file_path}: {e}")
        
        return py_files, total_lines, folders

    def print_tree(self, path=None, prefix="", is_last=True, level=0):
        """Правильное отображение дерева"""
        if path is None:
            path = self.project_path
            
        if level > 5:  # Защита от бесконечной рекурсии
            return
            
        if not self.is_in_project_bounds(path):
            return
            
        if self.should_ignore(path):
            return

        # Определяем имя и иконку
        if path == self.project_path:
            name = "clearyfi/"
            icon = "🚗"
        else:
            name = path.name + ("/" if path.is_dir() else "")
            icon = "📁" if path.is_dir() else "🐍" if path.suffix == '.py' else "📄"

        # Выводим элемент
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{icon} {name}")

        # Для папок - обрабатываем содержимое
        if path.is_dir() and level < 4:
            try:
                items = []
                for item in path.iterdir():
                    if self.is_in_project_bounds(item) and not self.should_ignore(item):
                        items.append(item)
                
                # Сортируем: папки сначала, потом файлы
                items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
                
                new_prefix = prefix + ("    " if is_last else "│   ")
                
                for i, item in enumerate(items):
                    is_last_item = (i == len(items) - 1)
                    self.print_tree(item, new_prefix, is_last_item, level + 1)
                    
            except (PermissionError, OSError) as e:
                print(f"{prefix}    └── 🔒 Ошибка доступа: {e}")

    def show_project_info(self):
        """Показываем информацию о проекте"""
        print("🚗 CLEARYFI 2.0 - ПРАВИЛЬНАЯ СТРУКТУРА")
        print("=" * 50)
        
        if not self.project_path.exists():
            print(f"❌ Папка проекта не найдена: {self.project_path}")
            return
        
        # Считаем файлы ПРАВИЛЬНЫМ методом
        py_files, total_lines, folders = self.count_project_files()
        
        print(f"📊 ПРАВИЛЬНАЯ статистика:")
        print(f"   📁 Папок: {len(folders)}")
        print(f"   🐍 Файлов .py: {len(py_files)}")
        print(f"   📝 Строк кода: {total_lines}")
        print(f"   📍 Путь: {self.project_path}")
        print()
        
        # Показываем дерево
        print("🌳 Структура папок:")
        self.print_tree()

def main():
    """Главная функция"""
    project_path = "/data/data/com.termux/files/home/projects/clearyfi"
    
    visualizer = ProjectVisualizer(project_path)
    visualizer.show_project_info()

if __name__ == "__main__":
    main()
