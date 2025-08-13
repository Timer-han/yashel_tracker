from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List
from ....core.config import config
from ....core.database.models.fast import Fast

def get_fast_tracking_keyboard(fasts: List[Fast]) -> InlineKeyboardMarkup:
    """Клавиатура для отслеживания постов"""
    builder = InlineKeyboardBuilder()
    
    # Порядок постов
    fast_order = ['ramadan', 'voluntary', 'oath', 'kaffarah']
    
    # Добавляем посты в вертикальном формате
    for fast_type in fast_order:
        fast_data = next((f for f in fasts if f.fast_type == fast_type), None)
        if fast_data and fast_data.remaining > 0:
            fast_name = config.FAST_TYPES[fast_type]
            
            # Строка с названием и количеством
            builder.add(InlineKeyboardButton(
                text=f"{fast_name}: {fast_data.remaining}", 
                callback_data=f"fast_info_{fast_type}"
            ))
            
            # Строка с кнопками + и -
            builder.add(
                InlineKeyboardButton(text="➖", callback_data=f"fast_dec_{fast_type}"),
                InlineKeyboardButton(text="➕", callback_data=f"fast_inc_{fast_type}")
            )
    
    # Дополнительные кнопки
    builder.add(InlineKeyboardButton(text="📊 Статистика", callback_data="show_fast_stats"))
    builder.add(InlineKeyboardButton(text="🔄 Сброс", callback_data="reset_fasts"))
    
    # Настраиваем расположение
    fasts_count = len([f for f in fasts if f.fast_type in fast_order and f.remaining > 0])
    
    # Формируем паттерн: для каждого поста [1 кнопка], [2 кнопки]
    adjust_pattern = []
    
    # Посты
    for _ in range(fasts_count):
        adjust_pattern.extend([1, 2])  # название, затем две кнопки
    
    # Дополнительные кнопки
    adjust_pattern.extend([1, 1])
    
    builder.adjust(*adjust_pattern)
    
    return builder.as_markup()

def get_fast_adjustment_keyboard(fast_type: str, current_remaining: int) -> InlineKeyboardMarkup:
    """Клавиатура для точной настройки постов"""
    builder = InlineKeyboardBuilder()
    
    # Кнопки уменьшения оставшихся (восполнение)
    builder.add(
        InlineKeyboardButton(text="-10", callback_data=f"fast_adjust_{fast_type}_-10"),
        InlineKeyboardButton(text="-5", callback_data=f"fast_adjust_{fast_type}_-5"),
        InlineKeyboardButton(text="-1", callback_data=f"fast_adjust_{fast_type}_-1")
    )
    
    # Кнопки увеличения оставшихся
    builder.add(
        InlineKeyboardButton(text="+10", callback_data=f"fast_adjust_{fast_type}_10"),
        InlineKeyboardButton(text="+5", callback_data=f"fast_adjust_{fast_type}_5"),
        InlineKeyboardButton(text="+1", callback_data=f"fast_adjust_{fast_type}_1")
    )
    
    builder.add(InlineKeyboardButton(text="✅ Готово", callback_data="fast_adjustment_done"))
    
    builder.adjust(3, 3, 1)
    
    return builder.as_markup()