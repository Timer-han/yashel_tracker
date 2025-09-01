import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from ..core.config import config
from .daily_notifications import send_daily_reminders, send_evening_reminders
# from .prayer_reminders import send_evening_reminders, send_daily_reminders

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def start_scheduler():
    """Запуск планировщика задач"""
    
    # Ежедневные напоминания в указанное время
    scheduler.add_job(
        send_evening_reminders,
        # CronTrigger(hour=13, minute=25,second=50),
        CronTrigger(hour=17, minute=0,second=0),
        id='evening_reminders'
    )
    
    # Дополнительная задача для отправки ежедневной статистики
    scheduler.add_job(
        send_daily_reminders,
        CronTrigger(hour=19, minute=0, second=0),  # 22:00 ежедневно
        id='daily_statistics'
    )
    
    scheduler.start()
    logger.info("📅 Планировщик задач запущен")
