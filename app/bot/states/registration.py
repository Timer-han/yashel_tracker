from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    """Состояния регистрации"""
    waiting_for_gender = State()
    waiting_for_birth_date = State()
    waiting_for_city = State()
    
    # Состояния для женщин
    waiting_for_hayd_average = State()  # Текущая продолжительность хайда
    waiting_for_childbirth_count = State()
    waiting_for_childbirth_date = State()
    waiting_for_nifas_days = State()
    waiting_for_hayd_before_birth = State()  # Хайд ДО конкретных родов
    # Убрали waiting_for_hayd_after_birth - больше не нужно
    
    confirmation = State()