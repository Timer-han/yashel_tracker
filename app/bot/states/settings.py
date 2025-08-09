from aiogram.fsm.state import State, StatesGroup

class SettingsStates(StatesGroup):
    """Состояния для настроек"""
    waiting_for_name = State()
    waiting_for_gender = State()
    waiting_for_birth_date = State()
    waiting_for_city = State()