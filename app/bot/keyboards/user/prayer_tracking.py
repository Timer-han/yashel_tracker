from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict
from ....core.config import config
from ....core.database.models.prayer import Prayer

def get_prayer_tracking_keyboard(prayers: List[Prayer]) -> InlineKeyboardMarkup:
    """Клавиатура для отслеживания намазов"""
    builder = InlineKeyboardBuilder()
    
    # Разделяем намазы на обычные и сафар
    prayer_order = ['fajr', 'zuhr', 'asr', 'maghrib', 'isha', 'witr']  # Порядок обычных намазов
    safar_order = ['zuhr_safar', 'asr_safar', 'isha_safar']  # Порядок сафар намазов
    
    # Сначала добавляем обычные намазы в вертикальном формате
    for prayer_type in prayer_order:
        prayer_data = next((p for p in prayers if p.prayer_type == prayer_type), None)
        if prayer_data and prayer_data.remaining > 0:
            prayer_name = config.PRAYER_TYPES[prayer_type]
            
            # Строка с названием и количеством
            builder.add(InlineKeyboardButton(
                text=f"{prayer_name}: {prayer_data.remaining}", 
                callback_data=f"prayer_info_{prayer_type}"
            ))
            
            # Строка с кнопками + и -
            builder.add(
                InlineKeyboardButton(text="➖", callback_data=f"prayer_dec_{prayer_type}"),
                InlineKeyboardButton(text="➕", callback_data=f"prayer_inc_{prayer_type}")
            )
    
    # Добавляем разделитель, если есть и обычные, и сафар намазы
    has_regular = any(p for p in prayers if p.prayer_type in prayer_order and p.remaining > 0)
    has_safar = any(p for p in prayers if p.prayer_type in safar_order and p.remaining > 0)
    
    if has_regular and has_safar:
        builder.add(InlineKeyboardButton(text="✈️ — Сафар намазы — ✈️", callback_data="safar_divider"))
    
    # Затем добавляем сафар намазы в том же формате
    for prayer_type in safar_order:
        prayer_data = next((p for p in prayers if p.prayer_type == prayer_type), None)
        if prayer_data and prayer_data.remaining > 0:
            prayer_name = config.PRAYER_TYPES[prayer_type]
            
            # Строка с названием и количеством
            builder.add(InlineKeyboardButton(
                text=f"{prayer_name}: {prayer_data.remaining}", 
                callback_data=f"prayer_info_{prayer_type}"
            ))
            
            # Строка с кнопками + и -
            builder.add(
                InlineKeyboardButton(text="➖", callback_data=f"prayer_dec_{prayer_type}"),
                InlineKeyboardButton(text="➕", callback_data=f"prayer_inc_{prayer_type}")
            )
    
    # Дополнительные кнопки
    builder.add(InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats"))
    builder.add(InlineKeyboardButton(text="🔄 Сброс", callback_data="reset_prayers"))
    builder.add(InlineKeyboardButton(text="⚙️ Настройки", callback_data="prayer_settings"))
    
    # Настраиваем расположение
    regular_count = len([p for p in prayers if p.prayer_type in prayer_order and p.remaining > 0])
    safar_count = len([p for p in prayers if p.prayer_type in safar_order and p.remaining > 0])
    
    # Формируем паттерн: для каждого намаза [1 кнопка], [2 кнопки]
    adjust_pattern = []
    
    # Обычные намазы
    for _ in range(regular_count):
        adjust_pattern.extend([1, 2])  # название, затем две кнопки
    
    # Разделитель
    if has_regular and has_safar:
        adjust_pattern.append(1)
    
    # Сафар намазы
    for _ in range(safar_count):
        adjust_pattern.extend([1, 2])  # название, затем две кнопки
    
    # Дополнительные кнопки
    adjust_pattern.extend([1, 1, 1])
    
    builder.adjust(*adjust_pattern)
    
    return builder.as_markup()


def get_prayer_adjustment_keyboard(prayer_type: str, current_remaining: int) -> InlineKeyboardMarkup:
    """Клавиатура для точной настройки намазов"""
    builder = InlineKeyboardBuilder()
    
    # Кнопки уменьшения оставшихся (восполнение)
    builder.add(
        InlineKeyboardButton(text="-10", callback_data=f"fast_adjust_{prayer_type}_-10"),
        InlineKeyboardButton(text="-5", callback_data=f"fast_adjust_{prayer_type}_-5"),
        InlineKeyboardButton(text="-1", callback_data=f"fast_adjust_{prayer_type}_-1")
    )
    
    # Кнопки увеличения оставшихся
    builder.add(
        InlineKeyboardButton(text="+10", callback_data=f"fast_adjust_{prayer_type}_10"),
        InlineKeyboardButton(text="+5", callback_data=f"fast_adjust_{prayer_type}_5"),
        InlineKeyboardButton(text="+1", callback_data=f"fast_adjust_{prayer_type}_1")
    )
    
    # НОВАЯ КНОПКА для ручного ввода
    builder.add(InlineKeyboardButton(text="✏️ Ввести вручную", callback_data=f"manual_input_{prayer_type}"))
    builder.add(InlineKeyboardButton(text="✅ Готово", callback_data="adjustment_done"))
    
    builder.adjust(3, 3, 2)  # Изменил последнюю строку
    
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

def get_prayer_category_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора категории намазов"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="🕌 Обычные намазы", callback_data="category_regular"))
    builder.add(InlineKeyboardButton(text="✈️ Сафар намазы", callback_data="category_safar"))
    builder.add(InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats"))
    builder.add(InlineKeyboardButton(text="🔄 Сброс", callback_data="reset_prayers"))
    
    builder.adjust(2, 2)
    
    return builder.as_markup()

def get_compact_prayer_tracking_keyboard(prayers: List[Prayer], category: str = "regular") -> InlineKeyboardMarkup:
    """Компактная клавиатура для отслеживания намазов с вертикальным расположением"""
    builder = InlineKeyboardBuilder()
    
    if category == "regular":
        prayer_order = ['fajr', 'zuhr', 'asr', 'maghrib', 'isha', 'witr']
    else:  # safar
        prayer_order = ['zuhr_safar', 'asr_safar', 'isha_safar']
    
    # Добавляем намазы в вертикальном формате
    for prayer_type in prayer_order:
        prayer_data = next((p for p in prayers if p.prayer_type == prayer_type), None)
        if prayer_data and prayer_data.remaining > 0:
            prayer_name = config.PRAYER_TYPES[prayer_type]
            
            # Название и количество
            builder.add(InlineKeyboardButton(
                text=f"{prayer_name}: {prayer_data.remaining}", 
                callback_data=f"prayer_info_{prayer_type}"
            ))
            
            # Кнопки - и +
            builder.add(
                InlineKeyboardButton(text="➖", callback_data=f"prayer_dec_{prayer_type}"),
                InlineKeyboardButton(text="➕", callback_data=f"prayer_inc_{prayer_type}")
            )
    
    # Навигационные кнопки
    if category == "regular":
        builder.add(InlineKeyboardButton(text="✈️ Сафар намазы", callback_data="switch_to_safar"))
    else:
        builder.add(InlineKeyboardButton(text="🕌 Обычные намазы", callback_data="switch_to_regular"))
    
    builder.add(InlineKeyboardButton(text="◀️ Назад к выбору", callback_data="back_to_categories"))
    
    # Настраиваем расположение: название, затем 2 кнопки для каждого намаза
    prayers_count = len([p for p in prayers if p.prayer_type in prayer_order and p.remaining > 0])
    adjust_pattern = [1, 2] * prayers_count + [1, 1]  # По 2 строки на каждый намаз + навигация
    
    builder.adjust(*adjust_pattern)
    
    return builder.as_markup()
