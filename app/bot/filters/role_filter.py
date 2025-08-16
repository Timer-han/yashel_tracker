from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from typing import Union

from ...core.database.repositories.user_repository import UserRepository
from ...core.database.repositories.admin_repository import AdminRepository
from ...core.config import config

class RoleFilter(BaseFilter):
    """Фильтр для проверки роли пользователя"""
    
    def __init__(self, roles: Union[str, list]):
        self.roles = roles if isinstance(roles, list) else [roles]
        self.user_repo = UserRepository()
        self.admin_repo = AdminRepository()
    
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        user_id = event.from_user.id
        
        # Проверяем базовую роль пользователя
        user = await self.user_repo.get_user_by_telegram_id(user_id)
        if not user:
            return config.Roles.USER in self.roles
        
        # Проверяем роль администратора
        if user.role in [config.Roles.ADMIN, config.Roles.MODERATOR]:
            admin = await self.admin_repo.get_admin(user_id)
            if admin and admin.is_active:
                return admin.role in self.roles
        
        return user.role in self.roles

# Готовые фильтры
admin_filter = RoleFilter(config.Roles.ADMIN)
moderator_filter = RoleFilter([config.Roles.ADMIN, config.Roles.MODERATOR])
user_filter = RoleFilter([config.Roles.USER, config.Roles.MODERATOR, config.Roles.ADMIN])
