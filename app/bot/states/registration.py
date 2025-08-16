from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    """Состояния регистрации"""
    waiting_for_gender = State()
    waiting_for_birth_date = State()
    waiting_for_city = State()
    
    # Новые состояния для женщин
    waiting_for_hayd_average = State()
    waiting_for_childbirth_count = State()
    waiting_for_childbirth_date = State()
    waiting_for_nifas_days = State()
    waiting_for_hayd_after_birth = State()
    waiting_for_hayd_before_birth = State()
    
    confirmation = State()