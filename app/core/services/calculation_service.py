from datetime import date, timedelta
from typing import Dict, Tuple, List
from ..config import config
import logging

logger = logging.getLogger(__name__)


class CalculationService:
    """Сервис для расчета количества намазов"""
    
    def calculate_prayers_from_age(self, birth_date: date, adult_age: int = None,
                               prayer_start_date: date = None, user=None) -> Dict[str, int]:
        """Расчет намазов от возраста совершеннолетия до начала совершения намазов"""
        if adult_age is None:
            adult_age = config.ADULT_AGE_MALE  # По умолчанию для мужчин
            if user and user.gender == 'female':
                adult_age = config.ADULT_AGE_FEMALE
        
        # Дата совершеннолетия
        adult_date = birth_date.replace(year=birth_date.year + adult_age)
        
        # Если дата начала намазов не указана, используем сегодняшнюю дату
        if prayer_start_date is None:
            prayer_start_date = date.today()
        
        # Для женщин используем специальный расчет
        if user and user.gender == 'female':
            return self.calculate_prayers_for_female(
                adult_date, prayer_start_date, 
                user.hyde_periods, user.nifas_lengths, user.childbirths
            )
        else:
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
    
    def calculate_prayers_for_female(self, start_date: date, end_date: date, 
                                 hyde_periods: List[int], nifas_lengths: List[int],
                                 childbirths: List[date]) -> Dict[str, int]:
        """Расчет намазов для женщин с учетом хайда и нифаса"""
        if start_date >= end_date:
            return {prayer_type: 0 for prayer_type in config.PRAYER_TYPES.keys()}
        
        total_days = (end_date - start_date).days
        
        # Рассчитываем дни хайда
        months_count = total_days // 30  # Приблизительное количество месяцев
        avg_hyde_days = sum(hyde_periods) / len(hyde_periods) if hyde_periods else 0
        total_hyde_days = months_count * avg_hyde_days
        
        # Рассчитываем дни нифаса
        total_nifas_days = 0
        for i, childbirth_date in enumerate(childbirths):
            if start_date <= childbirth_date <= end_date:
                # Находим соответствующую длительность нифаса
                if i < len(nifas_lengths):
                    total_nifas_days += nifas_lengths[i]
        
        # Количество дней для намазов
        prayer_days = total_days - total_hyde_days - total_nifas_days
        prayer_days = max(0, prayer_days)  # Не может быть отрицательным
        
        # Базовые намазы
        prayers = {
            'fajr': int(prayer_days),
            'zuhr': int(prayer_days),
            'asr': int(prayer_days),
            'maghrib': int(prayer_days),
            'isha': int(prayer_days),
            'witr': int(prayer_days),
            'zuhr_safar': 0,
            'asr_safar': 0,
            'isha_safar': 0
        }
        
        return prayers

    def calculate_fasts_between_dates(self, start_date: date, end_date: date) -> int:
        """Расчет количества пропущенных постов Рамадана"""
        if start_date >= end_date:
            return 0
        
        # Приблизительно 30 дней Рамадана в году
        years = (end_date.year - start_date.year)
        if years == 0:
            return 0
        
        return years * 30  # 30 дней Рамадана за каждый год

