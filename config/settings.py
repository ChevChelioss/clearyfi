import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    
    # Weather APIs
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY',"DEFAULT_COUNTRY" '')
    
    # App settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

settings = Settings()
