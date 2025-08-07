from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from ...core.services.user_service import UserService

class AuthMiddleware(BaseMiddleware):
    """Middleware для аутентификации пользователей"""
    
    def __init__(self):
        self.user_service = UserService()
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        
        # Обновляем активность пользователя
        await self.user_service.update_last_activity(event.from_user.id)
        
        return await handler(event, data)
