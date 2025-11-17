#!/usr/bin/env python3
"""
Единая система логирования для ClearyFi
"""

import logging
import sys
from typing import Optional


class Logger:
    """Настраивает и возвращает логгер для всего приложения"""
    
    @staticmethod
    def setup(level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
        """
        Настраивает логгер
        
        Args:
            level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
            log_file: Путь к файлу для записи логов (опционально)
            
        Returns:
            Настроенный логгер
        """
        # Создаем логгер с именем 'clearyfi'
        logger = logging.getLogger("clearyfi")
        
        # Устанавливаем уровень логирования
        logger.setLevel(getattr(logging, level.upper()))
        
        # Формат логов
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Обработчик для вывода в консоль
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Обработчик для записи в файл (если указан)
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # Запрещаем передачу логов родительским логгерам
        logger.propagate = False
        
        return logger


# Создаем глобальный логгер для импорта в других модулях
logger = Logger.setup()
