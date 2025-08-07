from typing import List, Dict, Any, Optional
from aiogram import Bot

from ..database.repositories.user_repository import UserRepository
from .calculation_service import CalculationService
from ..config import config

class BroadcastService:
    """Сервис для рассылки сообщений"""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.calc_service = CalculationService()
    
    async def send_broadcast(self, message_text: str, filters: Dict[str, Any] = None, 
                           photo: str = None, video: str = None) -> Dict[str, int]:
        """Отправка рассылки с фильтрами"""
        
        # Получаем пользователей по фильтрам
        users = await self._get_filtered_users(filters or {})
        
        bot = Bot(token=config.BOT_TOKEN)
        sent_count = 0
        error_count = 0
        
        try:
            for user in users:
                try:
                    if photo:
                        await bot.send_photo(
                            chat_id=user.telegram_id,
                            photo=photo,
                            caption=message_text,
                            parse_mode="Markdown"
                        )
                    elif video:
                        await bot.send_video(
                            chat_id=user.telegram_id,
                            video=video,
                            caption=message_text,
                            parse_mode="Markdown"
                        )
                    else:
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=message_text,
                            parse_mode="Markdown"
                        )
                    
                    sent_count += 1
                    
                except Exception as e:
                    error_count += 1
                    continue
        
        finally:
            await bot.session.close()
        
        return {
            'sent': sent_count,
            'errors': error_count,
            'total_users': len(users)
        }
    
    async def _get_filtered_users(self, filters: Dict[str, Any]) -> List:
        """Получение пользователей по фильтрам"""
        
        # Базовая фильтрация
        gender = filters.get('gender')
        city = filters.get('city')
        
        users = await self.user_repo.get_users_by_filters(
            gender=gender,
            city=city
        )
        
        # Фильтрация по возрасту
        age_filter = filters.get('age_range')
        if age_filter and users:
            min_age, max_age = age_filter
            filtered_users = []
            
            for user in users:
                if user.birth_date:
                    age = self.calc_service.calculate_age(user.birth_date)
                    if min_age <= age <= max_age:
                        filtered_users.append(user)
            
            users = filtered_users
        
        return users
