from aiogram.fsm.state import State, StatesGroup

class PrayerCalculationStates(StatesGroup):
    """Обновленные состояния расчета намазов"""
    
    # Общие состояния
    choosing_method = State()
    manual_input_count = State()
    
    # === МУЖСКИЕ СОСТОЯНИЯ ===
    
    # Метод 1: Знаю дату совершеннолетия
    male_maturity_date_input = State()
    male_prayer_start_date_input = State()
    
    # Метод 2: Научиться считать сам
    male_learning_remember_maturity = State()
    male_learning_know_prayer_start = State() 
    male_learning_had_breaks = State()
    male_learning_final_count_input = State()
    
    # === ЖЕНСКИЕ СОСТОЯНИЯ ===
    
    # Метод 1: Знаю дату совершеннолетия
    female_maturity_date_input = State()
    female_regular_cycle_question = State()
    female_cycle_length_input = State()
    female_track_hayd_question = State()
    female_total_hayd_days_input = State()
    female_average_hayd_input = State()
    
    # Роды
    female_births_question = State()
    female_births_count_input = State()
    female_birth_date_input = State()
    female_birth_nifas_input = State()
    female_birth_hayd_after_input = State()
    
    # Выкидыши
    female_miscarriages_question = State()
    female_miscarriages_count_input = State()
    female_miscarriage_date_input = State()
    female_miscarriage_nifas_input = State()
    female_miscarriage_hayd_after_input = State()
    
    # Менопауза и финал
    female_menopause_question = State()
    female_menopause_date_input = State()
    female_prayer_start_date_input = State()
    
    # Метод 2: Не помню дату совершеннолетия  
    female_no_maturity_date_input = State()
    
    # Состояния для циклов (обработка нескольких родов/выкидышей)
    processing_births = State()
    processing_miscarriages = State()
    
    # Подтверждение расчетов
    calculation_confirmation = State()
    
    # Дополнительные состояния для завершения циклов
    birth_cycle_complete = State()
    miscarriage_cycle_complete = State()
    
    # Ручной ввод по каждому намазу
    manual_input_individual = State()
    manual_input_fajr = State()
    manual_input_zuhr = State()
    manual_input_asr = State()
    manual_input_maghrib = State()
    manual_input_isha = State()
    manual_input_witr = State()
    manual_input_zuhr_safar = State()
    manual_input_asr_safar = State()
    manual_input_isha_safar = State()