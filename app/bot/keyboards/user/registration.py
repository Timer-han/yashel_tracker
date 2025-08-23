from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# Основные клавиатуры
def get_gender_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора пола"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="👨 Мужской", callback_data="gender:male"),
        InlineKeyboardButton(text="👩 Женский", callback_data="gender:female")
    )
    builder.adjust(2)
    return builder.as_markup()

def get_childbirth_count_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора количества родов"""
    builder = InlineKeyboardBuilder()
    
    # Быстрые варианты
    for i in range(6):  # 0-5 родов
        text = "Не было" if i == 0 else str(i)
        builder.add(InlineKeyboardButton(text=text, callback_data=f"births:{i}"))
    
    # Кнопка для ввода большего числа
    builder.add(InlineKeyboardButton(text="6+ (ввести)", callback_data="births:manual"))
    
    builder.adjust(3, 3, 1)
    return builder.as_markup()

def get_hayd_duration_presets_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с предустановленными значениями хайда"""
    builder = InlineKeyboardBuilder()
    
    # Популярные значения
    common_values = [3, 4, 5, 6, 7, 8]
    for days in common_values:
        builder.add(InlineKeyboardButton(text=f"{days} дней", callback_data=f"hayd:{days}"))
    
    builder.add(InlineKeyboardButton(text="Другое (ввести)", callback_data="hayd:manual"))
    builder.adjust(3, 3, 1)
    return builder.as_markup()

def get_nifas_duration_presets_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с предустановленными значениями нифаса"""
    builder = InlineKeyboardBuilder()
    
    # Популярные значения нифаса
    common_values = [20, 30, 40]
    for days in common_values:
        builder.add(InlineKeyboardButton(text=f"{days} дней", callback_data=f"nifas:{days}"))
    
    builder.add(InlineKeyboardButton(text="Другое (ввести)", callback_data="nifas:manual"))
    builder.adjust(3, 1)
    return builder.as_markup()

def get_use_default_hayd_keyboard(default_days: float) -> InlineKeyboardMarkup:
    """Клавиатура для использования значения хайда по умолчанию"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=f"Использовать {default_days} дней", callback_data=f"hayd:{default_days}"),
        InlineKeyboardButton(text="Ввести другое значение", callback_data="hayd:manual")
    )
    builder.adjust(1, 1)
    return builder.as_markup()

def get_data_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения регистрационных данных"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ Все верно", callback_data="confirm:yes"),
        InlineKeyboardButton(text="✏️ Изменить", callback_data="confirm:edit")
    )
    builder.adjust(2)
    return builder.as_markup()

def get_navigation_keyboard(back_action: str = None, skip_action: str = None) -> InlineKeyboardMarkup:
    """Универсальная навигационная клавиатура"""
    builder = InlineKeyboardBuilder()
    
    if back_action:
        builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data=back_action))
    if skip_action:
        builder.add(InlineKeyboardButton(text="⏭️ Пропустить", callback_data=skip_action))
        
    if back_action and skip_action:
        builder.adjust(2)
    else:
        builder.adjust(1)
        
    return builder.as_markup()

# Специальные клавиатуры для текстового ввода
def get_text_input_reminder_keyboard(continue_action: str) -> InlineKeyboardMarkup:
    """Напоминание о текстовом вводе с кнопкой продолжения"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📝 Ввести текстом", callback_data=continue_action))
    return builder.as_markup()

def get_gender_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора пола"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="👨 Мужской"))
    builder.add(KeyboardButton(text="👩 Женский"))
    
    builder.adjust(2)
    
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def get_inline_gender_keyboard() -> InlineKeyboardMarkup:  # Возвращает InlineKeyboardMarkup!
    """Клавиатура выбора пола (inline версия)"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(text="👨 Мужской", callback_data="gender_male_edit"),
        InlineKeyboardButton(text="👩 Женский", callback_data="gender_female_edit")  
    )
    
    builder.adjust(2)
    
    return builder.as_markup()  # InlineKeyboardMarkup, не ReplyKeyboardMarkup!

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
