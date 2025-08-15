from datetime import datetime, date
from typing import Optional
from .base import BaseModel

class User(BaseModel):
    """Модель пользователя"""
    
    def __init__(
        self,
        telegram_id: int,
        username: Optional[str] = None,

        full_name: Optional[str] = None,
        gender: Optional[str] = None,
        birth_date: Optional[date] = None,
        city: Optional[str] = None,
        role: str = "user",
        is_registered: bool = False,
        prayer_start_date: Optional[date] = None,
        adult_date: Optional[date] = None,
        fasting_start_date: Optional[date] = None,
        has_childbirth: bool = False,
        childbirth_count: int = 0
    ):
        super().__init__()
        self.telegram_id = telegram_id
        self.username = username

        self.full_name = full_name
        self.gender = gender
        self.birth_date = birth_date
        self.city = city
        self.role = role
        self.is_registered = is_registered
        self.prayer_start_date = prayer_start_date
        self.adult_date = adult_date
        self.last_activity = datetime.now()
        self.fasting_start_date = fasting_start_date
        self.has_childbirth = has_childbirth
        self.childbirth_count = childbirth_count
        self.last_activity = datetime.now()