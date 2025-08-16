import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

def escape_markdown(text):
    special_chars = '\\`*_{}[]()#+-.!|>~^='
    for char in special_chars:
        text = text.replace(char, '\\' + char)
    return text


class Config:
    """Конфигурация приложения"""
    
    # Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Администраторы
    ADMIN_IDS: List[int] = [
        int(id_str.strip()) for id_str in os.getenv("ADMIN_IDS", "").split(",") if id_str.strip()
    ]
    
    # База данных
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/yashel_tracker.db")
    
    # Отладка
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Возрast совершеннолетия в исламе
    ADULT_AGE: int = 12

    # Возраст совершеннолетия в исламе (зависит от пола)
    ADULT_AGE_MALE: int = 12
    ADULT_AGE_FEMALE: int = 9

    # Хайд и нифас (для женщин)
    HAYD_MIN_DAYS: int = 3
    HAYD_MAX_DAYS: int = 10
    NIFAS_MAX_DAYS: int = 40
    
    # Время для ежедневных напоминаний (час в формате 24ч)
    DAILY_REMINDER_HOUR: int = 17  # 20:00
    
    # Виды намазов
    PRAYER_TYPES = {
        'fajr': 'Фаджр',
        'zuhr': 'Зухр', 
        'asr': 'Аср',
        'maghrib': 'Магриб',
        'isha': 'Иша',
        'witr': 'Витр',
        'zuhr_safar': 'Зухр сафар',
        'asr_safar': 'Аср сафар',
        'isha_safar': 'Иша сафар'
    }
    
    # Роли пользователей
    class Roles:
        USER = "user"
        MODERATOR = "moderator"
        ADMIN = "admin"

config = Config()
