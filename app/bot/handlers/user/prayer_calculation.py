from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import date, datetime
import logging

from ...keyboards.user.prayer_calc import get_calculation_method_keyboard, get_prayer_types_keyboard
from ...keyboards.user.main_menu import get_main_menu_keyboard
from ...keyboards.user.prayer_calc import get_prayer_type_selection_keyboard
from ....core.services.calculation_service import CalculationService
from ....core.services.prayer_service import PrayerService
from ....core.services.user_service import UserService
from ....core.config import config
from ...states.prayer_calculation import PrayerCalculationStates
from ...utils.date_utils import parse_date, format_date

logger = logging.getLogger(__name__)
router = Router()
calculation_service = CalculationService()
prayer_service = PrayerService()
user_service = UserService()

@router.message(F.text == "🔢 Расчет намазов")
async def start_prayer_calculation(message: Message, state: FSMContext):
    """Начало расчета намазов"""
    await state.clear()
    
    await message.answer(
        "🔢 Выберите способ расчета пропущенных намазов:",
        reply_markup=get_calculation_method_keyboard()
    )
    await state.set_state(PrayerCalculationStates.choosing_method)

@router.callback_query(PrayerCalculationStates.choosing_method, F.data == "calc_from_age")
async def calc_from_age(callback: CallbackQuery, state: FSMContext):
    """Расчет от возраста совершеннолетия"""
    await callback.message.edit_text(
        "📅 Этот метод рассчитает намазы от 12 лет до даты, когда вы начали регулярно совершать намазы.\n\n"
        "Введите дату, когда вы начали регулярно совершать 5 намазов в день в формате ДД.ММ.ГГГГ:\n"
        "Например: 01.01.2020"
    )
    await state.set_state(PrayerCalculationStates.waiting_for_prayer_start_date)

