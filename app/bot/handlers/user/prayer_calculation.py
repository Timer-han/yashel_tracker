from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from datetime import date, datetime
import logging

from ...keyboards.user.main_menu import get_main_menu_keyboard
from ...keyboards.user.prayer_calc import (
    get_male_calculation_method_keyboard,
    get_female_calculation_method_keyboard,
    get_yes_no_keyboard,
    get_births_count_keyboard,
    get_miscarriages_count_keyboard,
    get_hayd_duration_keyboard,
    get_nifas_duration_keyboard,
    get_calculation_confirmation_keyboard
)
from ....core.services.calculation_service import CalculationService
from ....core.services.prayer_service import PrayerService
from ....core.services.user_service import UserService
from ....core.config import config, escape_markdown
from ...states.prayer_calculation import PrayerCalculationStates
from ...utils.date_utils import parse_date, format_date

logger = logging.getLogger(__name__)
router = Router()
calculation_service = CalculationService()
prayer_service = PrayerService()
user_service = UserService()

# ======================================
# НАЧАЛЬНЫЙ ОБРАБОТЧИК
# ======================================

@router.message(F.text == "🔢 Расчет намазов")
async def start_prayer_calculation(message: Message, state: FSMContext):
    """Начало расчета намазов"""
    await state.clear()
    
    user = await user_service.get_or_create_user(message.from_user.id)
    
    if user.gender == 'male':
        await message.answer(
            "🔢 **Расчет пропущенных намазов**\n\n"
            "Выбери способ расчета:",
            reply_markup=get_male_calculation_method_keyboard(),
            parse_mode="MarkdownV2"
        )
    else:  # female
        await message.answer(
            "🔢 **Расчет пропущенных намазов**\n\n"
            "Выбери способ расчета:",
            reply_markup=get_female_calculation_method_keyboard(),
            parse_mode="MarkdownV2"
        )
    
    await state.set_state(PrayerCalculationStates.choosing_method)

# ====================================== 
# ОБРАБОТЧИКИ ДЛЯ МУЖЧИН
# ======================================

@router.callback_query(PrayerCalculationStates.choosing_method, F.data == "male_know_maturity")
async def male_know_maturity(callback: CallbackQuery, state: FSMContext):
    """Мужчина знает дату совершеннолетия"""
    await callback.message.edit_text(
        "📅 Введи дату своего совершеннолетия по исламу в формате ДД\.ММ\.ГГГГ:\n\n"
        "Например: 15\.03\.2010",
        parse_mode="MarkdownV2"
    )
    await state.set_state(PrayerCalculationStates.male_maturity_date_input)

@router.message(PrayerCalculationStates.male_maturity_date_input)
async def process_male_maturity_date(message: Message, state: FSMContext):
    """Обработка даты совершеннолетия мужчины"""
    maturity_date, error = validate_date_input(message.text, max_date=date.today())
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    await state.update_data(maturity_date=maturity_date)
    
    await message.answer(
        "📅 Введи дату, когда начал регулярно совершать 6 намазов в день в формате ДД\.ММ\.ГГГГ:\n\n"
        "Например: 01\.09\.2020",
        parse_mode="MarkdownV2"
    )
    await state.set_state(PrayerCalculationStates.male_prayer_start_date_input)

@router.message(PrayerCalculationStates.male_prayer_start_date_input)
async def process_male_prayer_start_date(message: Message, state: FSMContext):
    """Обработка даты начала намазов мужчины"""
    data = await state.get_data()
    maturity_date = data['maturity_date']
    
    prayer_start_date, error = validate_date_input(message.text, min_date=maturity_date, max_date=date.today())
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    # Рассчитываем намазы
    prayers_data = calculation_service.calculate_male_prayers_simple(maturity_date, prayer_start_date)
    
    # Сохраняем результат
    await prayer_service.set_user_prayers(message.from_user.id, prayers_data)
    
    # Показываем результат
    result_text = calculation_service.format_calculation_summary(
        prayers_data,
        {
            'start_date': format_date(maturity_date),
            'end_date': format_date(prayer_start_date)
        }
    )
    
    await message.answer(escape_markdown(result_text, "()-?.!_="), reply_markup=get_main_menu_keyboard(), parse_mode="MarkdownV2")
    await state.clear()

@router.callback_query(PrayerCalculationStates.choosing_method, F.data == "male_manual")
async def male_manual_input(callback: CallbackQuery, state: FSMContext):
    """Ручной ввод намазов для мужчины"""
    await callback.message.edit_text(
        "✋ **Ручной ввод количества намазов**\n\n"
        "Введи общее количество пропущенных дней:\n\n"
        "Например: 1500",
        parse_mode="MarkdownV2"
    )
    await state.set_state(PrayerCalculationStates.manual_input_count)

@router.callback_query(PrayerCalculationStates.choosing_method, F.data == "male_learn")
async def male_learn_to_calculate(callback: CallbackQuery, state: FSMContext):
    """Обучение расчету для мужчины"""
    await callback.message.edit_text(
        "🎓 **Учимся считать намазы самостоятельно**\n\n"
        "Ты помнишь дату своего совершеннолетия?\n\n"
        "💡 Если не помнишь, спроси у родных, раскопай архивы, вспомни события 12\-15\-летнего возраста\. "
        "Если совсем не помнишь, то возьми за возраст совершеннолетия 11\.5 лет\.",
        reply_markup=get_yes_no_keyboard("male_learn_remember_yes", "male_learn_remember_no"),
        parse_mode="MarkdownV2"
    )
    await state.set_state(PrayerCalculationStates.male_learning_remember_maturity)

