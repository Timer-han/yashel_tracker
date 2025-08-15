import logging
from aiogram import Bot
from typing import List

from ..core.config import config
from ..core.database.repositories.user_repository import UserRepository
from ..core.services.prayer_service import PrayerService

logger = logging.getLogger(__name__)

async def send_daily_reminders():
    """Отправка ежедневных напоминаний со статистикой"""
    bot = Bot(token=config.BOT_TOKEN)
    user_repo = UserRepository()
    prayer_service = PrayerService()
    
    try:
        # Получаем всех зарегистрированных пользователей
        users = await user_repo.get_all_registered_users()
        
        for user in users:
            try:
                stats = await prayer_service.get_user_statistics(user.telegram_id)
                
                if stats['total_remaining'] > 0:
                    message_text = (
                        f"🌙 Доброй ночи, {user.full_name or user.first_name}!\n\n"
                        f"📊 Ваша статистика на сегодня:\n"
                        f"⏳ Осталось восполнить: **{stats['total_remaining']}** намазов\n\n"
                        "🤲 Не забывайте о восполнении намазов каждый день.\n"
                        "Пусть Аллах облегчит вам этот путь!"
                    )
                    
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=message_text,
                        parse_mode="Markdown"
                    )
                
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления пользователю {user.telegram_id}: {e}")
                continue
        
        logger.info(f"Отправлены ежедневные напоминания для {len(users)} пользователей")
        
    except Exception as e:
        logger.error(f"Ошибка в задаче ежедневных напоминаний: {e}")
    finally:
        await bot.session.close()
