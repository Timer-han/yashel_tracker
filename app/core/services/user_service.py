from typing import Optional
from datetime import date
from ..database.repositories.user_repository import UserRepository
from ..database.models.user import User
from ..config import config

class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    async def complete_registration(self, telegram_id: int, 
                                    gender: str = None, 
                                    birth_date: date = None,
                                    city: str = None, 
                                    prayer_start_date: date = None,
                                    adult_date: date = None,
                                    hayd_average_days: float = None,
                                    childbirth_count: int = 0,
                                    childbirth_data: str = None) -> bool:
        """Завершение регистрации пользователя"""
        return await self.user_repo.update_user(
            telegram_id=telegram_id,
            gender=gender,
            birth_date=birth_date,
            city=city,
            prayer_start_date=prayer_start_date,
            adult_date=adult_date,
            is_registered=True,
            hayd_average_days=hayd_average_days,
            childbirth_count=childbirth_count,
            childbirth_data=childbirth_data
            # daily_notifications_enabled остается дефолтным (1)
        )

    async def get_or_create_user(self, telegram_id: int, username: str = None) -> User:
        """Получение или создание пользователя"""
        user = await self.user_repo.get_user_by_telegram_id(telegram_id)
        
        if not user:
            # Проверяем, является ли пользователь админом
            role = config.Roles.ADMIN if telegram_id in config.ADMIN_IDS else config.Roles.USER
            
            user = User(
                telegram_id=telegram_id,
                username=username,
                role=role,
                daily_notifications_enabled=1  # По умолчанию включены
            )
            await self.user_repo.create_user(user)
        
        return user
    
    async def update_last_activity(self, telegram_id: int) -> bool:
        """Обновление времени последней активности"""
        from datetime import datetime
        return await self.user_repo.update_user(
            telegram_id=telegram_id,
            last_activity=datetime.now()
        )
    
    async def toggle_notifications(self, telegram_id: int) -> bool:
        """Переключение настройки уведомлений"""
        user = await self.get_or_create_user(telegram_id)
        new_state = 0 if user.notifications_enabled else 1
        
        return await self.user_repo.update_user(
            telegram_id=telegram_id,
            daily_notifications_enabled=new_state
        )
    
    async def set_notifications(self, telegram_id: int, enabled: bool) -> bool:
        """Установка настройки уведомлений"""
        return await self.user_repo.update_user(
            telegram_id=telegram_id,
            daily_notifications_enabled=1 if enabled else 0
        )