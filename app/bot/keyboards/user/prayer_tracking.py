from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict
from ....core.config import config
from ....core.database.models.prayer import Prayer

def get_prayer_tracking_keyboard(prayers: List[Prayer]) -> InlineKeyboardMarkup:
    """Клавиатура для отслеживания намазов"""
    builder = InlineKeyboardBuilder()
    
    # Создаем кнопки для каждого типа намаза
    for prayer_type, prayer_name in config.PRAYER_TYPES.items():
        # Находим данные о намазе
        prayer_data = next((p for p in prayers if p.prayer_type == prayer_type), None)
        remaining = prayer_data.remaining if prayer_data else 0
        
        if remaining > 0:
            # Кнопки уменьшения и увеличения
            builder.add(
                InlineKeyboardButton(text="➖", callback_data=f"prayer_dec_{prayer_type}"),
                InlineKeyboardButton(text=f"{prayer_name}: {remaining}", callback_data=f"prayer_info_{prayer_type}"),
                InlineKeyboardButton(text="➕", callback_data=f"prayer_inc_{prayer_type}")
            )
    
    # Дополнительные кнопки
    builder.add(InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats"))
    builder.add(InlineKeyboardButton(text="🔄 Сброс", callback_data="reset_prayers"))
    builder.add(InlineKeyboardButton(text="⚙️ Настройки", callback_data="prayer_settings"))
    
    # Настраиваем расположение: по 3 кнопки в ряду для намазов, затем по 1
    prayer_rows = len([p for p in prayers if p.remaining > 0])
    adjust_pattern = [3] * prayer_rows + [1, 1, 1]
    builder.adjust(*adjust_pattern)
    
    return builder.as_markup()

def get_prayer_adjustment_keyboard(prayer_type: str, current_count: int) -> InlineKeyboardMarkup:
    """Клавиатура для точной настройки намазов"""
    builder = InlineKeyboardBuilder()
    
    # Кнопки быстрого изменения
    builder.add(
        InlineKeyboardButton(text="-10", callback_data=f"adjust_{prayer_type}_-10"),
        InlineKeyboardButton(text="-5", callback_data=f"adjust_{prayer_type}_-5"),
        InlineKeyboardButton(text="-1", callback_data=f"adjust_{prayer_type}_-1")
    )
    
    builder.add(
        InlineKeyboardButton(text=f"{config.PRAYER_TYPES[prayer_type]}: {current_count}", 
                           callback_data=f"current_{prayer_type}")
    )
    
    builder.add(
        InlineKeyboardButton(text="+1", callback_data=f"adjust_{prayer_type}_1"),
        InlineKeyboardButton(text="+5", callback_data=f"adjust_{prayer_type}_5"),
        InlineKeyboardButton(text="+10", callback_data=f"adjust_{prayer_type}_10")
    )
    
    builder.add(InlineKeyboardButton(text="✅ Готово", callback_data="adjustment_done"))
    
    builder.adjust(3, 1, 3, 1)
    
    return builder.as_markup()

def get_reset_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения сброса"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(text="✅ Да, сбросить", callback_data="confirm_reset"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_reset")
    )
    
    builder.adjust(2)
    
    return builder.as_markup()
