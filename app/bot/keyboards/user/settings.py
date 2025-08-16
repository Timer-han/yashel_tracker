from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_settings_menu_keyboard(notifications_enabled: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура меню настроек"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="⚧ Изменить пол", callback_data="change_gender"))
    builder.add(InlineKeyboardButton(text="📅 Изменить дату рождения", callback_data="change_birth_date"))
    builder.add(InlineKeyboardButton(text="🏙️ Изменить город", callback_data="change_city"))
    
    # Кнопка управления уведомлениями
    notification_text = "🔕 Отключить уведомления" if notifications_enabled else "🔔 Включить уведомления"
    notification_callback = "disable_notifications" if notifications_enabled else "enable_notifications"
    builder.add(InlineKeyboardButton(text=notification_text, callback_data=notification_callback))
    
    builder.add(InlineKeyboardButton(text="📤 Экспорт данных", callback_data="export_data"))
    builder.add(InlineKeyboardButton(text="🔄 Полный сброс", callback_data="reset_all_data"))
    
    builder.adjust(2, 2, 2)
    
    return builder.as_markup()

def get_change_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения изменений"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{action}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_{action}")
    )
    
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_settings"))
    
    builder.adjust(2, 1)
    
    return builder.as_markup()

def get_notifications_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения изменения уведомлений"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_notifications_change"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_notifications_change")
    )
    
    builder.adjust(2)
    
    return builder.as_markup()