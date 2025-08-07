from datetime import datetime
from .base import BaseModel

class Admin(BaseModel):
    """Модель администратора/модератора"""
    
    def __init__(
        self,
        telegram_id: int,
        role: str,  # 'admin' or 'moderator'
        added_by: int,
        is_active: bool = True
    ):
        super().__init__()
        self.telegram_id = telegram_id
        self.role = role
        self.added_by = added_by
        self.is_active = is_active