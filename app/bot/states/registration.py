from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    """Состояния регистрации"""
    waiting_for_name = State()
    waiting_for_gender = State()
    waiting_for_birth_date = State()
    waiting_for_city = State()
    confirmation = State()