@router.callback_query(PrayerCalculationStates.male_learning_remember_maturity, F.data.startswith("male_learn_remember_"))
async def process_male_learn_remember(callback: CallbackQuery, state: FSMContext):
    """Обработка ответа о памяти даты совершеннолетия"""
    remembers = callback.data == "male_learn_remember_yes"
    
    if not remembers:
        user = await user_service.get_or_create_user(callback.from_user.id)
        if user.birth_date:
            estimated_maturity = calculation_service.estimate_maturity_age(user.birth_date, False)
            await state.update_data(maturity_date=estimated_maturity, estimated=True)
            text = f"📅 Используем приблизительную дату совершеннолетия: {format_date(estimated_maturity)}\n\n"
        else:
            await callback.message.edit_text(
                "❌ Нужна дата рождения для оценки\. Пройди регистрацию или введи дату совершеннолетия вручную\.",
                parse_mode="MarkdownV2"
            )
            return
    else:
        text = ""
    
    text += ("Ты знаешь дату, когда начал стабильно совершать 6 намазов в день?\n\n"
             "💡 Если не знаешь точно, возьми дату, в которую ты уже точно читал 6 намазов ежедневно\.")
    
    await callback.message.edit_text(
        text,
        reply_markup=get_yes_no_keyboard("male_learn_know_start_yes", "male_learn_know_start_no"),
        parse_mode="MarkdownV2"
    )
    await state.set_state(PrayerCalculationStates.male_learning_know_prayer_start)

@router.callback_query(PrayerCalculationStates.male_learning_know_prayer_start, F.data.startswith("male_learn_know_start_"))
async def process_male_learn_prayer_start(callback: CallbackQuery, state: FSMContext):
    """Обработка знания даты начала намазов"""
    knows_start = callback.data == "male_learn_know_start_yes"
    await state.update_data(knows_prayer_start=knows_start)
    
    await callback.message.edit_text(
        "🤔 Были ли ещё периоды, когда ты не читал намаз?\n\n"
        "Например: болезнь, путешествия, забывчивость и т\.д\.",
        reply_markup=get_yes_no_keyboard("male_learn_breaks_yes", "male_learn_breaks_no"),
        parse_mode="MarkdownV2"
    )
    await state.set_state(PrayerCalculationStates.male_learning_had_breaks)

@router.callback_query(PrayerCalculationStates.male_learning_had_breaks, F.data == "male_learn_breaks_yes")
async def male_learn_had_breaks(callback: CallbackQuery, state: FSMContext):
    """У мужчины были перерывы в намазах"""
    await callback.message.edit_text(
        "📊 Посчитай суммарное количество пропущенных дней и введи его:\n\n"
        "Например: 180",
        parse_mode="MarkdownV2"
    )
    await state.set_state(PrayerCalculationStates.male_learning_breaks_days_input)

@router.callback_query(PrayerCalculationStates.male_learning_had_breaks, F.data == "male_learn_breaks_no")
async def male_learn_no_breaks(callback: CallbackQuery, state: FSMContext):
    """У мужчины не было перерывов"""
    await state.update_data(break_days=0)
    await ask_male_final_input(callback, state)

@router.message(PrayerCalculationStates.male_learning_breaks_days_input)
async def process_male_break_days(message: Message, state: FSMContext):
    """Обработка дней перерывов"""
    break_days, error = validate_number_input(message.text, min_val=0, integer_only=True)
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    await state.update_data(break_days=break_days)
    
    # Создаем фиктивный callback для совместимости
    class FakeCallback:
        def __init__(self, message):
            self.message = message
    
    await ask_male_final_input(FakeCallback(message), state, is_message=True)

async def ask_male_final_input(callback_or_message, state: FSMContext, is_message=False):
    """Запрос финального ввода количества намазов"""
    text = ("📝 Теперь введи общее количество пропущенных намазов:\n\n"
            "💡 Это может быть количество дней × 6 намазов \+ дополнительные пропуски")
    
    if is_message:
        await callback_or_message.message.answer(text, parse_mode="MarkdownV2")
    else:
        await callback_or_message.message.edit_text(text, parse_mode="MarkdownV2")
    
    await state.set_state(PrayerCalculationStates.male_learning_final_count_input)

