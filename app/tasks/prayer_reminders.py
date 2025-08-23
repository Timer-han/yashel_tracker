import logging
from aiogram import Bot

from ..core.config import config, escape_markdown
from ..core.database.repositories.user_repository import UserRepository
from ..core.services.prayer_service import PrayerService
from ..bot.utils.text_messages import text_message

logger = logging.getLogger(__name__)

async def send_evening_reminders():
    """Отправка вечерних напоминаний о восполнении намазов"""
    bot = Bot(token=config.BOT_TOKEN)
    user_repo = UserRepository()
    prayer_service = PrayerService()
    
    try:
        users = await user_repo.get_all_registered_users()
        
        reminder_messages = text_message.reminder_messages
        
        import random
        message_text = escape_markdown(random.choice(reminder_messages), ".?!-()[]")
        
        sent_count = 0
        for user in users:
            try:
                stats = await prayer_service.get_user_statistics(user.telegram_id)
                
                if stats['total_remaining'] > 0:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=message_text,
                        parse_mode="MarkdownV2"
                    )
                    sent_count += 1
                
            except Exception as e:
                logger.error(f"Ошибка отправки напоминания пользователю {user.telegram_id}: {e}")
                continue
        
        logger.info(f"Отправлены вечерние напоминания для {sent_count} пользователей")
        
    except Exception as e:
        logger.error(f"Ошибка в задаче вечерних напоминаний: {e}")
    finally:
        await bot.session.close()
