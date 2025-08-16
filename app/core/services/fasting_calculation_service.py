from datetime import date, timedelta
from typing import Dict, List, Optional
from ..config import config
import logging

logger = logging.getLogger(__name__)

class FastingCalculationService:
    """Сервис для расчета пропущенных постов"""
    
    # def calculate_fasts_from_age(self, birth_date: date, fast_start_date: date,
    #                              gender: str = 'male',
    #                              hayd_average_days: float = None,
    #                              childbirth_data: List[Dict] = None) -> Dict[str, int]:
    #     """Расчет постов от возраста совершеннолетия до начала соблюдения постов"""
    #     adult_age = config.ADULT_AGE_FEMALE if gender == 'female' else config.ADULT_AGE_MALE
    #     adult_date = birth_date.replace(year=birth_date.year + adult_age)
        
    #     return self.calculate_fasts_between_dates(
    #         adult_date, fast_start_date, gender, 
    #         hayd_average_days, childbirth_data
    #     )
    
    def calculate_fasts_between_dates(self, start_date: date, end_date: date,
                                      gender: str = 'male',
                                      hayd_average_days: float = None,
                                      childbirth_data: List[Dict] = None) -> Dict[str, int]:
        """Расчет постов между двумя датами"""
        if start_date >= end_date:
            return {'total_days': 0, 'excluded_days': 0, 'fasting_days': 0, 'details': ''}
        
        # Количество полных лет
        years_diff = end_date.year - start_date.year
        if end_date.month < start_date.month or (end_date.month == start_date.month and end_date.day < start_date.day):
            years_diff -= 1
        
        # Приблизительное количество дней постов в году (30 дней Рамадана)
        base_fast_days = years_diff * 30
        
        # Для женщин вычитаем дни хайда и нифаса
        excluded_days = 0
        details = ""
        
        if False and gender == 'female':
            excluded_days = self._calculate_excluded_fast_days_for_women(
                start_date, end_date, hayd_average_days, childbirth_data
            )
            details = self._generate_calculation_details(
                start_date, end_date, hayd_average_days, childbirth_data, excluded_days
            )
        
        final_fast_days = max(0, base_fast_days - excluded_days)
        
        return {
            'total_days': base_fast_days,
            'excluded_days': excluded_days,
            'fasting_days': final_fast_days,
            'details': details,
            'years': years_diff
        }
        
    def calculate_fasts_by_years(self, years: int) -> Dict[str, int]:
        """Расчет постов за заданное количество лет"""
        if years <= 0:
            return {'total_days': 0, 'excluded_days': 0, 'fasting_days': 0, 'details': ''}
        
        # Количество дней постов в год
        base_fast_days = years * 30
        
        # Для женщин вычитаем дни хайда и нифаса
        excluded_days = 0
        details = ""
        
        return {
            'total_days': base_fast_days,
            'excluded_days': excluded_days,
            'fasting_days': base_fast_days - excluded_days,
            'details': details,
            'years': years
        }
    
    def _calculate_excluded_fast_days_for_women(self, start_date: date, end_date: date,
                                                hayd_average_days: float = None,
                                                childbirth_data: List[Dict] = None) -> int:
        """Расчет исключенных дней для женщин (хайд + нифас)"""
        if not hayd_average_days:
            hayd_average_days = 0
        
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
        
        births.sort(key=lambda x: x['date'])
        
        total_excluded_days = 0
        current_start = start_date
        
        for i, birth in enumerate(births):
            birth_date = birth['date']
            
            # 1. Период до родов
            if current_start < birth_date:
                years_before = self._calculate_years_between_dates(current_start, birth_date)
                hayd_days_before = years_before * birth['hayd_before']
                total_excluded_days += hayd_days_before
                
                logger.info(f"До родов {i+1}: {years_before:.1f} лет * {birth['hayd_before']} дней хайда = {hayd_days_before:.1f} дней")
            
            # 2. Период нифаса
            nifas_days_in_ramadan = birth['nifas_days'] * (30 / 365)  # Пропорция нифаса попавшего на Рамадан
            total_excluded_days += nifas_days_in_ramadan
            
            logger.info(f"Нифас после родов {i+1}: {birth['nifas_days']} дней, в Рамадан попало ~{nifas_days_in_ramadan:.1f} дней")
            
            # Следующий период начинается после нифаса
            current_start = birth_date + timedelta(days=birth['nifas_days'])
        
        # 3. Период после последних родов (или весь период если родов не было)
        if current_start < end_date:
            years_after = self._calculate_years_between_dates(current_start, end_date)
            hayd_days_after = years_after * hayd_average_days
            total_excluded_days += hayd_days_after
            
            logger.info(f"После последних родов: {years_after:.1f} лет * {hayd_average_days} дней хайда = {hayd_days_after:.1f} дней")
        
        return int(total_excluded_days)
    
    def _calculate_years_between_dates(self, start: date, end: date) -> float:
        """Расчет количества лет между датами (с дробной частью)"""
        years = end.year - start.year
        
        # Корректируем если дата окончания раньше в году
        if end.month < start.month or (end.month == start.month and end.day < start.day):
            years -= 1
            
        # Добавляем дробную часть
        days_diff = (end - start).days
        return days_diff / 365.25
    
    def _generate_calculation_details(self, start_date: date, end_date: date,
                                      hayd_average_days: float,
                                      childbirth_data: List[Dict],
                                      excluded_days: int) -> str:
        """Генерация детального отчета о расчете"""
        details = "📋 **Детали расчета для женщин:**\n\n"
        
        years_total = self._calculate_years_between_dates(start_date, end_date)
        details += f"🗓️ Общий период: {years_total:.1f} лет\n"
        details += f"🌙 Текущий хайд: {hayd_average_days} дней/месяц\n\n"
        
        if childbirth_data:
            details += "👶 **Роды в этом периоде:**\n"
            births_in_period = []
            
            for birth in childbirth_data:
                try:
                    birth_date = date.fromisoformat(birth['date'])
                    if start_date <= birth_date <= end_date:
                        births_in_period.append(birth)
                        details += f"• {birth_date.strftime('%d.%m.%Y')}: нифас {birth['nifas_days']} дней, хайд до родов {birth['hayd_before']} дней\n"
                except:
                    continue
            
            if not births_in_period:
                details += "• Родов в этом периоде не было\n"
            
            details += "\n"
        
        details += f"❌ **Исключено дней:** {excluded_days}\n"
        details += "💡 **Принцип расчета:** из 30 дней поста в год вычитаются дни хайда и нифаса, попадающие на Рамадан"
        
        return details