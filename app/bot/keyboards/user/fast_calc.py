from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_fast_calculation_method_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора метода расчета постов"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="🔢 От возраста совершеннолетия",
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