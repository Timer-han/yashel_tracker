from datetime import datetime
from typing import Optional
from .base import BaseModel

class Fast(BaseModel):
    """Модель счетчика постов пользователя"""
    
    def __init__(
        self,
        user_id: int,
        fast_type: str,
        total_missed: int = 0,
        completed: int = 0
    ):
        super().__init__()
        self.user_id = user_id
        self.fast_type = fast_type
        self.total_missed = total_missed
        self.completed = completed
    
    @property
    def remaining(self) -> int:
        """Оставшиеся посты"""
        return max(0, self.total_missed - self.completed)