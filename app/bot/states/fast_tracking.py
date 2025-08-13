from aiogram.fsm.state import State, StatesGroup

class FastTrackingStates(StatesGroup):
    """Состояния отслеживания постов"""
    main_menu = State()
    editing_fast = State()
    manual_adjustment = State()
    confirmation_reset = State()