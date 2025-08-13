from typing import Optional
from datetime import date
from ..database.repositories.user_repository import UserRepository
from ..database.models.user import User
from ..config import config

class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    async def get_or_create_user(self, telegram_id: int, username: str = None) -> User:
        """Получение или создание пользователя"""
        user = await self.user_repo.get_user_by_telegram_id(telegram_id)
        
        if not user:
            # Проверяем, является ли пользователь админом
            role = config.Roles.ADMIN if telegram_id in config.ADMIN_IDS else config.Roles.USER
            
            user = User(
                telegram_id=telegram_id,
                username=username,
                role=role
            )
            await self.user_repo.create_user(user)
        
        return user
    
    async def complete_registration(self, telegram_id: int, gender: str = None,
                                birth_date: date = None, city: str = None,
                                childbirth_count: int = 0, childbirths: list = None,
                                hyde_periods: list = None, nifas_lengths: list = None) -> bool:
        """Завершение регистрации пользователя"""
        return await self.user_repo.update_user(
            telegram_id=telegram_id,
            gender=gender,
            birth_date=birth_date,
            city=city,
            childbirth_count=childbirth_count,
            childbirths=User.childbirths_to_json_static(childbirths or []),
            hyde_periods=User.hyde_periods_to_json_static(hyde_periods or []),
            nifas_lengths=User.nifas_lengths_to_json_static(nifas_lengths or []),
            is_registered=True
        )

    
    async def update_last_activity(self, telegram_id: int) -> bool:
        """Обновление времени последней активности"""
        return await self.user_repo.update_user(telegram_id=telegram_id)