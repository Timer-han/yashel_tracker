from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    """Состояния регистрации"""
    waiting_for_gender = State()
    waiting_for_birth_date = State()
    waiting_for_city = State()
    
    # Состояния для женщин
    asking_about_childbirths = State()
    waiting_for_childbirth_count = State()
    waiting_for_childbirth_dates = State()
    waiting_for_hyde_before_first = State()
    waiting_for_nifas_length = State()
    waiting_for_hyde_after_birth = State()
    waiting_for_average_hyde = State()
    
    confirmation = State()