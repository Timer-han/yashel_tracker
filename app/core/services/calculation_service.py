from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from ..config import config
import logging

logger = logging.getLogger(__name__)

class CalculationService:
    """Улучшенный сервис для расчета намазов с детальной логикой для женщин"""
    
    def calculate_male_prayers_simple(self, maturity_date: date, prayer_start_date: date) -> Dict[str, int]:
        """Простой расчет намазов для мужчин между двумя датами"""
        if maturity_date >= prayer_start_date:
            return {prayer_type: 0 for prayer_type in config.PRAYER_TYPES.keys()}
        
        total_days = (prayer_start_date - maturity_date).days
        
        return {
            'fajr': total_days,
            'zuhr': total_days,
            'asr': total_days,
            'maghrib': total_days,
            'isha': total_days,
            'witr': total_days,
            'zuhr_safar': 0,
            'asr_safar': 0,
            'isha_safar': 0
        }
    
    def calculate_male_prayers_with_breaks(self, maturity_date: date, prayer_start_date: date, break_days: int) -> Dict[str, int]:
        """Расчет намазов для мужчин с учетом перерывов"""
        base_days = (prayer_start_date - maturity_date).days
        total_missed_days = base_days + break_days
        
        return {
            'fajr': total_missed_days,
            'zuhr': total_missed_days,
            'asr': total_missed_days,
            'maghrib': total_missed_days,
            'isha': total_missed_days,
            'witr': total_missed_days,
            'zuhr_safar': 0,
            'asr_safar': 0,
            'isha_safar': 0
        }
    
    def calculate_female_prayers_complex(self, 
                                        maturity_date: date,
                                        prayer_start_date: date,
                                        regular_cycle: bool,
                                        hayd_data: Dict,
                                        births_data: List[Dict] = None,
                                        miscarriages_data: List[Dict] = None,
                                        menopause_date: date = None) -> Dict[str, int]:
        """Сложный расчет намазов для женщин с учетом всех факторов"""
        
        # Определяем конечную дату расчета
        if menopause_date and menopause_date < prayer_start_date:
            calculation_end_date = menopause_date
            # Дни от менопаузы до начала намазов добавляются полностью
            post_menopause_days = (prayer_start_date - menopause_date).days if menopause_date < prayer_start_date else 0
        else:
            calculation_end_date = prayer_start_date
            post_menopause_days = 0
        
        if maturity_date >= calculation_end_date:
            return {prayer_type: 0 for prayer_type in config.PRAYER_TYPES.keys()}
        
        # Общее количество дней в периоде
        total_period_days = (calculation_end_date - maturity_date).days
        
        # Вычисляем исключенные дни
        excluded_days = self._calculate_excluded_days_detailed(
            maturity_date, calculation_end_date, regular_cycle, hayd_data, 
            births_data or [], miscarriages_data or []
        )
        
        # Количество дней для намазов
        prayer_days = max(0, total_period_days - excluded_days) + post_menopause_days
        
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
    
    def _calculate_excluded_days_detailed(self, start_date: date, end_date: date,
                                        regular_cycle: bool, hayd_data: Dict,
                                        births_data: List[Dict], miscarriages_data: List[Dict]) -> int:
        """Детальный расчет исключенных дней для женщин"""
        
        # Если указано общее количество дней хайда, используем его
        if hayd_data.get('use_total', False):
            total_nifas_days = self._calculate_total_nifas_days(start_date, end_date, births_data, miscarriages_data)
            total_hayd_days = hayd_data.get('total_hayd_days', 0)
            return min(total_nifas_days + total_hayd_days, (end_date - start_date).days)
        
        # Объединяем и сортируем все события (роды и выкидыши)
        all_events = []
        
        # Добавляем роды
        for birth in births_data:
            # Убеждаемся, что дата в правильном формате
            birth_date = birth['date'] if isinstance(birth['date'], date) else date.fromisoformat(birth['date'])
            all_events.append({
                'date': birth_date,
                'type': 'birth',
                'nifas_days': birth['nifas_days'],
                'hayd_after': birth.get('hayd_after')
            })
        
        # Добавляем выкидыши
        for miscarriage in miscarriages_data:
            miscarriage_date = miscarriage['date'] if isinstance(miscarriage['date'], date) else date.fromisoformat(miscarriage['date'])
            all_events.append({
                'date': miscarriage_date,
                'type': 'miscarriage', 
                'nifas_days': miscarriage['nifas_days'],
                'hayd_after': miscarriage.get('hayd_after')
            })
        
        # Сортируем события по дате
        all_events.sort(key=lambda x: x['date'])
        
        # Создаем периоды для расчета
        periods = self._create_calculation_periods(start_date, end_date, all_events, hayd_data)
        
        total_excluded_days = 0
        
        # Считаем исключенные дни для каждого периода
        for period in periods:
            # Дни нифаса исключаются полностью
            total_excluded_days += period.get('nifas_days', 0)
            
            # Считаем дни хайда в периоде
            hayd_days = self._calculate_hayd_in_period(period, regular_cycle)
            total_excluded_days += hayd_days
        
        return min(total_excluded_days, (end_date - start_date).days)
    
    def _calculate_total_nifas_days(self, start_date: date, end_date: date, 
                                   births_data: List[Dict], miscarriages_data: List[Dict]) -> int:
        """Расчет общего количества дней нифаса в периоде"""
        total_nifas = 0
        
        # Нифас от родов
        for birth in births_data:
            birth_date = birth['date'] if isinstance(birth['date'], date) else date.fromisoformat(birth['date'])
            if start_date <= birth_date <= end_date:
                # Рассчитываем сколько дней нифаса попадает в наш период
                nifas_end = birth_date + timedelta(days=birth['nifas_days'])
                nifas_in_period = min(
                    birth['nifas_days'],
                    (min(nifas_end, end_date) - max(birth_date, start_date)).days
                )
                total_nifas += max(0, nifas_in_period)
        
        # Нифас от выкидышей
        for miscarriage in miscarriages_data:
            miscarriage_date = miscarriage['date'] if isinstance(miscarriage['date'], date) else date.fromisoformat(miscarriage['date'])
            if start_date <= miscarriage_date <= end_date:
                nifas_end = miscarriage_date + timedelta(days=miscarriage['nifas_days'])
                nifas_in_period = min(
                    miscarriage['nifas_days'],
                    (min(nifas_end, end_date) - max(miscarriage_date, start_date)).days
                )
                total_nifas += max(0, nifas_in_period)
        
        return total_nifas
    
    def _create_calculation_periods(self, start_date: date, end_date: date, 
                                   events: List[Dict], hayd_data: Dict) -> List[Dict]:
        """Создание периодов для расчета между событиями"""
        periods = []
        current_start = start_date
        
        for event in events:
            event_date = event['date']
            
            # Проверяем, попадает ли событие в наш период
            if start_date <= event_date <= end_date:
                # Период до события
                if current_start < event_date:
                    periods.append({
                        'start': current_start,
                        'end': event_date,
                        'hayd_days_per_month': hayd_data.get('average_hayd', 5),
                        'type': 'regular_period'
                    })
                
                # Добавляем период нифаса
                nifas_end = min(event_date + timedelta(days=event['nifas_days']), end_date)
                if event['nifas_days'] > 0:
                    periods.append({
                        'start': event_date,
                        'end': nifas_end,
                        'nifas_days': min(event['nifas_days'], (end_date - event_date).days),
                        'type': 'nifas'
                    })
                
                # Следующий период начинается после нифаса
                current_start = nifas_end
                
                # Обновляем данные о хайде для следующего периода (если указано)
                if event.get('hayd_after'):
                    hayd_data['average_hayd'] = event['hayd_after']
        
        # Последний период после всех событий
        if current_start < end_date:
            periods.append({
                'start': current_start,
                'end': end_date,
                'hayd_days_per_month': hayd_data.get('average_hayd', 5),
                'type': 'regular_period'
            })
        
        # Если событий не было вообще
        if not events:
            periods.append({
                'start': start_date,
                'end': end_date,
                'hayd_days_per_month': hayd_data.get('average_hayd', 5),
                'type': 'regular_period'
            })
        
        return periods
    
    def _calculate_hayd_in_period(self, period: Dict, regular_cycle: bool) -> int:
        """Расчет дней хайда в конкретном периоде"""
        if period['type'] == 'nifas':
            return 0  # В нифас хайда нет
        
        period_days = (period['end'] - period['start']).days
        if period_days <= 0:
            return 0
        
        # Для регулярного цикла используем точный расчет
        if regular_cycle:
            # Примерно 12 циклов в год, каждый цикл ~30 дней
            period_months = period_days / 30.0
            hayd_days = period_months * min(period['hayd_days_per_month'], config.HAYD_MAX_DAYS)
        else:
            # Для нерегулярного цикла используем среднее значение  
            period_months = period_days / 30.0
            hayd_days = period_months * min(period['hayd_days_per_month'], config.HAYD_MAX_DAYS)
        
        return min(int(hayd_days), period_days)
    
    def estimate_maturity_age(self, birth_date: date, is_female: bool) -> date:
        """Оценка даты совершеннолетия"""
        if is_female:
            # Для девочек 8.5 лет
            years_to_add = 8
            days_to_add = int(0.5 * 365)  # Полгода
        else:
            # Для мальчиков 11.5 лет  
            years_to_add = 11
            days_to_add = int(0.5 * 365)  # Полгода
        
        maturity_date = birth_date.replace(year=birth_date.year + years_to_add)
        maturity_date += timedelta(days=days_to_add)
        
        return maturity_date
    
    def format_calculation_summary(self, prayers_data: Dict[str, int], 
                                   calculation_details: Dict = None) -> str:
        """Форматирование итогов расчета"""
        total_prayers = sum(prayers_data.values())
        
        summary = f"📊 **Результат расчета:**\n\n"
        summary += f"📝 **Всего пропущенных намазов: {total_prayers}**\n\n"
        
        if calculation_details:
            summary += f"📅 Период: с {calculation_details.get('start_date', '')} по {calculation_details.get('end_date', '')}\n"
            if calculation_details.get('excluded_days'):
                summary += f"❌ Исключено дней: {calculation_details['excluded_days']}\n"
            if calculation_details.get('prayer_days'):
                summary += f"✅ Дней для намазов: {calculation_details['prayer_days']}\n"
            summary += "\n"
        
        summary += "**Детализация по намазам:**\n"
        for prayer_type, count in prayers_data.items():
            if count > 0:
                prayer_name = config.PRAYER_TYPES[prayer_type]
                summary += f"🕌 {prayer_name}: {count}\n"
        
        summary += "\n🤲 Пусть Аллах облегчит тебе восполнение!"
        
        return summary