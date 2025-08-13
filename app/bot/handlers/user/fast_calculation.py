from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import date

from ...keyboards.user.fast_calc import get_fast_calculation_method_keyboard, get_fast_type_selection_keyboard
from ...keyboards.user.main_menu import get_main_menu_keyboard
from ....core.services.calculation_service import CalculationService
from ....core.services.fast_service import FastService
from ....core.services.user_service import UserService
from ....core.config import config
from ...states.fast_calculation import FastCalculationStates
from ...utils.date_utils import parse_date, format_date

router = Router()
calculation_service = CalculationService()
fast_service = FastService()
user_service = UserService()

@router.message(F.text == "🥗 Расчет постов")
async def start_fast_calculation(message: Message, state: FSMContext):
    """Начало расчета постов"""
    await state.clear()
    
    await message.answer(
        "🥗 Выберите способ расчета пропущенных постов:",
        reply_markup=get_fast_calculation_method_keyboard()
    )
    await state.set_state(FastCalculationStates.choosing_method)

@router.callback_query(FastCalculationStates.choosing_method, F.data == "fast_calc_from_age")
async def fast_calc_from_age(callback: CallbackQuery, state: FSMContext):
    """Расчет постов от возраста совершеннолетия"""
    await callback.message.edit_text(
        "📅 Этот метод рассчитает посты от возраста совершеннолетия до даты, когда вы начали регулярно поститься.\n\n"
        "Введите дату, когда вы начали регулярно соблюдать посты в формате ДД.ММ.ГГГГ:\n"
        "Например: 01.01.2020"
    )
    await state.set_state(FastCalculationStates.waiting_for_fast_start_date)

