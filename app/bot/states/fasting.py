from aiogram.fsm.state import State, StatesGroup

class FastingStates(StatesGroup):
    """Состояния для работы с постами"""
    
    # Выбор метода расчета
    choosing_method = State()
    
    # Расчет от совершеннолетия
    waiting_for_fast_start_date = State()
    
    # Расчет между датами  
    waiting_for_fast_period_start = State()
    waiting_for_fast_period_end = State()
    
    # Расчет за года
    waiting_for_fast_year_count = State()
    
    # Ручной ввод
    waiting_for_manual_days = State()
    
    # Подтверждение
    confirmation = State()