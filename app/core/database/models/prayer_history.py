from datetime import datetime
from typing import Optional
from .base import BaseModel

class PrayerHistory(BaseModel):
    """Модель истории изменений намазов"""
    
    def __init__(
        self,
        user_id: int,
        prayer_type: str,
        action: str,  # 'add', 'remove', 'set'
        amount: int,
        previous_value: int,
        new_value: int,
        comment: Optional[str] = None
    ):
        super().__init__()
        self.user_id = user_id
        self.prayer_type = prayer_type
        self.action = action
        self.amount = amount
        self.previous_value = previous_value
        self.new_value = new_value
        self.comment = comment