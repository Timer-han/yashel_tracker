from datetime import datetime, date
from typing import Optional, Dict, List
from .base import BaseModel
import json

class User(BaseModel):
    """Модель пользователя"""
    
    def __init__(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        gender: Optional[str] = None,
        birth_date: Optional[date] = None,
        city: Optional[str] = None,
        role: str = "user",
        is_registered: bool = False,
        prayer_start_date: Optional[date] = None,
        adult_date: Optional[date] = None,
        fasting_missed_days: int = 0,
        fasting_completed_days: int = 0,
        hayd_average_days: Optional[float] = None,
        childbirth_count: int = -1,
        childbirth_data: Optional[str] = None,
        daily_notifications_enabled: int = 1  # Новое поле: 1 - включены, 0 - отключены
    ):
        super().__init__()
        self.telegram_id = telegram_id
        self.username = username
        self.gender = gender
        self.birth_date = birth_date
        self.city = city
        self.role = role
        self.is_registered = is_registered
        self.prayer_start_date = prayer_start_date
        self.adult_date = adult_date
        self.last_activity = datetime.now()
        
        # Поля для постов
        self.fasting_missed_days = fasting_missed_days
        self.fasting_completed_days = fasting_completed_days
        
        # Поля для женщин (хайд/нифас)
        self.hayd_average_days = hayd_average_days
        self.childbirth_count = childbirth_count
        self.childbirth_data = childbirth_data  # JSON строка с данными о родах
        
        # Настройки уведомлений
        self.daily_notifications_enabled = daily_notifications_enabled
    
    @property
    def fasting_remaining_days(self) -> int:
        """Оставшиеся дни постов"""
        return max(0, self.fasting_missed_days - self.fasting_completed_days)
    
    @property
    def notifications_enabled(self) -> bool:
        """Включены ли ежедневные уведомления"""
        return bool(self.daily_notifications_enabled)
    
    def get_childbirth_info(self) -> List[Dict]:
        """Получение информации о родах из JSON"""
        if not self.childbirth_data:
            return []
        try:
            return json.loads(self.childbirth_data)
        except:
            return []
    
    def set_childbirth_info(self, info: List[Dict]):
        """Сохранение информации о родах в JSON"""
        self.childbirth_data = json.dumps(info)
        
    @property
    def display_name(self) -> str:
        """Отображаемое имя пользователя"""
        if self.username:
            return self.username
        elif self.gender == 'male':
            return 'брат'
        elif self.gender == 'female':
            return 'сестра' 
        else:
            return 'пользователь'