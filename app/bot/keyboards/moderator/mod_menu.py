from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

def get_broadcast_filters_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура фильтров для рассылки"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="👨 Мужчины", callback_data="filter_gender_male"))
    builder.add(InlineKeyboardButton(text="👩 Женщины", callback_data="filter_gender_female"))
    
    builder.add(InlineKeyboardButton(text="📍 По городу", callback_data="filter_city"))
    builder.add(InlineKeyboardButton(text="🎂 По возрасту", callback_data="filter_age"))
    
    builder.add(InlineKeyboardButton(text="📢 Всем пользователям", callback_data="filter_all"))
    
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast"))
    
    builder.adjust(2, 2, 1, 1)
    
    return builder.as_markup()

def get_age_filter_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура фильтра по возрасту"""
    builder = InlineKeyboardBuilder()
    
    age_groups = [
        ("До 18", "age_0_18"),
        ("18-24", "age_18_24"),
        ("25-34", "age_25_34"),
        ("35-44", "age_35_44"),
        ("45-54", "age_45_54"),
        ("55+", "age_55_plus")
    ]
    
    for text, callback in age_groups:
        builder.add(InlineKeyboardButton(text=text, callback_data=f"filter_{callback}"))
    
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_filters"))
    
    builder.adjust(2)
    
    return builder.as_markup()

def get_broadcast_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения рассылки"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_broadcast"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")
    )
    
    builder.adjust(2)
    
    return builder.as_markup()
