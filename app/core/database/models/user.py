from datetime import datetime, date
from typing import Optional, List
import json
from .base import BaseModel

class User(BaseModel):
    """Модель пользователя"""
    
    def __init__(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        gender: Optional[str] = None,
        childbirth_count: Optional[int] = 0,
        childbirths: Optional[List[date]] = None,
        hyde_periods: Optional[List[int]] = None,
        nifas_lengths: Optional[List[int]] = None,
        birth_date: Optional[date] = None,
        city: Optional[str] = None,
        role: str = "user",
        is_registered: bool = False,
        prayer_start_date: Optional[date] = None,
        adult_date: Optional[date] = None
    ):
        super().__init__()
        self.telegram_id = telegram_id
        self.username = username
        self.gender = gender
        self.childbirth_count = childbirth_count or 0
        self.childbirths = childbirths or []
        self.hyde_periods = hyde_periods or []
        self.nifas_lengths = nifas_lengths or []
        self.birth_date = birth_date
        self.city = city
        self.role = role
        self.is_registered = is_registered
        self.prayer_start_date = prayer_start_date
        self.adult_date = adult_date
        self.last_activity = datetime.now()
    
    def childbirths_to_json(self) -> str:
        """Преобразование дат родов в JSON"""
        if not self.childbirths:
            return "[]"
        return json.dumps([date.isoformat() for date in self.childbirths])
    
    def hyde_periods_to_json(self) -> str:
        """Преобразование периодов хайда в JSON"""
        return json.dumps(self.hyde_periods or [])
    
    def nifas_lengths_to_json(self) -> str:
        """Преобразование длительности нифаса в JSON"""
        return json.dumps(self.nifas_lengths or [])
    
    @classmethod
    def from_json_childbirths(cls, json_str: str) -> List[date]:
        """Восстановление дат родов из JSON"""
        if not json_str:
            return []
        try:
            dates_str = json.loads(json_str)
            return [datetime.fromisoformat(date_str).date() for date_str in dates_str]
        except:
            return []
    
    @classmethod
    def from_json_periods(cls, json_str: str) -> List[int]:
        """Восстановление периодов из JSON"""
        if not json_str:
            return []
        try:
            return json.loads(json_str)
        except:
            return []
        

    # Муть пошла
    @classmethod
    def childbirths_to_json_static(cls, childbirths: List[date]) -> str:
        """Статический метод для преобразования дат родов в JSON"""
        if not childbirths:
            return "[]"
        return json.dumps([date.isoformat() for date in childbirths])

    @classmethod  
    def hyde_periods_to_json_static(cls, periods: List[int]) -> str:
        """Статический метод для преобразования периодов хайда в JSON"""
        return json.dumps(periods or [])

    @classmethod
    def nifas_lengths_to_json_static(cls, lengths: List[int]) -> str:
        """Статический метод для преобразования длительности нифаса в JSON"""
        return json.dumps(lengths or [])