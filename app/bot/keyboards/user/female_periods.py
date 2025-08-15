from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_childbirth_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для вопроса о родах"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(text="✅ Да", callback_data="has_childbirth_yes"),
        InlineKeyboardButton(text="❌ Нет", callback_data="has_childbirth_no")
    )
    
    builder.adjust(2)
    
    return builder.as_markup()

def get_continue_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для продолжения"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(text="➡️ Продолжить", callback_data="continue_input")
    )
    
    return builder.as_markup()