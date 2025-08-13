from datetime import datetime
from typing import Optional
from .base import BaseModel

class FastHistory(BaseModel):
    """Модель истории изменений постов"""
    
    def __init__(
        self,
        user_id: int,
        fast_type: str,
        action: str,  # 'add', 'remove', 'set'
        amount: int,
        previous_value: int,
        new_value: int,
        comment: Optional[str] = None
    ):
        super().__init__()
        self.user_id = user_id
        self.fast_type = fast_type
        self.action = action
        self.amount = amount
        self.previous_value = previous_value
        self.new_value = new_value
        self.comment = comment