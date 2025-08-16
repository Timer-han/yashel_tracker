from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    """Состояния администратора"""
    main_menu = State()
    add_admin_id = State()
    add_admin_role = State()
    remove_admin_id = State()
    confirmation = State()