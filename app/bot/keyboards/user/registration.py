from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

def get_gender_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора пола"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="👨 Мужской"))
    builder.add(KeyboardButton(text="👩 Женский"))
    
    builder.adjust(2)
    
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def get_gender_inline_keyboard() -> InlineKeyboardMarkup:
    """Встроенная клавиатура выбора пола"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="👨 Мужской", callback_data="set_gender_male"))
    builder.add(InlineKeyboardButton(text="👩 Женский", callback_data="set_gender_female"))
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_settings"))
    
    builder.adjust(2, 1)
    
    return builder.as_markup()

def get_skip_name_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой пропуска имени"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="⏭️ Пропустить"))
    
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def get_confirmation_keyboard() -> InlineKeyboardMarkup:    
    """Клавиатура подтверждения регистрации"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_registration"))
    builder.add(InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_registration"))
    
    builder.adjust(2)
    
    return builder.as_markup()
