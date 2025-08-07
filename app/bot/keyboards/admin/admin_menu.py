from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_admin_management_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления администраторами"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="➕ Добавить модератора", callback_data="add_moderator"))
    builder.add(InlineKeyboardButton(text="➕ Добавить админа", callback_data="add_admin"))
    
    builder.add(InlineKeyboardButton(text="👥 Список админов", callback_data="list_admins"))
    builder.add(InlineKeyboardButton(text="➖ Удалить админа", callback_data="remove_admin"))
    
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu"))
    
    builder.adjust(2, 2, 1)
    
    return builder.as_markup()

def get_role_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора роли"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(text="👮 Модератор", callback_data="role_moderator"),
        InlineKeyboardButton(text="👑 Админ", callback_data="role_admin")
    )
    
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_admin"))
    
    builder.adjust(2, 1)
    
    return builder.as_markup()

def get_admin_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действий админа"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_admin_action"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin_action")
    )
    
    builder.adjust(2)
    
    return builder.as_markup()
