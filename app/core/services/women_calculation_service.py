from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from ..config import config
import json

class WomenCalculationService:
    """Сервис для расчета намазов и постов с учетом хайда/нифаса"""
    
    def calculate_hayd_days(self, start_date: date, end_date: date, 
                            average_hayd_days: float) -> int:
        """Расчет общего количества дней хайда за период"""
        if not average_hayd_days or average_hayd_days <= 0:
            return 0
        
        total_days = (end_date - start_date).days
        total_months = total_days / 30  # Приблизительно
        total_hayd_days = int(total_months * average_hayd_days)
        
        return min(total_hayd_days, total_days)
    
    def calculate_nifas_days(self, childbirth_data: List[Dict]) -> int:
        """Расчет общего количества дней нифаса"""
        if not childbirth_data:
            return 0
        
        total_nifas = 0
        for birth in childbirth_data:
            nifas_days = birth.get('nifas_days', 0)
            total_nifas += min(nifas_days, config.NIFAS_MAX_DAYS)
        
        return total_nifas
    
    def calculate_adjusted_prayer_days(self, start_date: date, end_date: date,
                                       hayd_average_days: float, 
                                       childbirth_data: List[Dict]) -> Tuple[int, int, int]:
        """
        Расчет дней для намазов с учетом хайда и нифаса
        Возвращает: (общее_количество_дней, дни_хайда, дни_нифаса)
        """
        total_days = (end_date - start_date).days
        
        # Рассчитываем дни хайда
        hayd_days = self.calculate_hayd_days(start_date, end_date, hayd_average_days)
        
        # Рассчитываем дни нифаса
        nifas_days = 0
        if childbirth_data:
            for birth in childbirth_data:
                birth_date = date.fromisoformat(birth['date'])
                if start_date <= birth_date <= end_date:
                    nifas_days += min(birth.get('nifas_days', 0), config.NIFAS_MAX_DAYS)
        
        # Дни, когда нужно читать намаз (исключаем хайд и нифас)
        prayer_days = max(0, total_days - hayd_days - nifas_days)
        
        return prayer_days, hayd_days, nifas_days
    
    def calculate_missed_fasts(self, birth_date: date, fast_start_date: date,
                              gender: str, hayd_average_days: float = None,
                              childbirth_data: List[Dict] = None) -> Dict[str, int]:
        """Расчет пропущенных постов"""
        # Определяем возраст начала обязательных постов
        adult_age = config.ADULT_AGE_FEMALE if gender == 'female' else config.ADULT_AGE_MALE
        adult_date = birth_date.replace(year=birth_date.year + adult_age)
        
        if fast_start_date <= adult_date:
            return {'total': 0, 'hayd_days': 0, 'nifas_days': 0}
        
        # Считаем количество Рамаданов между датами
        years_missed = fast_start_date.year - adult_date.year
        total_fast_days = years_missed * 30  # Приблизительно 30 дней в Рамадане
        
        # Для женщин учитываем хайд и нифас
        if gender == 'female':
            # Хайд во время Рамадана (примерно)
            hayd_during_ramadan = 0
            if hayd_average_days:
                hayd_during_ramadan = int(years_missed * min(hayd_average_days, 10))
            
            # Нифас во время Рамадана
            nifas_during_ramadan = 0
            if childbirth_data:
                for birth in childbirth_data:
                    birth_date_obj = date.fromisoformat(birth['date'])
                    # Проверяем, попадает ли нифас на Рамадан (упрощенно)
                    if adult_date <= birth_date_obj <= fast_start_date:
                        # Примерно 1/12 вероятность попадания на Рамадан
                        nifas_during_ramadan += int(birth.get('nifas_days', 0) / 12)
            
            # Посты нужно восполнять 1:1 даже за дни хайда/нифаса
            return {
                'total': total_fast_days,
                'hayd_days': hayd_during_ramadan,
                'nifas_days': nifas_during_ramadan
            }
        
        return {'total': total_fast_days, 'hayd_days': 0, 'nifas_days': 0}


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
    hayd_during_ramadan = 0
    nifas_during_ramadan = 0
    
    # Примерные даты Рамадана (сдвигается на ~11 дней каждый год)
    ramadan_dates = self._get_ramadan_dates(start_year, end_year)
    
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
                # Хайд (примерно 1 раз в месяц)
                if hayd_average_days:
                    hayd_during_ramadan += min(hayd_average_days, days_in_ramadan)
                
                # Нифас
                if childbirth_data:
                    for birth in childbirth_data:
                        birth_date_obj = date.fromisoformat(birth['date'])
                        nifas_end = birth_date_obj + timedelta(days=birth.get('nifas_days', 0))
                        
                        # Проверяем пересечение нифаса с Рамаданом
                        if birth_date_obj <= ramadan_end and nifas_end >= ramadan_start:
                            nifas_start = max(birth_date_obj, ramadan_start)
                            nifas_finish = min(nifas_end, ramadan_end)
                            nifas_days_in_ramadan = (nifas_finish - nifas_start).days + 1
                            nifas_during_ramadan += max(0, nifas_days_in_ramadan)
    
    return {
        'total': total_fast_days,
        'ramadan_count': ramadan_count,
        'hayd_days': int(hayd_during_ramadan),
        'nifas_days': int(nifas_during_ramadan)
    }

def _get_ramadan_dates(self, start_year: int, end_year: int) -> List[Tuple[date, date]]:
    """Получение примерных дат Рамадана для диапазона лет"""
    # Это упрощенный расчет. В реальности нужно использовать исламский календарь
    # Здесь используем примерные даты
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