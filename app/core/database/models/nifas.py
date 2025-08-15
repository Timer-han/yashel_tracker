from datetime import date
from .base import BaseModel

class NifasInfo(BaseModel):
    """Модель информации о нифас (послеродовой период)"""
    
    def __init__(
        self,
        user_id: int,
        childbirth_number: int,
        childbirth_date: date,
        nifas_duration: int
    ):
        super().__init__()
        self.user_id = user_id
        self.childbirth_number = childbirth_number
        self.childbirth_date = childbirth_date
        self.nifas_duration = nifas_duration