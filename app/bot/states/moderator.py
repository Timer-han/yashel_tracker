from aiogram.fsm.state import State, StatesGroup

class ModeratorStates(StatesGroup):
    """Состояния модератора"""
    main_menu = State()
    broadcast_message = State()
    broadcast_filters = State()
    broadcast_confirmation = State()