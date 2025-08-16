from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from ...core.services.user_service import UserService

class AuthMiddleware(BaseMiddleware):
    """Middleware для аутентификации пользователей"""
    
    def __init__(self):
        self.user_service = UserService()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        # Получаем пользователя из события
        user = None
        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user
        
        if user:
            # Обновляем активность пользователя
            try:
                await self.user_service.update_last_activity(user.id)
            except Exception as e:
                # Логируем ошибку, но не прерываем выполнение
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Ошибка обновления активности пользователя {user.id}: {e}")
        
        return await handler(event, data)