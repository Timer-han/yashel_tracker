from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

def get_calculation_method_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора метода расчета"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="🔢 От 12 лет до начала намазов", 
        callback_data="calc_from_age"
    ))
    builder.add(InlineKeyboardButton(
        text="📅 Между двумя датами", 
        callback_data="calc_between_dates"
    ))
    builder.add(InlineKeyboardButton(
        text="📝 Задать даты совершеннолетия", 
        callback_data="calc_custom_adult"
    ))
    builder.add(InlineKeyboardButton(
        text="✋ Ввести вручную", 
        callback_data="calc_manual"
    ))
    
    builder.adjust(1)
    
    return builder.as_markup()

# def get_prayer_types_keyboard() -> InlineKeyboardMarkup:
#     """Клавиатура с типами намазов для ручного ввода"""
#     builder = InlineKeyboardBuilder()
    
#     from ....core.config import config
    
#     for prayer_type, prayer_name in config.PRAYER_TYPES.items():
#         builder.add(InlineKeyboardButton(
#             text=f"{prayer_name}: 0", 
#             callback_data=f"prayer_type_{prayer_type}_0"
#         ))
    
#     builder.add(InlineKeyboardButton(text="✅ Готово", callback_data="prayers_done"))
    
#     builder.adjust(2)
    
#     return builder.as_markup()

def get_prayer_types_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с типами намазов для ручного ввода"""
    builder = InlineKeyboardBuilder()
    
    from ....core.config import config
    
    for prayer_type, prayer_name in config.PRAYER_TYPES.items():
        builder.add(InlineKeyboardButton(
            text=f"{prayer_name}: 0", 
            callback_data=f"prayer_type_{prayer_type}_0"
        ))
    
    builder.add(InlineKeyboardButton(text="✅ Готово", callback_data="prayer_done_0"))
    
    builder.adjust(2)
    
    return builder.as_markup()

def get_updated_prayer_types_keyboard(manual_prayers: dict) -> InlineKeyboardMarkup:
    """Клавиатура с обновленными значениями намазов"""
    builder = InlineKeyboardBuilder()
    
    from ....core.config import config
    
    for prayer_type, prayer_name in config.PRAYER_TYPES.items():
        count = manual_prayers.get(prayer_type, 0)
        builder.add(InlineKeyboardButton(
            text=f"{prayer_name}: {count}", 
            callback_data=f"prayer_{prayer_type}_{count}"
        ))
    
    builder.add(InlineKeyboardButton(text="✅ Готово", callback_data="prayer_done_0"))
    
    builder.adjust(2)
    
    return builder.as_markup()