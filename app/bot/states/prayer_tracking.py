from aiogram.fsm.state import State, StatesGroup

class PrayerTrackingStates(StatesGroup):
    """Состояния отслеживания намазов"""
    main_menu = State()
    editing_prayer = State()
    manual_adjustment = State()
    confirmation_reset = State()
    manual_input = State()
