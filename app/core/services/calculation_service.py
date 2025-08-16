from datetime import date, timedelta
from typing import Dict, Tuple, List, Optional
from ..config import config
import logging

logger = logging.getLogger(__name__)

class CalculationService:
    """Сервис для расчета количества намазов"""
    
    def calculate_prayers_from_age(self, birth_date: date, gender: str = 'male',
                                   prayer_start_date: date = None,
                                   hayd_average_days: float = None,
                                   childbirth_data: List[Dict] = None) -> Dict[str, int]:
        """Расчет намазов от возраста совершеннолетия до начала совершения намазов"""
        adult_age = config.ADULT_AGE_FEMALE if gender == 'female' else config.ADULT_AGE_MALE
        
        # Дата совершеннолетия
        adult_date = birth_date.replace(year=birth_date.year + adult_age)
        
        # Если дата начала намазов не указана, используем сегодняшнюю дату
        if prayer_start_date is None:
            prayer_start_date = date.today()
        
        return self.calculate_prayers_between_dates(
            adult_date, prayer_start_date, gender, 
            hayd_average_days, childbirth_data
        )
    
    def calculate_prayers_between_dates(self, start_date: date, end_date: date,
                                        gender: str = 'male',
                                        hayd_average_days: float = None,
                                        childbirth_data: List[Dict] = None) -> Dict[str, int]:
        """Расчет количества намазов между двумя датами с учетом пола"""
        if start_date >= end_date:
            return {prayer_type: 0 for prayer_type in config.PRAYER_TYPES.keys()}
        
        # Количество дней
        total_days = (end_date - start_date).days
        
        # Для женщин вычитаем дни хайда и нифаса
        if gender == 'female':
            excluded_days = self._calculate_excluded_days_for_women(
                start_date, end_date, hayd_average_days, childbirth_data
            )
            prayer_days = max(0, total_days - excluded_days)
        else:
            prayer_days = total_days
        
        # Базовые намазы (5 в день + витр)
        prayers = {
            'fajr': prayer_days,
            'zuhr': prayer_days,
            'asr': prayer_days,
            'maghrib': prayer_days,
            'isha': prayer_days,
            'witr': prayer_days,
            'zuhr_safar': 0,
            'asr_safar': 0,
            'isha_safar': 0
        }
        
        return prayers
    
    def _calculate_excluded_days_for_women(self, start_date: date, end_date: date,
                                           hayd_average_days: float = None,
                                           childbirth_data: List[Dict] = None) -> int:
        """Вычисление дней, когда женщина не читает намаз"""
        excluded_days = 0
        
        # Расчет дней хайда
        if hayd_average_days and hayd_average_days > 0:
            total_months = (end_date - start_date).days / 30
            hayd_total = int(total_months * min(hayd_average_days, config.HAYD_MAX_DAYS))
            excluded_days += hayd_total
        
        # Расчет дней нифаса
        if childbirth_data:
            for birth in childbirth_data:
                try:
                    birth_date = date.fromisoformat(birth['date'])
                    if start_date <= birth_date <= end_date:
                        nifas_days = min(birth.get('nifas_days', 0), config.NIFAS_MAX_DAYS)
                        excluded_days += nifas_days
                        
                        # Корректируем хайд после родов
                        if 'hayd_after' in birth:
                            # Период после родов до конца расчетного периода
                            days_after_birth = (end_date - birth_date).days
                            months_after = days_after_birth / 30
                            # Новый хайд после родов
                            new_hayd = int(months_after * min(birth['hayd_after'], config.HAYD_MAX_DAYS))
                            # Вычитаем старый хайд за этот период и добавляем новый
                            old_hayd = int(months_after * min(hayd_average_days or 0, config.HAYD_MAX_DAYS))
                            excluded_days = excluded_days - old_hayd + new_hayd
                except:
                    continue
        
        return min(excluded_days, (end_date - start_date).days)
    
    def calculate_age(self, birth_date: date, reference_date: date = None) -> int:
        """Расчет возраста"""
        if reference_date is None:
            reference_date = date.today()
        
        age = reference_date.year - birth_date.year
        if reference_date.month < birth_date.month or \
           (reference_date.month == birth_date.month and reference_date.day < birth_date.day):
            age -= 1
        
        return age
    
    def calculate_prayers_from_dates(self, adult_date: date, prayer_start_date: date,
                                     gender: str = 'male',
                                     hayd_average_days: float = None,
                                     childbirth_data: List[Dict] = None) -> Dict[str, int]:
        """Расчет намазов между датой совершеннолетия и началом намазов"""
        return self.calculate_prayers_between_dates(
            adult_date, prayer_start_date, gender, 
            hayd_average_days, childbirth_data
        )