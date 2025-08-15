from datetime import datetime
from .base import BaseModel

class HaydInfo(BaseModel):
    """Модель информации о хайд"""
    
    def __init__(
        self,
        user_id: int,
        average_duration: int,
        period_number: int = 0  # 0 - общий, 1 - до первых родов, 2 - после первых и т.д.
    ):
        super().__init__()
        self.user_id = user_id
        self.average_duration = average_duration
        self.period_number = period_number