from aiogram.fsm.state import State, StatesGroup

class FastCalculationStates(StatesGroup):
    """Состояния расчета постов"""
    choosing_method = State()
    
    # Автоматический расчет
    waiting_for_fast_start_date = State()
    
    # Расчет между датами
    waiting_for_start_date = State()
    waiting_for_end_date = State()
    
    # Ручной ввод
    waiting_for_fast_type_selection = State()
    waiting_for_manual_fast_count = State()
    
    confirmation = State()