@router.message(PrayerCalculationStates.waiting_for_prayer_start_date)
async def process_prayer_start_date(message: Message, state: FSMContext):
    """Обработка даты начала совершения намазов"""
    prayer_start_date = parse_date(message.text)
    if not prayer_start_date:
        await message.answer("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
        return
    
    # Получаем данные пользователя
    user = await user_service.get_or_create_user(message.from_user.id)
    if not user.birth_date:
        await message.answer("❌ Для этого расчета нужна ваша дата рождения. Пройдите регистрацию сначала.")
        return
    
    # Рассчитываем намазы
    prayers_data = calculation_service.calculate_prayers_from_age(
        birth_date=user.birth_date,
        prayer_start_date=prayer_start_date
    )
    
    # Сохраняем результат
    await prayer_service.set_user_prayers(message.from_user.id, prayers_data)
    
    # Показываем результат
    total_prayers = sum(prayers_data.values())
    result_text = (
        f"✅ Расчет завершен!\n\n"
        f"📊 Рассчитано намазов от {calculation_service.calculate_age(user.birth_date, user.birth_date.replace(year=user.birth_date.year + config.ADULT_AGE))} лет "
        f"до {format_date(prayer_start_date)}:\n\n"
        f"📝 **Всего пропущенных намазов: {total_prayers}**\n\n"
        "Детализация:\n"
    )
    
    for prayer_type, count in prayers_data.items():
        if count > 0:
            prayer_name = config.PRAYER_TYPES[prayer_type]
            result_text += f"• {prayer_name}: {count}\n"
    
    result_text += "\n🤲 Пусть Аллах облегчит вам восполнение!"
    
    await message.answer(result_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    await state.clear()

@router.callback_query(PrayerCalculationStates.choosing_method, F.data == "calc_between_dates")
async def calc_between_dates(callback: CallbackQuery, state: FSMContext):
    """Расчет между двумя датами"""
    await callback.message.edit_text(
        "📅 Введите начальную дату (с какой даты считать) в формате ДД.ММ.ГГГГ:\n"
        "Например: 01.01.2015"
    )
    await state.set_state(PrayerCalculationStates.waiting_for_start_date)

@router.message(PrayerCalculationStates.waiting_for_start_date)
async def process_start_date(message: Message, state: FSMContext):
    """Обработка начальной даты"""
    start_date = parse_date(message.text)
    if not start_date:
        await message.answer("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
        return
    
    await state.update_data(start_date=start_date)
    
    await message.answer(
        "📅 Введите конечную дату (по какую дату считать) в формате ДД.ММ.ГГГГ:\n"
        "Например: 01.06.2020"
    )
    await state.set_state(PrayerCalculationStates.waiting_for_end_date)

@router.message(PrayerCalculationStates.waiting_for_end_date)
async def process_end_date(message: Message, state: FSMContext):
    """Обработка конечной даты"""
    end_date = parse_date(message.text)
    if not end_date:
        await message.answer("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
        return
    
    data = await state.get_data()
    start_date = data['start_date']
    
    if end_date <= start_date:
        await message.answer("❌ Конечная дата должна быть больше начальной даты.")
        return
    
    # Рассчитываем намазы
    prayers_data = calculation_service.calculate_prayers_between_dates(start_date, end_date)
    
    # Сохраняем результат
    await prayer_service.set_user_prayers(message.from_user.id, prayers_data)
    
    # Показываем результат
    total_prayers = sum(prayers_data.values())
    days_count = (end_date - start_date).days
    
    result_text = (
        f"✅ Расчет завершен!\n\n"
        f"📊 Период: с {format_date(start_date)} по {format_date(end_date)}\n"
        f"📅 Количество дней: {days_count}\n\n"
        f"📝 **Всего пропущенных намазов: {total_prayers}**\n\n"
        "Детализация:\n"
    )
    
    for prayer_type, count in prayers_data.items():
        if count > 0:
            prayer_name = config.PRAYER_TYPES[prayer_type]
            result_text += f"• {prayer_name}: {count}\n"
    
    result_text += "\n🤲 Пусть Аллах облегчит вам восполнение!"
    
    await message.answer(result_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    await state.clear()

@router.callback_query(PrayerCalculationStates.choosing_method, F.data == "calc_manual")
async def calc_manual(callback: CallbackQuery, state: FSMContext):
    """Ручной ввод количества намазов"""
    await state.update_data(manual_prayers={})
    
    from ...keyboards.user.prayer_calc import get_prayer_type_selection_keyboard
    
    await callback.message.edit_text(
        "✋ **Ручной ввод намазов**\n\n"
        "Выберите тип намаза, для которого хотите указать количество пропущенных.",
        reply_markup=get_prayer_type_selection_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(PrayerCalculationStates.waiting_for_prayer_type_selection)

# Продолжение следует...


@router.callback_query(PrayerCalculationStates.waiting_for_prayer_type_selection, F.data.startswith("select_prayer_"))
async def process_prayer_type_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа намаза"""
    prayer_type = callback.data.replace("select_prayer_", "")
    
    # Сохраняем выбранный тип намаза
    await state.update_data(current_prayer_type=prayer_type)
    
    from ....core.config import config
    prayer_name = config.PRAYER_TYPES[prayer_type]
    
    await callback.message.edit_text(
        f"🕌 **{prayer_name}**\n\n"
        f"Введите количество пропущенных намазов типа '{prayer_name}':\n\n"
        "Например: 50"
    )
    await state.set_state(PrayerCalculationStates.waiting_for_manual_prayer_count)

@router.message(PrayerCalculationStates.waiting_for_manual_prayer_count)
async def process_manual_prayer_count(message: Message, state: FSMContext):
    """Обработка ввода количества намазов"""
    try:
        count = int(message.text)
        if count < 0:
            await message.answer("❌ Количество не может быть отрицательным.")
            return
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число.")
        return
    
    data = await state.get_data()
    prayer_type = data['current_prayer_type']
    manual_prayers = data.get('manual_prayers', {})
    
    # Сохраняем количество
    manual_prayers[prayer_type] = count
    await state.update_data(manual_prayers=manual_prayers)
    
    from ....core.config import config
    from ...keyboards.user.prayer_calc import get_prayer_type_selection_keyboard
    
    prayer_name = config.PRAYER_TYPES[prayer_type]
    
    # Показываем результат и возвращаем к выбору
    current_text = "✋ **Ручной ввод намазов**\n\n"
    current_text += "✅ Сохранено:\n"
    
    for p_type, p_count in manual_prayers.items():
        p_name = config.PRAYER_TYPES[p_type]
        current_text += f"• {p_name}: {p_count}\n"
    
    current_text += "\nВыберите следующий тип намаза или завершите ввод:"
    
    await message.answer(
        current_text,
        reply_markup=get_prayer_type_selection_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(PrayerCalculationStates.waiting_for_prayer_type_selection)

@router.callback_query(PrayerCalculationStates.waiting_for_prayer_type_selection, F.data == "finish_manual_input")
async def finish_manual_input(callback: CallbackQuery, state: FSMContext):
    """Завершение ручного ввода"""
    data = await state.get_data()
    manual_prayers = data.get('manual_prayers', {})
    
    # Проверяем, есть ли хотя бы один намаз
    total_prayers = sum(manual_prayers.values())
    if total_prayers == 0:
        await callback.answer("❌ Введите хотя бы один намаз", show_alert=True)
        return
    
    # Сохраняем результат
    await prayer_service.set_user_prayers(callback.from_user.id, manual_prayers)
    
    # Показываем результат
    result_text = (
        f"✅ Ручной ввод завершен!\n\n"
        f"📝 **Всего пропущенных намазов: {total_prayers}**\n\n"
        "Детализация:\n"
    )
    
    for prayer_type, count in manual_prayers.items():
        if count > 0:
            prayer_name = config.PRAYER_TYPES[prayer_type]
            result_text += f"• {prayer_name}: {count}\n"
    
    result_text += "\n🤲 Пусть Аллах облегчит вам восполнение!"
    
    await callback.message.edit_text(result_text, parse_mode="Markdown")
    await callback.message.answer(
        "🏠 Возвращаемся в главное меню",
        reply_markup=get_main_menu_keyboard()
    )
    await state.clear()

@router.callback_query(PrayerCalculationStates.choosing_method, F.data == "calc_custom_adult")
async def calc_custom_adult_dates(callback: CallbackQuery, state: FSMContext):
    """Расчет с заданием дат совершеннолетия"""
    await callback.message.edit_text(
        "📅 Этот метод позволяет указать точную дату совершеннолетия.\n\n"
        "Введите дату совершеннолетия (когда стали обязаны совершать намазы) в формате ДД.ММ.ГГГГ:\n"
        "Например: 15.03.2005"
    )
    await state.set_state(PrayerCalculationStates.waiting_for_adult_date)

@router.message(PrayerCalculationStates.waiting_for_adult_date)
async def process_adult_date(message: Message, state: FSMContext):
    """Обработка даты совершеннолетия"""
    adult_date = parse_date(message.text)
    if not adult_date:
        await message.answer("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
        return
    
    await state.update_data(adult_date=adult_date)
    
    await message.answer(
        "📅 Введите дату, когда вы начали регулярно совершать 5 намазов в день в формате ДД.ММ.ГГГГ:\n"
        "Например: 01.01.2020"
    )
    await state.set_state(PrayerCalculationStates.waiting_for_prayer_start_from_adult)

@router.message(PrayerCalculationStates.waiting_for_prayer_start_from_adult)
async def process_prayer_start_from_adult(message: Message, state: FSMContext):
    """Обработка даты начала намазов после указания даты совершеннолетия"""
    prayer_start_date = parse_date(message.text)
    if not prayer_start_date:
        await message.answer("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
        return
    
    data = await state.get_data()
    adult_date = data['adult_date']
    
    if prayer_start_date <= adult_date:
        await message.answer("❌ Дата начала намазов должна быть позже даты совершеннолетия.")
        return
    
    # Рассчитываем намазы
    prayers_data = calculation_service.calculate_prayers_from_dates(adult_date, prayer_start_date)
    
    # Сохраняем результат
    await prayer_service.set_user_prayers(message.from_user.id, prayers_data)
    
    # Показываем результат
    total_prayers = sum(prayers_data.values())
    days_count = (prayer_start_date - adult_date).days
    
    result_text = (
        f"✅ Расчет завершен!\n\n"
        f"📊 Период: с {format_date(adult_date)} по {format_date(prayer_start_date)}\n"
        f"📅 Количество дней: {days_count}\n\n"
        f"📝 **Всего пропущенных намазов: {total_prayers}**\n\n"
        "Детализация:\n"
    )
    
    for prayer_type, count in prayers_data.items():
        if count > 0:
            prayer_name = config.PRAYER_TYPES[prayer_type]
            result_text += f"• {prayer_name}: {count}\n"
    
    result_text += "\n🤲 Пусть Аллах облегчит вам восполнение!"
    
    await message.answer(result_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    await state.clear()