from aiogram.fsm.state import State, StatesGroup

class FastingStates(StatesGroup):
    """Состояния для работы с постами"""
    waiting_for_fast_start_date = State()
    manual_input = State()
    confirmation = State()