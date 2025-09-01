from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_male_calculation_method_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура методов расчета для мужчин"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="📅 Знаю дату совершеннолетия", 
        callback_data="male_know_maturity"
    ))
    builder.add(InlineKeyboardButton(
        text="✋ Введу количество вручную", 
        callback_data="male_manual"
    ))
    builder.add(InlineKeyboardButton(
        text="🎓 Хочу научиться считать сам!", 
        callback_data="male_learn"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_female_calculation_method_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура методов расчета для женщин"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="✋ Введу количество вручную", 
        callback_data="female_manual"
    ))
    builder.add(InlineKeyboardButton(
        text="📖 Подробный гайд по вычислению", 
        callback_data="female_guide"
    ))
    builder.add(InlineKeyboardButton(
        text="📅 Знаю дату совершеннолетия", 
        callback_data="female_know_maturity"
    ))
    builder.add(InlineKeyboardButton(
        text="🤔 Не помню дату совершеннолетия", 
        callback_data="female_no_maturity"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_yes_no_keyboard(yes_callback: str, no_callback: str) -> InlineKeyboardMarkup:
    """Универсальная клавиатура Да/Нет"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="✅ Да", callback_data=yes_callback))
    builder.add(InlineKeyboardButton(text="❌ Нет", callback_data=no_callback))
    
    builder.adjust(2)
    return builder.as_markup()

def get_births_count_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора количества родов"""
    builder = InlineKeyboardBuilder()
    
    for i in range(1, 8):  # 1-7 родов
        builder.add(InlineKeyboardButton(text=str(i), callback_data=f"births_count_{i}"))
    
    builder.add(InlineKeyboardButton(text="8+ (ввести)", callback_data="births_count_manual"))
    
    builder.adjust(4, 4)
    return builder.as_markup()

def get_miscarriages_count_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора количества выкидышей"""
    builder = InlineKeyboardBuilder()
    
    for i in range(1, 7):  # 1-5 выкидышей
        builder.add(InlineKeyboardButton(text=str(i), callback_data=f"miscarriages_count_{i}"))
    
    builder.add(InlineKeyboardButton(text="6+ (ввести)", callback_data="miscarriages_count_manual"))
    
    builder.adjust(3, 3, 1)
    return builder.as_markup()

def day_case_russian (count: int) -> str:
    return "дней" if 10 <= count % 100 <= 20 or 5 <= count % 10 <= 9 else "дня"

def get_hayd_duration_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора продолжительности хайда"""
    builder = InlineKeyboardBuilder()
    
    common_values = [3, 4, 5, 6, 7, 8, 9, 10]
    for days in common_values:
        builder.add(InlineKeyboardButton(text=f"{days} {day_case_russian(days)}", callback_data=f"hayd_days_{days}"))
    
    # builder.add(InlineKeyboardButton(text="Другое (ввести)", callback_data="hayd_days_manual"))
    
    builder.adjust(4, 4)
    return builder.as_markup()

def get_nifas_duration_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора продолжительности нифаса"""
    builder = InlineKeyboardBuilder()
    
    common_values = [15, 20, 25, 30, 35, 40]
    for days in common_values:
        builder.add(InlineKeyboardButton(text=f"{days} дней", callback_data=f"nifas_days_{days}"))
    
    builder.add(InlineKeyboardButton(text="Другое (ввести)", callback_data="nifas_days_manual"))
    
    builder.adjust(3, 3, 1)
    return builder.as_markup()

def get_calculation_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения расчетов"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="✅ Все верно", callback_data="confirm_calculation"))
    builder.add(InlineKeyboardButton(text="🔄 Пересчитать", callback_data="recalculate"))
    
    builder.adjust(2)
    return builder.as_markup()

def get_continue_or_finish_keyboard(continue_callback: str, finish_callback: str) -> InlineKeyboardMarkup:
    """Клавиатура продолжить/завершить (для циклов)"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="➡️ Продолжить", callback_data=continue_callback))
    builder.add(InlineKeyboardButton(text="✅ Завершить", callback_data=finish_callback))
    
    builder.adjust(2)
    return builder.as_markup()

# Для совместимости с существующим кодом
def get_calculation_method_keyboard() -> InlineKeyboardMarkup:
    """Старая клавиатура - перенаправляем на мужскую"""
    return get_male_calculation_method_keyboard()

# def get_female_calculation_method_keyboard() -> InlineKeyboardMarkup:
#     """Клавиатура выбора метода расчета для женщин"""
#     return get_female_calculation_method_keyboard()