@router.message(FastCalculationStates.waiting_for_fast_start_date)
async def process_fast_start_date(message: Message, state: FSMContext):
    """Обработка даты начала соблюдения постов"""
    fast_start_date = parse_date(message.text)
    if not fast_start_date:
        await message.answer("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
        return
    
    # Получаем данные пользователя
    user = await user_service.get_or_create_user(message.from_user.id)
    if not user.birth_date:
        await message.answer("❌ Для этого расчета нужна ваша дата рождения. Пройдите регистрацию сначала.")
        return
    
    # Определяем возраст совершеннолетия
    adult_age = config.ADULT_AGE_FEMALE if user.gender == 'female' else config.ADULT_AGE_MALE
    adult_date = user.birth_date.replace(year=user.birth_date.year + adult_age)
    
    # Рассчитываем посты
    fast_count = calculation_service.calculate_fasts_between_dates(adult_date, fast_start_date)
    
    # Сохраняем результат (только Рамадан по умолчанию)
    fasts_data = {'ramadan': fast_count}
    await fast_service.set_user_fasts(message.from_user.id, fasts_data)
    
    # Показываем результат
    result_text = (
        f"✅ Расчет постов завершен!\n\n"
        f"📊 Рассчитано постов от {adult_age} лет до {format_date(fast_start_date)}:\n\n"
        f"🥗 **Всего пропущенных постов Рамадана: {fast_count}**\n\n"
        "🤲 Пусть Аллах облегчит вам восполнение!"
    )
    
    await message.answer(result_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    await state.clear()

@router.callback_query(FastCalculationStates.choosing_method, F.data == "fast_calc_between_dates")
async def fast_calc_between_dates(callback: CallbackQuery, state: FSMContext):
    """Расчет постов между двумя датами"""
    await callback.message.edit_text(
        "📅 Введите начальную дату (с какой даты считать посты) в формате ДД.ММ.ГГГГ:\n"
        "Например: 01.01.2015"
    )
    await state.set_state(FastCalculationStates.waiting_for_start_date)

@router.message(FastCalculationStates.waiting_for_start_date)
async def process_fast_start_date_between(message: Message, state: FSMContext):
    """Обработка начальной даты для постов"""
    start_date = parse_date(message.text)
    if not start_date:
        await message.answer("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
        return
    
    await state.update_data(start_date=start_date)
    
    await message.answer(
        "📅 Введите конечную дату (по какую дату считать посты) в формате ДД.ММ.ГГГГ:\n"
        "Например: 01.06.2020"
    )
    await state.set_state(FastCalculationStates.waiting_for_end_date)

@router.message(FastCalculationStates.waiting_for_end_date)
async def process_fast_end_date(message: Message, state: FSMContext):
    """Обработка конечной даты для постов"""
    end_date = parse_date(message.text)
    if not end_date:
        await message.answer("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
        return
    
    data = await state.get_data()
    start_date = data['start_date']
    
    if end_date <= start_date:
        await message.answer("❌ Конечная дата должна быть больше начальной даты.")
        return
    
    # Рассчитываем посты
    fast_count = calculation_service.calculate_fasts_between_dates(start_date, end_date)
    
    # Сохраняем результат
    fasts_data = {'ramadan': fast_count}
    await fast_service.set_user_fasts(message.from_user.id, fasts_data)
    
    # Показываем результат
    years_diff = end_date.year - start_date.year
    result_text = (
        f"✅ Расчет постов завершен!\n\n"
        f"📊 Период: с {format_date(start_date)} по {format_date(end_date)}\n"
        f"📅 Количество лет: {years_diff}\n\n"
        f"🥗 **Всего пропущенных постов Рамадана: {fast_count}**\n\n"
        "🤲 Пусть Аллах облегчит вам восполнение!"
    )
    
    await message.answer(result_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    await state.clear()

@router.callback_query(FastCalculationStates.choosing_method, F.data == "fast_calc_manual")
async def fast_calc_manual(callback: CallbackQuery, state: FSMContext):
    """Ручной ввод количества постов"""
    await state.update_data(manual_fasts={})
    
    await callback.message.edit_text(
        "✋ **Ручной ввод постов**\n\n"
        "Выберите тип поста, для которого хотите указать количество пропущенных.",
        reply_markup=get_fast_type_selection_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(FastCalculationStates.waiting_for_fast_type_selection)

@router.callback_query(FastCalculationStates.waiting_for_fast_type_selection, F.data.startswith("select_fast_"))
async def process_fast_type_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа поста"""
    fast_type = callback.data.replace("select_fast_", "")
    
    # Сохраняем выбранный тип поста
    await state.update_data(current_fast_type=fast_type)
    
    fast_name = config.FAST_TYPES[fast_type]
    
    await callback.message.edit_text(
        f"🥗 **{fast_name}**\n\n"
        f"Введите количество пропущенных постов типа '{fast_name}':\n\n"
        "Например: 50"
    )
    await state.set_state(FastCalculationStates.waiting_for_manual_fast_count)

@router.message(FastCalculationStates.waiting_for_manual_fast_count)
async def process_manual_fast_count(message: Message, state: FSMContext):
    """Обработка ввода количества постов"""
    try:
        count = int(message.text)
        if count < 0:
            await message.answer("❌ Количество не может быть отрицательным.")
            return
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число.")
        return
    
    data = await state.get_data()
    fast_type = data['current_fast_type']
    manual_fasts = data.get('manual_fasts', {})
    
    # Сохраняем количество
    manual_fasts[fast_type] = count
    await state.update_data(manual_fasts=manual_fasts)
    
    fast_name = config.FAST_TYPES[fast_type]
    
    # Показываем результат и возвращаем к выбору
    current_text = "✋ **Ручной ввод постов**\n\n"
    current_text += "✅ Сохранено:\n"
    
    for f_type, f_count in manual_fasts.items():
        f_name = config.FAST_TYPES[f_type]
        current_text += f"• {f_name}: {f_count}\n"
    
    current_text += "\nВыберите следующий тип поста или завершите ввод:"
    
    await message.answer(
        current_text,
        reply_markup=get_fast_type_selection_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(FastCalculationStates.waiting_for_fast_type_selection)

@router.callback_query(FastCalculationStates.waiting_for_fast_type_selection, F.data == "finish_manual_fast_input")
async def finish_manual_fast_input(callback: CallbackQuery, state: FSMContext):
    """Завершение ручного ввода постов"""
    data = await state.get_data()
    manual_fasts = data.get('manual_fasts', {})
    
    # Проверяем, есть ли хотя бы один пост
    total_fasts = sum(manual_fasts.values())
    if total_fasts == 0:
        await callback.answer("❌ Введите хотя бы один пост", show_alert=True)
        return
    
    # Сохраняем результат
    await fast_service.set_user_fasts(callback.from_user.id, manual_fasts)
    
    # Показываем результат
    result_text = (
        f"✅ Ручной ввод постов завершен!\n\n"
        f"🥗 **Всего пропущенных постов: {total_fasts}**\n\n"
        "Детализация:\n"
    )
    
    for fast_type, count in manual_fasts.items():
        if count > 0:
            fast_name = config.FAST_TYPES[fast_type]
            result_text += f"• {fast_name}: {count}\n"
    
    result_text += "\n🤲 Пусть Аллах облегчит вам восполнение!"
    
    await callback.message.edit_text(result_text, parse_mode="Markdown")
    await callback.message.answer(
        "🏠 Возвращаемся в главное меню",
        reply_markup=get_main_menu_keyboard()
    )
    await state.clear()