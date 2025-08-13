from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_fast_calculation_method_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора метода расчета постов"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="🔢 От совершеннолетия до начала постов", 
        callback_data="fast_calc_from_age"
    ))
    builder.add(InlineKeyboardButton(
        text="📅 Между двумя датами", 
        callback_data="fast_calc_between_dates"
    ))
    builder.add(InlineKeyboardButton(
        text="✋ Ввести вручную", 
        callback_data="fast_calc_manual"
    ))
    
    builder.adjust(1)
    
    return builder.as_markup()

def get_fast_type_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа поста для ручного ввода"""
    builder = InlineKeyboardBuilder()
    
    from ....core.config import config
    
    for fast_type, fast_name in config.FAST_TYPES.items():
        builder.add(InlineKeyboardButton(
            text=fast_name, 
            callback_data=f"select_fast_{fast_type}"
        ))
    
    builder.add(InlineKeyboardButton(text="✅ Завершить ввод", callback_data="finish_manual_fast_input"))
    
    builder.adjust(2)
    
    return builder.as_markup()