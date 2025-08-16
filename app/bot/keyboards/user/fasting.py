from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_fasting_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления постами"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="🔢 Рассчитать посты", callback_data="fast_calculate"))
    builder.add(InlineKeyboardButton(text="📊 Статистика", callback_data="fast_stats"))
    builder.add(InlineKeyboardButton(text="➖", callback_data="fast_completed"))
    builder.add(InlineKeyboardButton(text="➕", callback_data="fast_missed"))
    builder.add(InlineKeyboardButton(text="🔄 Сброс", callback_data="fast_reset"))
    
    builder.adjust(2, 2, 1)
    
    return builder.as_markup()

def get_fasting_calculation_method_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора метода расчета постов"""
    builder = InlineKeyboardBuilder()
    
    # builder.add(InlineKeyboardButton(
    #     text="🕌 От совершеннолетия до начала постов", 
    #     callback_data="fast_calc_from_age"
    # ))
    builder.add(InlineKeyboardButton(
        text="📅 Задать количество лет", 
        callback_data="fast_calc_years"
    ))
    builder.add(InlineKeyboardButton(
        text="✋ Ввести количество вручную", 
        callback_data="fast_calc_manual"
    ))
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="fast_calc_cancel"))
    
    builder.adjust(2, 1)
    
    return builder.as_markup()

def get_female_fasting_calculation_method_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора метода расчета постов"""
    builder = InlineKeyboardBuilder()
    
    # builder.add(InlineKeyboardButton(
    #     text="🕌 От совершеннолетия до начала постов", 
    #     callback_data="fast_calc_from_age"
    # ))
    # builder.add(InlineKeyboardButton(
    #     text="📅 Между двумя датами", 
    #     callback_data="fast_calc_years"
    # ))
    builder.add(InlineKeyboardButton(
        text="✋ Ввести количество вручную", 
        callback_data="fast_calc_manual"
    ))
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="fast_calc_cancel"))
    
    builder.adjust(1, 1)
    
    return builder.as_markup()

def get_fasting_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения расчета постов"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(text="✅ Сохранить", callback_data="fast_confirm_save"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="fast_confirm_cancel")
    )
    
    builder.adjust(2)
    
    return builder.as_markup()

def get_fasting_action_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура быстрых действий с постами"""
    builder = InlineKeyboardBuilder()
    
    # Быстрые действия для восполнения
    builder.add(
        InlineKeyboardButton(text="✅ +1", callback_data="fast_adjust_completed_1"),
        InlineKeyboardButton(text="✅ +3", callback_data="fast_adjust_completed_3"),
        InlineKeyboardButton(text="✅ +7", callback_data="fast_adjust_completed_7")
    )
    
    # Быстрые действия для пропущенных
    builder.add(
        InlineKeyboardButton(text="➕ +1", callback_data="fast_adjust_missed_1"),
        InlineKeyboardButton(text="➕ +3", callback_data="fast_adjust_missed_3"),
        InlineKeyboardButton(text="➕ +7", callback_data="fast_adjust_missed_7")
    )
    
    builder.add(InlineKeyboardButton(text="✅ Готово", callback_data="fast_done"))
    
    builder.adjust(3, 3, 1)
    
    return builder.as_markup()