from datetime import date, timedelta
from typing import Dict, Tuple, List, Optional
from ..config import config
import logging

logger = logging.getLogger(__name__)

class CalculationService:
    """Сервис для расчета количества намазов"""
    
    def calculate_prayers_from_age(self, birth_date: date, prayer_start_date: date,
                                   gender: str = 'male',
                                   hayd_average_days: float = None,
                                   childbirth_data: List[Dict] = None) -> Dict[str, int]:
        """Расчет намазов от возраста совершеннолетия до начала совершения намазов"""
        adult_age = config.ADULT_AGE_FEMALE if gender == 'female' else config.ADULT_AGE_MALE
        
        # Дата совершеннолетия
        adult_date = birth_date.replace(year=birth_date.year + adult_age)
        
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
        if not hayd_average_days:
            hayd_average_days = 0
            
        excluded_days = 0
        
        # Парсим и сортируем данные о родах
        births = []
        if childbirth_data:
            for birth in childbirth_data:
                try:
                    birth_date = date.fromisoformat(birth['date'])
                    if start_date <= birth_date <= end_date:
                        births.append({
                            'date': birth_date,
                            'nifas_days': min(birth.get('nifas_days', 0), config.NIFAS_MAX_DAYS),
                            'hayd_before': birth.get('hayd_before', hayd_average_days)
                        })
                except Exception as e:
                    logger.warning(f"Ошибка обработки данных о родах: {e}")
                    continue
        
        # Сортируем роды по дате
        births.sort(key=lambda x: x['date'])
        
        # Создаем периоды для расчета
        periods = []
        current_start = start_date
        
        for birth in births:
            # Период до родов
            if current_start < birth['date']:
                periods.append({
                    'start': current_start,
                    'end': birth['date'],
                    'hayd_days': birth['hayd_before'],
                    'type': 'before_birth'
                })
            
            # Период нифаса (дни исключаются полностью)
            nifas_end = birth['date'] + timedelta(days=birth['nifas_days'])
            excluded_days += min(birth['nifas_days'], (end_date - birth['date']).days)
            
            # Следующий период начинается после нифаса
            current_start = min(nifas_end, end_date)
        
        # Период после последних родов до конца
        if current_start < end_date:
            periods.append({
                'start': current_start,
                'end': end_date,
                'hayd_days': hayd_average_days,  # Текущая продолжительность
                'type': 'after_last_birth'
            })
        
        # Если родов не было, используем весь период с текущим хайдом
        if not births:
            periods.append({
                'start': start_date,
                'end': end_date,
                'hayd_days': hayd_average_days,
                'type': 'no_births'
            })
        
        # Рассчитываем дни хайда для каждого периода
        for period in periods:
            period_days = (period['end'] - period['start']).days
            if period_days > 0 and period['hayd_days'] > 0:
                period_months = period_days / 30.0
                hayd_days_in_period = int(period_months * min(period['hayd_days'], config.HAYD_MAX_DAYS))
                excluded_days += min(hayd_days_in_period, period_days)
        
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