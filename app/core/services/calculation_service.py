from datetime import date, timedelta
from typing import Dict, Tuple
from ..config import config

class CalculationService:
    """Сервис для расчета количества намазов"""
    
    def calculate_prayers_from_age(self, birth_date: date, adult_age: int = None,
                                   prayer_start_date: date = None) -> Dict[str, int]:
        """Расчет намазов от возраста совершеннолетия до начала совершения намазов"""
        if adult_age is None:
            adult_age = config.ADULT_AGE
        
        # Дата совершеннолетия
        adult_date = birth_date.replace(year=birth_date.year + adult_age)
        
        # Если дата начала намазов не указана, используем сегодняшнюю дату
        if prayer_start_date is None:
            prayer_start_date = date.today()
        
        return self.calculate_prayers_between_dates(adult_date, prayer_start_date)
    
    def calculate_prayers_from_dates(self, adult_date: date, 
                                     prayer_start_date: date) -> Dict[str, int]:
        """Расчет намазов между двумя датами (совершеннолетие и начало намазов)"""
        return self.calculate_prayers_between_dates(adult_date, prayer_start_date)
    
    def calculate_prayers_between_dates(self, start_date: date, end_date: date) -> Dict[str, int]:
        """Расчет количества намазов между двумя датами"""
        if start_date >= end_date:
            return {prayer_type: 0 for prayer_type in config.PRAYER_TYPES.keys()}
        
        # Количество дней
        days_count = (end_date - start_date).days
        
        # Базовые намазы (5 в день + витр)
        prayers = {
            'fajr': days_count,
            'zuhr': days_count, 
            'asr': days_count,
            'maghrib': days_count,
            'isha': days_count,
            'witr': days_count,
            'zuhr_safar': 0,
            'asr_safar': 0,
            'isha_safar': 0
        }
        
        return prayers
    
    def calculate_age(self, birth_date: date, reference_date: date = None) -> int:
        """Расчет возраста"""
        if reference_date is None:
            reference_date = date.today()
        
        age = reference_date.year - birth_date.year
        if reference_date.month < birth_date.month or \
           (reference_date.month == birth_date.month and reference_date.day < birth_date.day):
            age -= 1
        
        return age
