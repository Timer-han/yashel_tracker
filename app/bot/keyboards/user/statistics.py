from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_statistics_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для статистики"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="📋 История", callback_data="show_history"))
    builder.add(InlineKeyboardButton(text="🔍 Детали", callback_data="detailed_breakdown"))
    builder.add(InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_stats"))
    
    builder.adjust(2, 1)
    
    return builder.as_markup()