from aiogram.fsm.state import State, StatesGroup

class FemalePeriodsStates(StatesGroup):
    """Состояния для ввода информации о женских периодах"""
    
    # Хайд
    asking_hayd_duration = State()
    entering_hayd_duration = State()
    
    # Нифас
    asking_childbirth = State()
    entering_childbirth_count = State()
    
    # Ввод информации о родах
    entering_childbirth_date = State()
    entering_nifas_duration = State()
    entering_hayd_before_childbirth = State()
    entering_hayd_after_childbirth = State()
    
    # Текущий номер родов при вводе
    current_childbirth_number = State()

class FastCalculationStates(StatesGroup):
    """Состояния для расчета постов"""
    
    choosing_method = State()
    waiting_for_fasting_start_date = State()
    entering_ramadan_years = State()
    confirmation = State()