@router.message(PrayerCalculationStates.male_learning_final_count_input)
async def process_male_final_count(message: Message, state: FSMContext):
    """Финальная обработка количества намазов для мужчины"""
    total_count, error = validate_number_input(message.text, min_val=0, integer_only=True)
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    # Распределяем поровну между всеми намазами
    per_prayer = int(total_count // 6)
    
    prayers_data = {
        'fajr': per_prayer,
        'zuhr': per_prayer,
        'asr': per_prayer,
        'maghrib': per_prayer,
        'isha': per_prayer,
        'witr': per_prayer,
        'zuhr_safar': 0,
        'asr_safar': 0,
        'isha_safar': 0
    }
    
    # Сохраняем результат
    await prayer_service.set_user_prayers(message.from_user.id, prayers_data)
    
    result_text = calculation_service.format_calculation_summary(prayers_data)
    
    await message.answer(escape_markdown(result_text, "()-?.!_="), reply_markup=get_main_menu_keyboard(), parse_mode="MarkdownV2")
    await state.clear()

@router.message(PrayerCalculationStates.manual_input_count)
async def process_manual_count_input(message: Message, state: FSMContext):
    """Обработка ручного ввода количества намазов"""
    total_count, error = validate_number_input(message.text, min_val=0, integer_only=True)
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    # Распределяем поровну между всеми намазами
    per_prayer = int(total_count)
    
    prayers_data = {
        'fajr': per_prayer,
        'zuhr': per_prayer,
        'asr': per_prayer,
        'maghrib': per_prayer,
        'isha': per_prayer,
        'witr': per_prayer,
        'zuhr_safar': 0,
        'asr_safar': 0,
        'isha_safar': 0
    }
    
    # Сохраняем результат
    await prayer_service.set_user_prayers(message.from_user.id, prayers_data)
    
    result_text = calculation_service.format_calculation_summary(prayers_data)
    
    await message.answer(escape_markdown(result_text, "()-?.!_="), reply_markup=get_main_menu_keyboard(), parse_mode="MarkdownV2")
    await state.clear()

# ======================================
# ОБРАБОТЧИКИ ДЛЯ ЖЕНЩИН
# ======================================

@router.callback_query(PrayerCalculationStates.choosing_method, F.data == "female_manual")
async def female_manual_input(callback: CallbackQuery, state: FSMContext):
    """Ручной ввод намазов для женщины"""
    await callback.message.edit_text(
        "✋ **Ручной ввод количества намазов**\n\n"
        "Введи общее количество пропущенных дней:\n\n"
        "Например: 1200",
        parse_mode="MarkdownV2"
    )
    await state.set_state(PrayerCalculationStates.manual_input_count)

@router.callback_query(PrayerCalculationStates.choosing_method, F.data == "female_guide")
async def female_detailed_guide(callback: CallbackQuery, state: FSMContext):
    """Подробный гайд для женщин"""
    guide_text = escape_markdown("""
📖 **Подробный гайд по вычислению намазов для женщин**

**Основные принципы:**

🕌 **Что учитываем:**
• Дата совершеннолетия (первые месячные)
• Периоды хайда (месячных) - НЕ читаем намаз
• Периоды нифаса (послеродовые кровотечения) - НЕ читаем намаз
• Роды и выкидыши
• Менопауза (если была)

⚖️ **По ханафитскому мазхабу:**
• Минимальная продолжительность хайда: 3 дня (72 часа)
• Максимальная продолжительность хайда: 10 дней (240 часов)
• Максимальная продолжительность нифаса: 40 дней (960 часов)
• Между месячными должно пройти минимум 15 дней (360 ч)

🔬 **Как считаем:**
1. Берем весь период от совершеннолетия до начала чтения 6 намазов
2. Вычитаем все дни нифаса, которые попали в этот период
3. Вычитаем дни хайда (рассчитываем по периодам между событиями)
4. Если была менопауза - прибавляем дни от менопаузы до начала намазов
5. Получаем итоговое количество дней = количество каждого вида намазов

📚 **Рекомендуем изучить самостоятельно темы "хайд", "нифас" и "истихада" для более точного расчета.**

Введи количество пропущенных дней:""", "()-?.!_=")
    
    await callback.message.edit_text(guide_text, parse_mode="MarkdownV2")
    await state.set_state(PrayerCalculationStates.manual_input_count)

@router.callback_query(PrayerCalculationStates.choosing_method, F.data.startswith("female_"))
async def start_female_detailed_calculation(callback: CallbackQuery, state: FSMContext):
    """Начало детального расчета для женщин"""
    method = callback.data
    
    if method == "female_know_maturity":
        text = ("📅 Напоминаем, что совершеннолетие по исламу наступает с приходом первого хайда \(месячных\)\.\n\n"
                "Укажи дату совершеннолетия в формате ДД\.ММ\.ГГГГ:\n\n"
                "Например: 10\.05\.2015")
        await state.set_state(PrayerCalculationStates.female_maturity_date_input)
    else:  # female_no_maturity
        text = ("🤔 Спроси у родных, раскопай архивы, вспомни события своего 9\-15\-летнего возраста\.\n\n"
                "Если не помнишь, то возьми за возраст совершеннолетия 8\.5 лет\.\n\n"
                "Укажи дату совершеннолетия в формате ДД\.ММ\.ГГГГ:\n\n"
                "Например: 15\.08\.2012")
        await state.set_state(PrayerCalculationStates.female_no_maturity_date_input)
    
    await callback.message.edit_text(text, parse_mode="MarkdownV2")

# ПРОДОЛЖЕНИЕ ЖЕНСКИХ ОБРАБОТЧИКОВ

@router.message(PrayerCalculationStates.female_maturity_date_input)
@router.message(PrayerCalculationStates.female_no_maturity_date_input)
async def process_female_maturity_date(message: Message, state: FSMContext):
    """Обработка даты совершеннолетия женщины"""
    maturity_date, error = validate_date_input(message.text, max_date=date.today())
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    await state.update_data(maturity_date=maturity_date)
    
    cycle_info_text = escape_markdown("""
🌙 Регулярный ли у тебя цикл?

По ханафитскому мазхабу:
• Минимальная продолжительность хайда: 3 дня (72 часа)
• Максимальная продолжительность хайда: 10 дней (240 часов)

Если хайд продолжается более 10 дней, то посмотри на продолжительность прошлого хайда и из 10 дней вычти это число - эти дни истихада (период кровотечения), в который необходимо совершать намаз.

Между месячными должно пройти не менее 15 дней (360 ч). Если меньше - это истихада, не хайд.

Советуем самостоятельно изучить тему "хайда" для более корректного подсчета.""", "()-?.!_=")
    
    await message.answer(
        cycle_info_text,
        reply_markup=get_yes_no_keyboard("female_regular_yes", "female_regular_no"),
        parse_mode="MarkdownV2"
    )
    await state.set_state(PrayerCalculationStates.female_regular_cycle_question)

@router.callback_query(PrayerCalculationStates.female_regular_cycle_question, F.data.startswith("female_regular_"))
async def process_female_cycle_regularity(callback: CallbackQuery, state: FSMContext):
    """Обработка регулярности цикла"""
    regular_cycle = callback.data == "female_regular_yes"
    await state.update_data(regular_cycle=regular_cycle)
    
    if regular_cycle:
        await callback.message.edit_text(
            "📏 Введи продолжительность хайда в днях:",
            reply_markup=get_hayd_duration_keyboard()
        )
        await state.set_state(PrayerCalculationStates.female_cycle_length_input)
    else:
        await callback.message.edit_text(
            "📊 Фиксируешь ли ты дни хайда с совершеннолетия?",
            reply_markup=get_yes_no_keyboard("female_track_yes", "female_track_no"),
            parse_mode="MarkdownV2"
        )
        await state.set_state(PrayerCalculationStates.female_track_hayd_question)

@router.callback_query(PrayerCalculationStates.female_cycle_length_input, F.data.startswith("hayd_days_"))
async def process_female_hayd_duration(callback: CallbackQuery, state: FSMContext):
    """Обработка продолжительности хайда"""
    if callback.data == "hayd_days_manual":
        await callback.message.edit_text(
            "📏 Введи продолжительность хайда в днях \(от 3 до 10\):\n\n"
            "Например: 5",
            parse_mode="MarkdownV2"
        )
        return
    
    hayd_days = int(callback.data.split("_")[2])
    await state.update_data(hayd_average_days=hayd_days)
    await ask_about_births(callback, state)

@router.message(PrayerCalculationStates.female_cycle_length_input)
async def process_female_hayd_duration_manual(message: Message, state: FSMContext):
    """Обработка ручного ввода продолжительности хайда"""
    hayd_days, error = validate_number_input(message.text, min_val=3, max_val=10)
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    await state.update_data(hayd_average_days=hayd_days)
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
    
    await ask_about_births(FakeCallback(message), state, is_message=True)

@router.callback_query(PrayerCalculationStates.female_track_hayd_question, F.data.startswith("female_track_"))
async def process_female_track_hayd(callback: CallbackQuery, state: FSMContext):
    """Обработка вопроса о фиксации хайда"""
    tracks_hayd = callback.data == "female_track_yes"
    await state.update_data(tracks_hayd=tracks_hayd)
    
    if tracks_hayd:
        await callback.message.edit_text(
            "📊 Введи количество дней хайда за весь период:\n\n"
            "Например: 180",
            parse_mode="MarkdownV2"
        )
        await state.set_state(PrayerCalculationStates.female_total_hayd_days_input)
    else:
        await callback.message.edit_text(
            "📏 Введи среднюю продолжительность хайда с момента совершеннолетия до родов/выкидыша, если они были:",
            reply_markup=get_hayd_duration_keyboard()
        )
        await state.set_state(PrayerCalculationStates.female_average_hayd_input)

@router.message(PrayerCalculationStates.female_total_hayd_days_input)
async def process_female_total_hayd_days(message: Message, state: FSMContext):
    """Обработка общего количества дней хайда"""
    total_hayd_days, error = validate_number_input(message.text, min_val=0, integer_only=True)
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    await state.update_data(total_hayd_days=total_hayd_days)
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
    
    await ask_about_births(FakeCallback(message), state, is_message=True)

@router.callback_query(PrayerCalculationStates.female_average_hayd_input, F.data.startswith("hayd_days_"))
async def process_female_average_hayd(callback: CallbackQuery, state: FSMContext):
    """Обработка средней продолжительности хайда"""
    if callback.data == "hayd_days_manual":
        await callback.message.edit_text(
            "📏 Введи среднюю продолжительность хайда в днях:\n\n"
            "Например: 5",
            parse_mode="MarkdownV2"
        )
        return
    
    hayd_days = int(callback.data.split("_")[2])
    await state.update_data(hayd_average_days=hayd_days)
    await ask_about_births(callback, state)

@router.message(PrayerCalculationStates.female_average_hayd_input)
async def process_female_average_hayd_manual(message: Message, state: FSMContext):
    """Обработка ручного ввода средней продолжительности хайда"""
    hayd_days, error = validate_number_input(message.text, min_val=0)
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    await state.update_data(hayd_average_days=hayd_days)
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
    
    await ask_about_births(FakeCallback(message), state, is_message=True)

async def ask_about_births(callback_or_message, state: FSMContext, is_message=False):
    """Вопрос о родах"""
    text = "👶 Были ли у тебя роды\? \(Роды, не выкидыши\)"
    keyboard = get_yes_no_keyboard("female_births_yes", "female_births_no")
    
    if is_message:
        await callback_or_message.message.answer(text, reply_markup=keyboard, parse_mode="MarkdownV2")
    else:
        await callback_or_message.message.edit_text(text, reply_markup=keyboard, parse_mode="MarkdownV2")
    
    await state.set_state(PrayerCalculationStates.female_births_question)

@router.callback_query(PrayerCalculationStates.female_births_question, F.data == "female_births_yes")
async def female_has_births(callback: CallbackQuery, state: FSMContext):
    """У женщины были роды"""
    await callback.message.edit_text(
        "👶 Сколько раз у тебя были роды?",
        reply_markup=get_births_count_keyboard()
    )
    await state.set_state(PrayerCalculationStates.female_births_count_input)

@router.callback_query(PrayerCalculationStates.female_births_question, F.data == "female_births_no")
async def female_no_births(callback: CallbackQuery, state: FSMContext):
    """У женщины не было родов"""
    await state.update_data(births_data=[])
    await ask_about_miscarriages(callback, state)

@router.callback_query(PrayerCalculationStates.female_births_count_input, F.data.startswith("births_count_"))
async def process_female_births_count(callback: CallbackQuery, state: FSMContext):
    """Обработка количества родов"""
    if callback.data == "births_count_manual":
        await callback.message.edit_text(
            "👶 Введи количество родов числом:\n\n"
            "Например: 8"
        )
        return
    
    births_count = int(callback.data.split("_")[2])
    await state.update_data(
        births_count=births_count,
        births_data=[],
        current_birth=1
    )
    
    await ask_birth_date(callback, state, 1)

@router.message(PrayerCalculationStates.female_births_count_input)
async def process_female_births_count_manual(message: Message, state: FSMContext):
    """Обработка ручного ввода количества родов"""
    births_count, error = validate_number_input(message.text, min_val=1, integer_only=True)
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    await state.update_data(
        births_count=int(births_count),
        births_data=[],
        current_birth=1
    )
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
    
    await ask_birth_date(FakeCallback(message), state, 1, is_message=True)

async def ask_birth_date(callback_or_message, state: FSMContext, birth_number: int, is_message=False):
    """Запрос даты родов"""
    text = (f"📅 Введи дату {birth_number}\-х родов в формате ДД\.ММ\.ГГГГ:\n\n"
            f"Например: 20\.03\.2018")
    
    if is_message:
        await callback_or_message.message.answer(text, parse_mode="MarkdownV2")
    else:
        await callback_or_message.message.edit_text(text, parse_mode="MarkdownV2")
    
    await state.set_state(PrayerCalculationStates.female_birth_date_input)

@router.message(PrayerCalculationStates.female_birth_date_input)
async def process_female_birth_date(message: Message, state: FSMContext):
    """Обработка даты родов"""
    data = await state.get_data()
    maturity_date = data['maturity_date']
    
    birth_date, error = validate_date_input(message.text, min_date=maturity_date, max_date=date.today())
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    await state.update_data(current_birth_date=birth_date)
    
    current_birth = data['current_birth']
    nifas_text = escape_markdown(f"""
🌙 Продолжительность нифаса после {current_birth}-х родов.

Напоминаем, что максимальная продолжительность нифаса 40 дней (960ч). 
Советуем тебе самостоятельно изучить эту тему для более корректного определения количества дней нифаса.""", "()-?.!_=")
    
    await message.answer(
        nifas_text,
        reply_markup=get_nifas_duration_keyboard(),
        parse_mode="MarkdownV2"
    )
    await state.set_state(PrayerCalculationStates.female_birth_nifas_input)

@router.callback_query(PrayerCalculationStates.female_birth_nifas_input, F.data.startswith("nifas_days_"))
async def process_female_birth_nifas(callback: CallbackQuery, state: FSMContext):
    """Обработка продолжительности нифаса после родов"""
    if callback.data == "nifas_days_manual":
        await callback.message.edit_text(
            "🌙 Введи продолжительность нифаса в днях \(от 0 до 40\):\n\n"
            "Например: 30",
            parse_mode="MarkdownV2"
        )
        return
    
    nifas_days = int(callback.data.split("_")[2])
    await process_birth_nifas_data(callback, state, nifas_days)

@router.message(PrayerCalculationStates.female_birth_nifas_input)
async def process_female_birth_nifas_manual(message: Message, state: FSMContext):
    """Обработка ручного ввода нифаса"""
    nifas_days, error = validate_number_input(message.text, min_val=0, max_val=40, integer_only=True)
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
    
    await process_birth_nifas_data(FakeCallback(message), state, int(nifas_days), is_message=True)

async def process_birth_nifas_data(callback_or_message, state: FSMContext, nifas_days: int, is_message=False):
    """Обработка данных о нифасе и переход к следующему шагу"""
    data = await state.get_data()
    current_birth = data['current_birth']
    
    birth_data = {
        'date': data['current_birth_date'],
        'nifas_days': nifas_days
    }
    
    # Если цикл нерегулярный, спрашиваем про хайд после родов
    logger.error(data)
    if not data.get('regular_cycle', False) and not data.get('tracks_hayd', False):
        text = f"📊 Введи среднюю продолжительность хайда после {current_birth}\-х родов:"
        keyboard = get_hayd_duration_keyboard()
        
        if is_message:
            await callback_or_message.message.answer(text, reply_markup=keyboard, parse_mode="MarkdownV2")
        else:
            await callback_or_message.message.edit_text(text, reply_markup=keyboard, parse_mode="MarkdownV2")
        
        await state.update_data(current_birth_data=birth_data)
        await state.set_state(PrayerCalculationStates.female_birth_hayd_after_input)
    else:
        # Для регулярного цикла используем общую продолжительность хайда
        birth_data['hayd_after'] = data.get('hayd_average_days', 5)
        await complete_birth_processing(callback_or_message, state, birth_data, is_message)

@router.callback_query(PrayerCalculationStates.female_birth_hayd_after_input, F.data.startswith("hayd_days_"))
async def process_female_birth_hayd_after(callback: CallbackQuery, state: FSMContext):
    """Обработка хайда после родов"""
    if callback.data == "hayd_days_manual":
        await callback.message.edit_text(
            "📊 Введи продолжительность хайда в днях \(от 3 до 10\):\n\n"
            "Например: 6",
            parse_mode="MarkdownV2"
        )
        return
    
    hayd_days = int(callback.data.split("_")[2])
    data = await state.get_data()
    birth_data = data['current_birth_data']
    birth_data['hayd_after'] = hayd_days
    
    await complete_birth_processing(callback, state, birth_data)

@router.message(PrayerCalculationStates.female_birth_hayd_after_input)
async def process_female_birth_hayd_after_manual(message: Message, state: FSMContext):
    """Обработка ручного ввода хайда после родов"""
    hayd_days, error = validate_number_input(message.text, min_val=3, max_val=10)
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    data = await state.get_data()
    birth_data = data['current_birth_data']
    birth_data['hayd_after'] = hayd_days
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
    
    await complete_birth_processing(FakeCallback(message), state, birth_data, is_message=True)

async def complete_birth_processing(callback_or_message, state: FSMContext, birth_data: dict, is_message=False):
    """Завершение обработки текущих родов"""
    data = await state.get_data()
    births_data = data.get('births_data', [])
    births_data.append(birth_data)
    
    current_birth = data['current_birth']
    total_births = data['births_count']
    
    # Проверяем, есть ли еще роды для обработки
    if current_birth < total_births:
        next_birth = current_birth + 1
        await state.update_data(
            births_data=births_data,
            current_birth=next_birth
        )
        await ask_birth_date(callback_or_message, state, next_birth, is_message)
    else:
        # Все роды обработаны, переходим к выкидышам
        await state.update_data(births_data=births_data)
        await ask_about_miscarriages(callback_or_message, state, is_message)

async def ask_about_miscarriages(callback_or_message, state: FSMContext, is_message=False):
    """Вопрос о выкидышах"""
    miscarriage_info = escape_markdown("""
🤱 **Выкидыши**

По ханафитскому мазхабу, если выкидыш произошел после формирования эмбриона (примерно после 120 дней беременности), то после него наступает нифас.

Максимальная продолжительность нифаса после выкидыша также составляет 40 дней.

Если выкидыш был на раннем сроке (до формирования эмбриона), то это считается обычным кровотечением (истихада), во время которого нужно читать намаз.

Были ли у тебя выкидыши сформировавшегося эмбриона?""", "()-?.!_=")
    
    keyboard = get_yes_no_keyboard("female_miscarriages_yes", "female_miscarriages_no")
    
    if is_message:
        await callback_or_message.message.answer(miscarriage_info, reply_markup=keyboard, parse_mode="MarkdownV2")
    else:
        await callback_or_message.message.edit_text(miscarriage_info, reply_markup=keyboard, parse_mode="MarkdownV2")
    
    await state.set_state(PrayerCalculationStates.female_miscarriages_question)

@router.callback_query(PrayerCalculationStates.female_miscarriages_question, F.data == "female_miscarriages_yes")
async def female_has_miscarriages(callback: CallbackQuery, state: FSMContext):
    """У женщины были выкидыши"""
    await callback.message.edit_text(
        "🤱 Сколько у тебя было выкидышей сформировавшегося эмбриона?",
        reply_markup=get_miscarriages_count_keyboard()
    )
    await state.set_state(PrayerCalculationStates.female_miscarriages_count_input)

@router.callback_query(PrayerCalculationStates.female_miscarriages_question, F.data == "female_miscarriages_no")
async def female_no_miscarriages(callback: CallbackQuery, state: FSMContext):
    """У женщины не было выкидышей"""
    await state.update_data(miscarriages_data=[])
    await ask_about_menopause(callback, state)

@router.callback_query(PrayerCalculationStates.female_miscarriages_count_input, F.data.startswith("miscarriages_count_"))
async def process_female_miscarriages_count(callback: CallbackQuery, state: FSMContext):
    """Обработка количества выкидышей"""
    if callback.data == "miscarriages_count_manual":
        await callback.message.edit_text(
            "🤱 Введи количество выкидышей числом:\n\n"
            "Например: 2"
        )
        return
    
    miscarriages_count = int(callback.data.split("_")[2])
    await state.update_data(
        miscarriages_count=miscarriages_count,
        miscarriages_data=[],
        current_miscarriage=1
    )
    
    await ask_miscarriage_date(callback, state, 1)

@router.message(PrayerCalculationStates.female_miscarriages_count_input)
async def process_female_miscarriages_count_manual(message: Message, state: FSMContext):
    """Обработка ручного ввода количества выкидышей"""
    miscarriages_count, error = validate_number_input(message.text, min_val=1, integer_only=True)
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    await state.update_data(
        miscarriages_count=int(miscarriages_count),
        miscarriages_data=[],
        current_miscarriage=1
    )
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
    
    await ask_miscarriage_date(FakeCallback(message), state, 1, is_message=True)

async def ask_miscarriage_date(callback_or_message, state: FSMContext, miscarriage_number: int, is_message=False):
    """Запрос даты выкидыша"""
    text = (f"📅 Введи дату {miscarriage_number}\-го выкидыша в формате ДД\.ММ\.ГГГГ:\n\n"
            f"Например: 15\.07\.2019")
    
    if is_message:
        await callback_or_message.message.answer(text, parse_mode="MarkdownV2")
    else:
        await callback_or_message.message.edit_text(text, parse_mode="MarkdownV2")
    
    await state.set_state(PrayerCalculationStates.female_miscarriage_date_input)

@router.message(PrayerCalculationStates.female_miscarriage_date_input)
async def process_female_miscarriage_date(message: Message, state: FSMContext):
    """Обработка даты выкидыша"""
    data = await state.get_data()
    maturity_date = data['maturity_date']
    
    miscarriage_date, error = validate_date_input(message.text, min_date=maturity_date, max_date=date.today())
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    await state.update_data(current_miscarriage_date=miscarriage_date)
    
    current_miscarriage = data['current_miscarriage']
    nifas_text = escape_markdown(f"""
🌙 Продолжительность нифаса после {current_miscarriage}-го выкидыша.

Напоминаем, что максимальная продолжительность нифаса 40 дней (960ч).
Если выкидыш был на раннем сроке (до 120 дней), то введи 0 дней.""", "()-?.!_=")
    
    await message.answer(
        nifas_text,
        reply_markup=get_nifas_duration_keyboard(),
        parse_mode="MarkdownV2"
    )
    await state.set_state(PrayerCalculationStates.female_miscarriage_nifas_input)

@router.callback_query(PrayerCalculationStates.female_miscarriage_nifas_input, F.data.startswith("nifas_days_"))
async def process_female_miscarriage_nifas(callback: CallbackQuery, state: FSMContext):
    """Обработка продолжительности нифаса после выкидыша"""
    if callback.data == "nifas_days_manual":
        await callback.message.edit_text(
            "🌙 Введи продолжительность нифаса в днях \(от 0 до 40\):\n\n"
            "Например: 15",
            parse_mode="MarkdownV2"
        )
        return
    
    nifas_days = int(callback.data.split("_")[2])
    await process_miscarriage_nifas_data(callback, state, nifas_days)

@router.message(PrayerCalculationStates.female_miscarriage_nifas_input)
async def process_female_miscarriage_nifas_manual(message: Message, state: FSMContext):
    """Обработка ручного ввода нифаса после выкидыша"""
    nifas_days, error = validate_number_input(message.text, min_val=0, max_val=40, integer_only=True)
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
    
    await process_miscarriage_nifas_data(FakeCallback(message), state, int(nifas_days), is_message=True)

async def process_miscarriage_nifas_data(callback_or_message, state: FSMContext, nifas_days: int, is_message=False):
    """Обработка данных о нифасе после выкидыша"""
    data = await state.get_data()
    current_miscarriage = data['current_miscarriage']
    
    miscarriage_data = {
        'date': data['current_miscarriage_date'],
        'nifas_days': nifas_days
    }
    
    # Если цикл нерегулярный, спрашиваем про хайд после выкидыша
    if not data.get('regular_cycle', False) and not data.get('tracks_hayd', False):
        text = f"📊 Введи среднюю продолжительность хайда после {current_miscarriage}\-го выкидыша:"
        keyboard = get_hayd_duration_keyboard()
        
        if is_message:
            await callback_or_message.message.answer(text, reply_markup=keyboard, parse_mode="MarkdownV2")
        else:
            await callback_or_message.message.edit_text(text, reply_markup=keyboard, parse_mode="MarkdownV2")
        
        await state.update_data(current_miscarriage_data=miscarriage_data)
        await state.set_state(PrayerCalculationStates.female_miscarriage_hayd_after_input)
    else:
        # Для регулярного цикла используем общую продолжительность хайда
        miscarriage_data['hayd_after'] = data.get('hayd_average_days', 5)
        await complete_miscarriage_processing(callback_or_message, state, miscarriage_data, is_message)

@router.callback_query(PrayerCalculationStates.female_miscarriage_hayd_after_input, F.data.startswith("hayd_days_"))
async def process_female_miscarriage_hayd_after(callback: CallbackQuery, state: FSMContext):
    """Обработка хайда после выкидыша"""
    if callback.data == "hayd_days_manual":
        await callback.message.edit_text(
            "📊 Введи продолжительность хайда в днях \(от 3 до 10\):\n\n"
            "Например: 5",
            parse_mode="MarkdownV2"
        )
        return
    
    hayd_days = int(callback.data.split("_")[2])
    data = await state.get_data()
    miscarriage_data = data['current_miscarriage_data']
    miscarriage_data['hayd_after'] = hayd_days
    
    await complete_miscarriage_processing(callback, state, miscarriage_data)

@router.message(PrayerCalculationStates.female_miscarriage_hayd_after_input)
async def process_female_miscarriage_hayd_after_manual(message: Message, state: FSMContext):
    """Обработка ручного ввода хайда после выкидыша"""
    hayd_days, error = validate_number_input(message.text, min_val=3, max_val=10)
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    data = await state.get_data()
    miscarriage_data = data['current_miscarriage_data']
    miscarriage_data['hayd_after'] = hayd_days
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
    
    await complete_miscarriage_processing(FakeCallback(message), state, miscarriage_data, is_message=True)

async def complete_miscarriage_processing(callback_or_message, state: FSMContext, miscarriage_data: dict, is_message=False):
    """Завершение обработки текущего выкидыша"""
    data = await state.get_data()
    miscarriages_data = data.get('miscarriages_data', [])
    miscarriages_data.append(miscarriage_data)
    
    current_miscarriage = data['current_miscarriage']
    total_miscarriages = data['miscarriages_count']
    
    # Проверяем, есть ли еще выкидыши для обработки
    if current_miscarriage < total_miscarriages:
        next_miscarriage = current_miscarriage + 1
        await state.update_data(
            miscarriages_data=miscarriages_data,
            current_miscarriage=next_miscarriage
        )
        await ask_miscarriage_date(callback_or_message, state, next_miscarriage, is_message)
    else:
        # Все выкидыши обработаны, переходим к менопаузе
        await state.update_data(miscarriages_data=miscarriages_data)
        await ask_about_menopause(callback_or_message, state, is_message)

async def ask_about_menopause(callback_or_message, state: FSMContext, is_message=False):
    """Вопрос о менопаузе"""
    menopause_info = escape_markdown("""
🌅 **Менопауза**

Менопауза - это прекращение месячных.

Возраст наступления составляет 55 лунных лет (приблизительно 53 солнечных года и 4 месяца).

После наступления менопаузы женщина обязана читать намаз каждый день, так как у неё больше нет периодов хайда.

Наступила ли у тебя менопауза?""", "()-?.!_=")
    
    keyboard = get_yes_no_keyboard("female_menopause_yes", "female_menopause_no")
    
    if is_message:
        await callback_or_message.message.answer(menopause_info, reply_markup=keyboard, parse_mode="MarkdownV2")
    else:
        await callback_or_message.message.edit_text(menopause_info, reply_markup=keyboard, parse_mode="MarkdownV2")
    
    await state.set_state(PrayerCalculationStates.female_menopause_question)

@router.callback_query(PrayerCalculationStates.female_menopause_question, F.data == "female_menopause_yes")
async def female_has_menopause(callback: CallbackQuery, state: FSMContext):
    """У женщины была менопауза"""
    await callback.message.edit_text(
        "📅 Введи дату начала менопаузы в формате ДД\.ММ\.ГГГГ:\n\n"
        "Например: 10\.01\.2020",
        parse_mode="MarkdownV2"
    )
    await state.set_state(PrayerCalculationStates.female_menopause_date_input)

@router.callback_query(PrayerCalculationStates.female_menopause_question, F.data == "female_menopause_no")
async def female_no_menopause(callback: CallbackQuery, state: FSMContext):
    """У женщины не было менопаузы"""
    await state.update_data(menopause_date=None)
    await ask_prayer_start_date_female(callback, state)

@router.message(PrayerCalculationStates.female_menopause_date_input)
async def process_female_menopause_date(message: Message, state: FSMContext):
    """Обработка даты менопаузы"""
    data = await state.get_data()
    maturity_date = data['maturity_date']
    
    menopause_date, error = validate_date_input(message.text, min_date=maturity_date, max_date=date.today())
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    await state.update_data(menopause_date=menopause_date)
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
    
    await ask_prayer_start_date_female(FakeCallback(message), state, is_message=True)

async def ask_prayer_start_date_female(callback_or_message, state: FSMContext, is_message=False):
    """Запрос даты начала совершения намазов для женщины"""
    text = ("📅 Введи дату начала совершения 6\-кратных намазов в формате ДД\.ММ\.ГГГГ:\n\n"
            "Например: 01\.03\.2021")
    
    if is_message:
        await callback_or_message.message.answer(text, parse_mode="MarkdownV2")
    else:
        await callback_or_message.message.edit_text(text, parse_mode="MarkdownV2")
    
    await state.set_state(PrayerCalculationStates.female_prayer_start_date_input)

@router.message(PrayerCalculationStates.female_prayer_start_date_input)
async def process_female_prayer_start_date(message: Message, state: FSMContext):
    """Обработка даты начала намазов для женщины"""
    data = await state.get_data()
    maturity_date = data['maturity_date']
    
    prayer_start_date, error = validate_date_input(message.text, min_date=maturity_date, max_date=date.today())
    if error:
        await message.answer(error, parse_mode="MarkdownV2")
        return
    
    # Проводим финальный расчет
    await perform_female_calculation(message, state, prayer_start_date)

async def perform_female_calculation(message: Message, state: FSMContext, prayer_start_date: date):
    """Финальный расчет намазов для женщины"""
    data = await state.get_data()
    
    # Собираем все данные для расчета
    maturity_date = data['maturity_date']
    regular_cycle = data.get('regular_cycle', False)
    menopause_date = data.get('menopause_date')
    births_data = data.get('births_data', [])
    miscarriages_data = data.get('miscarriages_data', [])
    
    # Подготавливаем данные о хайде
    hayd_data = {}
    if data.get('total_hayd_days'):
        # Если указано общее количество дней хайда
        hayd_data['total_hayd_days'] = data['total_hayd_days']
        hayd_data['use_total'] = True
    else:
        # Используем среднюю продолжительность
        hayd_data['average_hayd'] = data.get('hayd_average_days', 5)
        hayd_data['use_total'] = False
    
    # Выполняем расчет
    try:
        prayers_data = calculation_service.calculate_female_prayers_complex(
            maturity_date=maturity_date,
            prayer_start_date=prayer_start_date,
            regular_cycle=regular_cycle,
            hayd_data=hayd_data,
            births_data=births_data,
            miscarriages_data=miscarriages_data,
            menopause_date=menopause_date
        )
        
        # Сохраняем результат
        await prayer_service.set_user_prayers(message.from_user.id, prayers_data)
        
        # Подготавливаем детали расчета
        calculation_details = {
            'start_date': format_date(maturity_date),
            'end_date': format_date(prayer_start_date),
            'menopause_date': format_date(menopause_date) if menopause_date else None,
            'births_count': len(births_data),
            'miscarriages_count': len(miscarriages_data),
            'regular_cycle': regular_cycle
        }
        
        # Показываем результат
        result_text = calculation_service.format_calculation_summary(prayers_data, calculation_details)
        
        await message.answer(
            escape_markdown(result_text, "()-?.!_="),
            reply_markup=get_main_menu_keyboard(),
            parse_mode="MarkdownV2"
        )
        
        logger.info(f"Женский расчет завершен для пользователя {message.from_user.id}: {prayers_data}")
        
    except Exception as e:
        logger.error(f"Ошибка при расчете намазов для женщины {message.from_user.id}: {e}")
        await message.answer(
            "❌ Произошла ошибка при расчете\. Попробуй еще раз или обратись к администратору\.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="MarkdownV2"
        )
    
    await state.clear()

# ======================================
# СЛУЖЕБНЫЕ ФУНКЦИИ
# ======================================

def validate_date_input(date_text: str, min_date: date = None, max_date: date = None) -> tuple[date, str]:
    """Валидация ввода даты"""
    parsed_date = parse_date(date_text)
    if not parsed_date:
        return None, "❌ Неверный формат даты\. Используй формат ДД\.ММ\.ГГГГ"
    
    if min_date and parsed_date < min_date:
        return None, f"❌ Дата не может быть раньше {format_date(min_date)}\."
    
    if max_date and parsed_date > max_date:
        return None, f"❌ Дата не может быть позже {format_date(max_date)}\."
    
    return parsed_date, ""

def validate_number_input(text: str, min_val: float = None, max_val: float = None, integer_only: bool = False) -> tuple[float, str]:
    """Валидация числового ввода"""
    try:
        if integer_only:
            value = int(text)
        else:
            value = float(text)
    except ValueError:
        return None, "❌ Введи корректное число\."
    
    if min_val is not None and value < min_val:
        return None, f"❌ Значение должно быть не менее {min_val}\."
    
    if max_val is not None and value > max_val:
        return None, f"❌ Значение должно быть не более {max_val}\."
    
    return value, ""

# Обработчик отмены для всех состояний
@router.message(Command("cancel"))
async def cancel_prayer_calculation(message: Message, state: FSMContext):
    """Отмена расчета намазов"""
    current_state = await state.get_state()
    if current_state and current_state.startswith("PrayerCalculationStates"):
        await state.clear()
        await message.answer(
            "❌ Расчет намазов отменен\.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="MarkdownV2"
        )