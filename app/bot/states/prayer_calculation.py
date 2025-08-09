from aiogram.fsm.state import State, StatesGroup

class PrayerCalculationStates(StatesGroup):
    """Состояния расчета намазов"""
    choosing_method = State()
    
    # Автоматический расчет с возраста
    waiting_for_adult_age = State()
    waiting_for_prayer_start_date = State()
    
    # Расчет между датами
    waiting_for_adult_date = State()
    waiting_for_prayer_start_date_custom = State()
    
    # Расчет между произвольными датами
    waiting_for_start_date = State()
    waiting_for_end_date = State()
    
    # Ручной ввод
    manual_input = State()
    
    confirmation = State()

    waiting_for_adult_date = State()
    waiting_for_prayer_start_from_adult = State()