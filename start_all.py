#!/usr/bin/env python3
"""
Улучшенный скрипт запуска ClearyFi с детальным логированием
"""

import os
import sys
import subprocess
import time
import signal
import logging
from datetime import datetime

# Настройка детального логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clearyfi_launcher.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ClearyFiLauncher')

class ClearyFiStarter:
    def __init__(self):
        self.daemon_process = None
        self.bot_process = None
        self.start_time = datetime.now()
        
    def check_environment(self):
        """Проверяет окружение и зависимости"""
        logger.info("🔍 Проверка окружения...")
        
        # Проверяем существование необходимых файлов
        required_files = [
            "services/daemon/weather_daemon.py",
            "telegram_bot.py",
            "config/settings.py"
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                logger.error(f"❌ Не найден файл: {file_path}")
                return False
            else:
                logger.info(f"✅ Файл найден: {file_path}")
        
        # Проверяем Python модули
        try:
            import telebot
            import requests
            logger.info("✅ Все Python зависимости доступны")
            return True
        except ImportError as e:
            logger.error(f"❌ Отсутствует зависимость: {e}")
            return False
    
    def is_daemon_running(self):
        """Проверяет, запущен ли уже демон"""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "weather_daemon.py"], 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Ошибка проверки демона: {e}")
            return False
    
    def start_daemon(self):
        """Запускает демон уведомлений в фоне"""
        try:
            if self.is_daemon_running():
                logging.info("✅ Демон уже запущен (найден запущенный процесс)")
                return True
            
            logging.info("🚀 Запускаем демон уведомлений...")
            
            # Используем абсолютный путь к демону
            daemon_path = os.path.join(os.getcwd(), "services/daemon/weather_daemon.py")
            
            # Запускаем демон в фоне
            self.daemon_process = subprocess.Popen([
                sys.executable, daemon_path
            ])
            
            # Даем время на инициализацию
            time.sleep(5)
            
            # Проверяем запустился ли демон
            if self.is_daemon_running():
                logging.info("✅ Демон успешно запущен и работает")
                return True
            else:
                logging.error("❌ Демон не запустился, проверьте логи")
                return False
                
        except Exception as e:
            logging.error(f"❌ Критическая ошибка запуска демона: {e}")
            return False
    
    def start_bot(self):
        """Запускает Telegram бота"""
        try:
            logger.info("🤖 Запускаем Telegram бота...")
            logger.info("ℹ️  Бот будет работать в основном процессе")
            logger.info("📝 Логи бота отображаются ниже:")
            logger.info("-" * 50)
            
            # Запускаем бота (блокирующий вызов)
            bot_process = subprocess.Popen(
                [sys.executable, "telegram_bot.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Читаем вывод бота в реальном времени
            for line in bot_process.stdout:
                print(f"[BOT] {line.strip()}")
                
            bot_process.wait()
            return bot_process.returncode
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            return 1
    
    def show_status(self):
        """Показывает статус всех сервисов"""
        logger.info("📊 Статус сервисов ClearyFi:")
        
        # Проверяем демон
        if self.is_daemon_running():
            logger.info("   ✅ Демон уведомлений: ЗАПУЩЕН")
        else:
            logger.info("   ❌ Демон уведомлений: ОСТАНОВЛЕН")
        
        # Проверяем бота
        bot_running = subprocess.run(
            ["pgrep", "-f", "telegram_bot.py"], 
            capture_output=True
        ).returncode == 0
        
        if bot_running:
            logger.info("   ✅ Telegram бот: ЗАПУЩЕН")
        else:
            logger.info("   ❌ Telegram бот: ОСТАНОВЛЕН")
        
        # Показываем время работы
        uptime = datetime.now() - self.start_time
        logger.info(f"   ⏱ Время работы: {uptime}")
    
    def stop_services(self):
        """Останавливает все сервисы"""
        logger.info("🛑 Останавливаем сервисы ClearyFi...")
        
        # Останавливаем демон
        if self.daemon_process:
            logger.info("⏹️  Останавливаем демон...")
            self.daemon_process.terminate()
            try:
                self.daemon_process.wait(timeout=10)
                logger.info("✅ Демон остановлен")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️  Демон не ответил на terminate, принудительное завершение...")
                self.daemon_process.kill()
        
        # Убиваем процессы по имени
        processes = ["weather_daemon.py", "telegram_bot.py"]
        for proc_name in processes:
            result = subprocess.run(["pkill", "-f", proc_name], capture_output=True)
            if result.returncode == 0:
                logger.info(f"✅ Процесс {proc_name} остановлен")
        
        logger.info("✅ Все сервисы ClearyFi остановлены")
    
    def run(self):
        """Основной метод запуска"""
        try:
            print("\n" + "="*60)
            print("🚗 CLEARYFI - СИСТЕМА АВТОМАТИЧЕСКИХ УВЕДОМЛЕНИЙ О ПОГОДЕ")
            print("="*60)
            print("📧 Демон уведомлений: Фоновая отправка прогнозов каждые 6 часов")
            print("🤖 Telegram бот: Обработка команд пользователей")
            print("📁 Рабочая директория:", os.getcwd())
            print("⏹️  Для остановки нажмите Ctrl+C")
            print("="*60)
            print(f"🕐 Время запуска: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*60 + "\n")
            
            # Проверяем окружение
            if not self.check_environment():
                logger.error("❌ Проверка окружения не пройдена. Завершение.")
                return
            
            # Показываем начальный статус
            self.show_status()
            
            # Запускаем демон
            if not self.start_daemon():
                logger.error("❌ Не удалось запустить демон. Продолжаем без него...")
            
            # Запускаем бота
            logger.info("🎯 Запускаем основной процесс бота...")
            bot_exit_code = self.start_bot()
            
            logger.info(f"🤖 Бот завершил работу с кодом: {bot_exit_code}")
            
        except KeyboardInterrupt:
            print("\n" + "="*50)
            print("🛑 Получен сигнал остановки (Ctrl+C)")
            print("="*50)
            self.stop_services()
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в лаунчере: {e}")
            self.stop_services()
        finally:
            # Финальный статус
            print("\n" + "="*50)
            logger.info("ФИНАЛЬНЫЙ СТАТУС:")
            self.show_status()
            print("="*50)

def main():
    """Точка входа"""
    starter = ClearyFiStarter()
    
    # Обработчик Ctrl+C
    def signal_handler(signum, frame):
        print("\n⚠️  Получен сигнал остановки...")
        starter.stop_services()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Запускаем систему
    starter.run()

if __name__ == "__main__":
    main()
