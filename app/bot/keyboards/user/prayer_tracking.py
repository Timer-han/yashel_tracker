from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict
from ....core.config import config
from ....core.database.models.prayer import Prayer

def get_prayer_tracking_keyboard(prayers: List[Prayer]) -> InlineKeyboardMarkup:
    """Клавиатура для отслеживания намазов"""
    builder = InlineKeyboardBuilder()
    
    # Разделяем намазы на обычные и сафар
    regular_prayers = []
    safar_prayers = []
    
    prayer_order = ['fajr', 'zuhr', 'asr', 'maghrib', 'isha', 'witr']  # Порядок обычных намазов
    safar_order = ['zuhr_safar', 'asr_safar', 'isha_safar']  # Порядок сафар намазов
    
    # Сначала добавляем обычные намазы в правильном порядке
    for prayer_type in prayer_order:
        prayer_data = next((p for p in prayers if p.prayer_type == prayer_type), None)
        if prayer_data and prayer_data.remaining > 0:
            prayer_name = config.PRAYER_TYPES[prayer_type]
            builder.add(
                InlineKeyboardButton(text="➖", callback_data=f"prayer_dec_{prayer_type}"),
                InlineKeyboardButton(text=f"{prayer_name}: {prayer_data.remaining}", callback_data=f"prayer_info_{prayer_type}"),
                InlineKeyboardButton(text="➕", callback_data=f"prayer_inc_{prayer_type}")
            )
    
    # Добавляем разделитель, если есть и обычные, и сафар намазы
    has_regular = any(p for p in prayers if p.prayer_type in prayer_order and p.remaining > 0)
    has_safar = any(p for p in prayers if p.prayer_type in safar_order and p.remaining > 0)
    
    if has_regular and has_safar:
        builder.add(InlineKeyboardButton(text="✈️ — Сафар намазы — ✈️", callback_data="safar_divider"))
    
    # Затем добавляем сафар намазы
    for prayer_type in safar_order:
        prayer_data = next((p for p in prayers if p.prayer_type == prayer_type), None)
        if prayer_data and prayer_data.remaining > 0:
            prayer_name = config.PRAYER_TYPES[prayer_type]
            builder.add(
                InlineKeyboardButton(text="➖", callback_data=f"prayer_dec_{prayer_type}"),
                InlineKeyboardButton(text=f"{prayer_name}: {prayer_data.remaining}", callback_data=f"prayer_info_{prayer_type}"),
                InlineKeyboardButton(text="➕", callback_data=f"prayer_inc_{prayer_type}")
            )
    
    # Дополнительные кнопки
    builder.add(InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats"))
    builder.add(InlineKeyboardButton(text="🔄 Сброс", callback_data="reset_prayers"))
    builder.add(InlineKeyboardButton(text="⚙️ Настройки", callback_data="prayer_settings"))
    
    # Настраиваем расположение
    regular_rows = len([p for p in prayers if p.prayer_type in prayer_order and p.remaining > 0])
    safar_rows = len([p for p in prayers if p.prayer_type in safar_order and p.remaining > 0])
    
    adjust_pattern = [3] * regular_rows
    
    if has_regular and has_safar:
        adjust_pattern += [1]  # Для разделителя
    
    adjust_pattern += [3] * safar_rows
    adjust_pattern += [1, 1, 1]  # Для дополнительных кнопок
    
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
