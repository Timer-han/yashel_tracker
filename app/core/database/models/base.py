from datetime import datetime
from typing import Dict, Any

class BaseModel:
    """Базовая модель для всех сущностей"""
    
    def __init__(self):
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {key: value for key, value in self.__dict__.items()}
    
    def update_timestamp(self):
        """Обновление времени изменения"""
        self.updated_at = datetime.now()