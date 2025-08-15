from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List
from ....core.database.models.fast import Fast
from ....core.config import config

def get_fast_tracking_keyboard(fasts: List[Fast]) -> InlineKeyboardMarkup:
    """Клавиатура для отслеживания постов"""
    builder = InlineKeyboardBuilder()
    
    # Сортируем посты: сначала Рамадан по годам, затем остальные
    ramadan_fasts = sorted(
        [f for f in fasts if f.fast_type == 'ramadan'],
        key=lambda x: x.year or 0
    )
    other_fasts = [f for f in fasts if f.fast_type != 'ramadan']
    
    # Добавляем посты Рамадана
    for fast in ramadan_fasts:
        fast_name = f"Рамадан {fast.year}" if fast.year else "Рамадан"
        year_str = str(fast.year) if fast.year else "None"
        
        # Кнопка с информацией
        builder.add(InlineKeyboardButton(
            text=f"{fast_name}: {fast.remaining} дней",
            callback_data=f"fast_info_{fast.fast_type}_{year_str}"
        ))
        
        # Кнопки управления
        builder.add(
            InlineKeyboardButton(text="➖", callback_data=f"fast_dec_{fast.fast_type}_{year_str}"),
            InlineKeyboardButton(text="➕", callback_data=f"fast_inc_{fast.fast_type}_{year_str}")
        )
    
    # Добавляем другие посты
    for fast in other_fasts:
        fast_name = config.FAST_TYPES.get(fast.fast_type, fast.fast_type)
        
        builder.add(InlineKeyboardButton(
            text=f"{fast_name}: {fast.remaining} дней",
            callback_data=f"fast_info_{fast.fast_type}_None"
        ))
        
        builder.add(
            InlineKeyboardButton(text="➖", callback_data=f"fast_dec_{fast.fast_type}_None"),
            InlineKeyboardButton(text="➕", callback_data=f"fast_inc_{fast.fast_type}_None")
        )
    
    # Кнопка статистики
    builder.add(InlineKeyboardButton(
        text="📊 Статистика постов",
        callback_data="show_fast_stats"
    ))
    
    # Настраиваем расположение: название, затем 2 кнопки для каждого поста
    adjust_pattern = []
    total_fasts = len(ramadan_fasts) + len(other_fasts)
    
    for _ in range(total_fasts):
        adjust_pattern.extend([1, 2])  # название, затем две кнопки
    
    adjust_pattern.append(1)  # кнопка статистики
    
    builder.adjust(*adjust_pattern)
    
    return builder.as_markup()

def get_fast_adjustment_keyboard(fast_type: str, year: int = None, 
                                 current_remaining: int = 0) -> InlineKeyboardMarkup:
    """Клавиатура для точной настройки постов"""
    builder = InlineKeyboardBuilder()
    
    year_str = str(year) if year else "None"
    
    # Кнопки быстрого восполнения
    builder.add(
        InlineKeyboardButton(text="✅ +1", callback_data=f"fast_adjust_{fast_type}_{year_str}_1"),
        InlineKeyboardButton(text="✅ +5", callback_data=f"fast_adjust_{fast_type}_{year_str}_5"),
        InlineKeyboardButton(text="✅ +10", callback_data=f"fast_adjust_{fast_type}_{year_str}_10")
    )
    
    # Кнопки добавления пропущенных
    builder.add(
        InlineKeyboardButton(text="➕ +1", callback_data=f"fast_adjust_{fast_type}_{year_str}_-1"),
        InlineKeyboardButton(text="➕ +5", callback_data=f"fast_adjust_{fast_type}_{year_str}_-5"),
        InlineKeyboardButton(text="➕ +10", callback_data=f"fast_adjust_{fast_type}_{year_str}_-10")
    )
    
    # Кнопка возврата
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_fasts"))
    
    builder.adjust(3, 3, 1)
    
    return builder.as_markup()