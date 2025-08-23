from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    """Состояния регистрации пользователя"""
    
    # Основные данные
    gender_selection = State()          # Выбор пола
    birth_date_input = State()          # Ввод даты рождения  
    city_input = State()                # Ввод города
    
    # Женские циклы (только для женщин)
    hayd_duration_input = State()       # Текущая продолжительность хайда
    childbirth_count_input = State()    # Количество родов
    pre_birth_hayd_input = State()      # Продолжительность хайда ДО конкретных родов
    childbirth_date_input = State()     # Дата конкретных родов
    nifas_duration_input = State()      # Продолжительность нифаса после родов
    
    # Финализация
    data_confirmation = State()         # Подтверждение введенных данных