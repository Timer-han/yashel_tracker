from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_fasting_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления постами"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="🔢 Рассчитать посты", callback_data="fast_calculate"))
    builder.add(InlineKeyboardButton(text="📊 Статистика", callback_data="fast_stats"))
    builder.add(InlineKeyboardButton(text="➕ Добавить день", callback_data="fast_add"))
    builder.add(InlineKeyboardButton(text="➖ Убрать день", callback_data="fast_remove"))
    builder.add(InlineKeyboardButton(text="🔄 Сброс", callback_data="fast_reset"))
    
    builder.adjust(2, 2, 1)
    
    return builder.as_markup()

def get_fasting_action_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура быстрых действий с постами"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(text="-7", callback_data="fast_adjust_-7"),
        InlineKeyboardButton(text="-3", callback_data="fast_adjust_-3"),
        InlineKeyboardButton(text="-1", callback_data="fast_adjust_-1")
    )
    
    builder.add(
        InlineKeyboardButton(text="+1", callback_data="fast_adjust_1"),
        InlineKeyboardButton(text="+3", callback_data="fast_adjust_3"),
        InlineKeyboardButton(text="+7", callback_data="fast_adjust_7")
    )
    
    builder.add(InlineKeyboardButton(text="✅ Готово", callback_data="fast_done"))
    
    builder.adjust(3, 3, 1)
    
    return builder.as_markup()