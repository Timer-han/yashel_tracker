from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from ..config import config
import json
import logging

logger = logging.getLogger(__name__)

class WomenCalculationService:
    """Сервис для расчета намазов и постов с учетом хайда/нифаса"""
    
    def calculate_missed_fasts_detailed(self, birth_date: date, adult_date: date,
                                        fast_start_date: date, gender: str,
                                        hayd_average_days: float = None,
                                        childbirth_data: List[Dict] = None) -> Dict[str, int]:
        """Детальный расчет пропущенных постов"""
        
        if fast_start_date <= adult_date:
            return {'total': 0, 'ramadan_count': 0, 'hayd_days': 0, 'nifas_days': 0}
        
        # Считаем количество Рамаданов между датами
        start_year = adult_date.year
        end_year = fast_start_date.year
        
        ramadan_count = 0
        total_fast_days = 0
        total_hayd_days = 0
        total_nifas_days = 0
        
        # Примерные даты Рамадана (сдвигается на ~11 дней каждый год)
        ramadan_dates = self._get_ramadan_dates(start_year, end_year)
        
        # Парсим и сортируем данные о родах
        births = []
        if childbirth_data:
            for birth in childbirth_data:
                try:
                    birth_date_obj = date.fromisoformat(birth['date'])
                    births.append({
                        'date': birth_date_obj,
                        'nifas_days': min(birth.get('nifas_days', 0), config.NIFAS_MAX_DAYS),
                        'hayd_before': birth.get('hayd_before', hayd_average_days or 0)
                    })
                except Exception as e:
                    logger.warning(f"Ошибка обработки данных о родах: {e}")
                    continue
        
        births.sort(key=lambda x: x['date'])
        
        for ramadan_start, ramadan_end in ramadan_dates:
            # Проверяем, попадает ли Рамадан в период пропуска
            if ramadan_end >= adult_date and ramadan_start <= fast_start_date:
                ramadan_count += 1
                
                # Корректируем даты Рамадана под наш период
                actual_start = max(ramadan_start, adult_date)
                actual_end = min(ramadan_end, fast_start_date)
                
                days_in_ramadan = (actual_end - actual_start).days + 1
                total_fast_days += days_in_ramadan
                
                # Для женщин считаем хайд и нифас в этот Рамадан
                if gender == 'female':
                    hayd_in_ramadan, nifas_in_ramadan = self._calculate_excluded_days_in_period(
                        actual_start, actual_end, hayd_average_days, births
                    )
                    total_hayd_days += hayd_in_ramadan
                    total_nifas_days += nifas_in_ramadan
        
        return {
            'total': total_fast_days,
            'ramadan_count': ramadan_count,
            'hayd_days': int(total_hayd_days),
            'nifas_days': int(total_nifas_days)
        }
    
    def _calculate_excluded_days_in_period(self, period_start: date, period_end: date,
                                           hayd_average_days: float,
                                           births: List[Dict]) -> Tuple[int, int]:
        """Расчет дней хайда и нифаса в конкретном периоде"""
        if not hayd_average_days:
            hayd_average_days = 0
            
        total_hayd_days = 0
        total_nifas_days = 0
        
        # Создаем периоды между родами для правильного расчета хайда
        periods = []
        current_start = period_start
        
        for birth in births:
            birth_date = birth['date']
            
            # Если роды попадают в наш период
            if period_start <= birth_date <= period_end:
                # Период до родов
                if current_start < birth_date:
                    periods.append({
                        'start': current_start,
                        'end': birth_date,
                        'hayd_days': birth['hayd_before']
                    })
                
                # Нифас
                nifas_end = birth_date + timedelta(days=birth['nifas_days'])
                nifas_in_period = max(0, min(
                    (min(nifas_end, period_end) - birth_date).days,
                    birth['nifas_days']
                ))
                total_nifas_days += nifas_in_period
                
                # Следующий период начинается после нифаса
                current_start = min(nifas_end, period_end)
        
        # Период после последних родов (или весь период если родов не было)
        if current_start < period_end:
            periods.append({
                'start': current_start,
                'end': period_end,
                'hayd_days': hayd_average_days  # Текущая продолжительность
            })
        
        # Рассчитываем хайд для каждого периода
        for period in periods:
            period_days = (period['end'] - period['start']).days
            if period_days > 0 and period['hayd_days'] > 0:
                period_months = period_days / 30.0
                hayd_in_period = period_months * min(period['hayd_days'], config.HAYD_MAX_DAYS)
                total_hayd_days += min(hayd_in_period, period_days)
        
        return int(total_hayd_days), total_nifas_days
    
    def _get_ramadan_dates(self, start_year: int, end_year: int) -> List[Tuple[date, date]]:
        """Получение примерных дат Рамадана для диапазона лет"""
        ramadan_dates = []
        
        # Базовая дата Рамадана 2024: примерно 11 марта - 9 апреля
        base_date = date(2024, 3, 11)
        
        for year in range(start_year, end_year + 1):
            # Сдвиг на ~11 дней назад каждый год
            year_diff = year - 2024
            shift_days = year_diff * 11
            
            ramadan_start = base_date - timedelta(days=shift_days)
            # Корректируем если вышли за границы года
            if ramadan_start.month == 12 and ramadan_start.day > 20:
                ramadan_start = ramadan_start.replace(year=year-1)
            else:
                ramadan_start = ramadan_start.replace(year=year)
                
            ramadan_end = ramadan_start + timedelta(days=29)  # Рамадан 29-30 дней
            
            ramadan_dates.append((ramadan_start, ramadan_end))
        
        return ramadan_dates
    
    def calculate_hayd_days(self, start_date: date, end_date: date, 
                            average_hayd_days: float, 
                            childbirth_data: List[Dict] = None) -> int:
        """Расчет общего количества дней хайда за период с учетом родов"""
        if not average_hayd_days or average_hayd_days <= 0:
            return 0
        
        # Используем новую логику расчета
        excluded_days = self._calculate_hayd_days_detailed(
            start_date, end_date, average_hayd_days, childbirth_data or []
        )
        
        return excluded_days
    
    def _calculate_hayd_days_detailed(self, start_date: date, end_date: date,
                                      hayd_average_days: float,
                                      childbirth_data: List[Dict]) -> int:
        """Детальный расчет дней хайда с учетом изменений после родов"""
        total_days = (end_date - start_date).days
        
        # Парсим и сортируем данные о родах
        births = []
        if childbirth_data:
            for birth in childbirth_data:
                try:
                    birth_date = date.fromisoformat(birth['date'])
                    if start_date <= birth_date <= end_date:
                        births.append({
                            'date': birth_date,
                            'hayd_before': birth.get('hayd_before', hayd_average_days)
                        })
                except Exception as e:
                    logger.warning(f"Ошибка обработки данных о родах: {e}")
                    continue
        
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
                    'hayd_days': birth['hayd_before']
                })
            
            # Пропускаем период нифаса (он не влияет на расчет хайда)
            current_start = birth['date']
        
        # Период после последних родов
        if current_start < end_date:
            periods.append({
                'start': current_start,
                'end': end_date,
                'hayd_days': hayd_average_days  # Текущая продолжительность
            })
        
        # Если родов не было
        if not births:
            periods.append({
                'start': start_date,
                'end': end_date,
                'hayd_days': hayd_average_days
            })
        
        # Рассчитываем дни хайда для каждого периода
        total_hayd_days = 0
        for period in periods:
            period_days = (period['end'] - period['start']).days
            if period_days > 0 and period['hayd_days'] > 0:
                period_months = period_days / 30.0
                hayd_days_in_period = period_months * min(period['hayd_days'], config.HAYD_MAX_DAYS)
                total_hayd_days += min(hayd_days_in_period, period_days)
        
        return int(min(total_hayd_days, total_days))
    
    def calculate_nifas_days(self, childbirth_data: List[Dict]) -> int:
        """Расчет общего количества дней нифаса"""
        if not childbirth_data:
            return 0
        
        total_nifas = 0
        for birth in childbirth_data:
            nifas_days = birth.get('nifas_days', 0)
            total_nifas += min(nifas_days, config.NIFAS_MAX_DAYS)
        
        return total_nifas