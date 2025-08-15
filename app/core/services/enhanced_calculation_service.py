from datetime import date, timedelta
from typing import Dict, List, Tuple, Optional
from ..config import config
from ..database.models.hayd import HaydInfo
from ..database.models.nifas import NifasInfo
import logging

logger = logging.getLogger(__name__)

class EnhancedCalculationService:
    """Расширенный сервис для расчета намазов и постов с учетом женских периодов"""
    
    def get_adult_age_by_gender(self, gender: str) -> int:
        """Получение возраста совершеннолетия по полу"""
        if gender == 'female':
            return config.ADULT_AGE_FEMALE
        return config.ADULT_AGE_MALE
    
    def calculate_prayers_with_female_periods(
        self, 
        start_date: date, 
        end_date: date,
        gender: str,
        hayd_info_list: List[HaydInfo],
        nifas_info_list: List[NifasInfo]
    ) -> Dict[str, int]:
        """Расчет намазов с учетом женских периодов"""
        
        # Если мужчина, используем стандартный расчет
        if gender != 'female':
            return self.calculate_prayers_between_dates(start_date, end_date)
        
        # Общее количество дней
        total_days = (end_date - start_date).days
        
        # Вычитаем дни хайд
        hayd_days = self._calculate_hayd_days(
            start_date, end_date, hayd_info_list, nifas_info_list
        )
        
        # Вычитаем дни нифас
        nifas_days = self._calculate_nifas_days(
            start_date, end_date, nifas_info_list
        )
        
        # Дни для намазов
        prayer_days = total_days - hayd_days - nifas_days
        prayer_days = max(0, prayer_days)
        
        return {
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
    
    def calculate_fasts_with_female_periods(
        self,
        start_date: date,
        end_date: date,
        gender: str,
        hayd_info_list: List[HaydInfo],
        nifas_info_list: List[NifasInfo]
    ) -> Dict[str, int]:
        """Расчет постов с учетом женских периодов"""
        
        fasts = {}
        current_date = start_date
        
        while current_date <= end_date:
            year = current_date.year
            
            # Рамадан (примерно 30 дней)
            ramadan_days = self._calculate_ramadan_days(year, start_date, end_date)
            
            if gender == 'female':
                # Для женщин посты во время хайд/нифас нужно восполнять 1:1
                # Они добавляются к общему количеству пропущенных
                ramadan_key = f"ramadan_{year}"
                fasts[ramadan_key] = ramadan_days
            else:
                ramadan_key = f"ramadan_{year}"
                fasts[ramadan_key] = ramadan_days
            
            # Переход к следующему году
            current_date = date(year + 1, 1, 1)
        
        return fasts
    
    def _calculate_hayd_days(
        self,
        start_date: date,
        end_date: date,
        hayd_info_list: List[HaydInfo],
        nifas_info_list: List[NifasInfo]
    ) -> int:
        """Подсчет дней хайд в периоде"""
        
        if not hayd_info_list:
            return 0
        
        total_hayd_days = 0
        
        # Сортируем нифас по дате для определения периодов
        sorted_nifas = sorted(nifas_info_list, key=lambda x: x.childbirth_date)
        
        # Определяем периоды между родами
        periods = []
        period_start = start_date
        
        for i, nifas in enumerate(sorted_nifas):
            if nifas.childbirth_date > start_date and nifas.childbirth_date < end_date:
                # Период до родов
                periods.append((period_start, nifas.childbirth_date, i))
                # Пропускаем период нифас
                period_start = nifas.childbirth_date + timedelta(days=nifas.nifas_duration)
        
        # Последний период до конца
        if period_start < end_date:
            periods.append((period_start, end_date, len(sorted_nifas)))
        
        # Считаем хайд для каждого периода
        for period_start, period_end, period_number in periods:
            # Находим соответствующую информацию о хайд
            hayd_info = next(
                (h for h in hayd_info_list if h.period_number == period_number),
                hayd_info_list[0] if hayd_info_list else None
            )
            
            if hayd_info:
                # Количество месяцев в периоде
                months = self._calculate_months_between(period_start, period_end)
                # Дни хайд = количество месяцев * средняя продолжительность
                total_hayd_days += months * hayd_info.average_duration
        
        return int(total_hayd_days)
    
    def _calculate_nifas_days(
        self,
        start_date: date,
        end_date: date,
        nifas_info_list: List[NifasInfo]
    ) -> int:
        """Подсчет дней нифас в периоде"""
        
        total_nifas_days = 0
        
        for nifas in nifas_info_list:
            # Проверяем, попадает ли нифас в наш период
            nifas_start = nifas.childbirth_date
            nifas_end = nifas_start + timedelta(days=nifas.nifas_duration)
            
            # Определяем пересечение периодов
            overlap_start = max(start_date, nifas_start)
            overlap_end = min(end_date, nifas_end)
            
            if overlap_start < overlap_end:
                overlap_days = (overlap_end - overlap_start).days
                total_nifas_days += overlap_days
        
        return total_nifas_days
    
    def _calculate_months_between(self, start_date: date, end_date: date) -> float:
        """Подсчет количества месяцев между датами"""
        months = (end_date.year - start_date.year) * 12
        months += end_date.month - start_date.month
        months += end_date.day / 30.0 - start_date.day / 30.0
        return max(0, months)
    
    def _calculate_ramadan_days(self, year: int, start_date: date, end_date: date) -> int:
        """Примерный расчет дней Рамадана в периоде"""
        # Упрощенный расчет - предполагаем 30 дней Рамадана в году
        # В реальности нужно использовать исламский календарь
        
        # Проверяем, попадает ли год в наш период
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        
        if year_end < start_date or year_start > end_date:
            return 0
        
        # Если год полностью в периоде, возвращаем 30 дней
        if year_start >= start_date and year_end <= end_date:
            return 30
        
        # Частичное попадание - упрощенно возвращаем пропорциональную часть
        overlap_start = max(start_date, year_start)
        overlap_end = min(end_date, year_end)
        overlap_days = (overlap_end - overlap_start).days
        
        # Примерно 30 дней Рамадана на 365 дней года
        return int(overlap_days * 30 / 365)
    
    def calculate_prayers_between_dates(self, start_date: date, end_date: date) -> Dict[str, int]:
        """Базовый расчет количества намазов между двумя датами"""
        if start_date >= end_date:
            return {prayer_type: 0 for prayer_type in config.PRAYER_TYPES.keys()}
        
        days_count = (end_date - start_date).days
        
        return {
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
    
    def calculate_age(self, birth_date: date, reference_date: date = None) -> int:
        """Расчет возраста"""
        if reference_date is None:
            reference_date = date.today()
        
        age = reference_date.year - birth_date.year
        if reference_date.month < birth_date.month or \
           (reference_date.month == birth_date.month and reference_date.day < birth_date.day):
            age -= 1
        
        return age