from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, date, timedelta
import json
import logging

from ...keyboards.user.registration import (
    get_gender_selection_keyboard, get_childbirth_count_keyboard,
    get_hayd_duration_presets_keyboard, get_nifas_duration_presets_keyboard,
    get_use_default_hayd_keyboard, get_data_confirmation_keyboard
)
from ...keyboards.user.main_menu import get_main_menu_keyboard, get_moderator_menu_keyboard, get_admin_menu_keyboard
from ....core.services.user_service import UserService
from ....core.config import config, escape_markdown
from ...states.registration import RegistrationStates
from ...utils.text_messages import text_message

logger = logging.getLogger(__name__)
router = Router()
user_service = UserService()

# ================================
# UTILITY FUNCTIONS
# ================================

def calculate_lunar_adult_date(birth_date: date, lunar_years: int) -> date:
    """Расчет даты совершеннолетия по лунному календарю"""
    LUNAR_YEAR_DAYS = 354.37
    total_lunar_days = int(lunar_years * LUNAR_YEAR_DAYS)
    return birth_date + timedelta(days=total_lunar_days)

def get_lunar_age(birth_date: date, current_date: date = None) -> tuple[int, int]:
    """Возвращает возраст в лунных годах и днях"""
    if current_date is None:
        current_date = date.today()
    days_lived = (current_date - birth_date).days
    return days_lived // 354, days_lived % 354

def format_confirmation_text(data: dict) -> str:
    """Форматирует текст подтверждения регистрации"""
    gender_text = 'Мужской' if data['gender'] == 'male' else 'Женский'
    birth_date_text = data['birth_date'].strftime('%d.%m.%Y')
    
    text = (
        f"👤 Пол: {escape_markdown(gender_text)}\n"
        f"📅 Дата рождения: {escape_markdown(birth_date_text)}\n"
        f"🏙️ Город: {escape_markdown(data['city'])}\n"
    )
    
    if False and data['gender'] == 'female':
        hayd_days = data.get('hayd_average_days', 0)
        birth_count = data.get('childbirth_count', 0)
        text += f"\n🌙 Средний хайд: {hayd_days} дней\n"
        text += f"👶 Количество родов: {birth_count}\n"
        
        if data.get('childbirth_data'):
            text += "\n*Информация о родах:*\n"
            for birth in data['childbirth_data']:
                text += (f"• {birth['number']}\-е роды: {birth['date']}, "
                        f"нифас {birth['nifas_days']} дней\n")
    
    text += "\n❓ Все данные корректны?"
    return text

async def save_user_registration(callback: CallbackQuery, data: dict) -> bool:
    """Сохраняет данные пользователя в базу"""
    adult_age = config.ADULT_AGE_FEMALE if data['gender'] == 'female' else config.ADULT_AGE_MALE
    adult_date = calculate_lunar_adult_date(data['birth_date'], adult_age)
    
    childbirth_data_json = None
    if data.get('childbirth_data'):
        childbirth_data_json = json.dumps(data['childbirth_data'])
    
    return await user_service.complete_registration(
        telegram_id=callback.from_user.id,
        gender=data['gender'],
        birth_date=data['birth_date'],
        city=data['city'],
        adult_date=adult_date,
        hayd_average_days=data.get('hayd_average_days'),
        childbirth_count=data.get('childbirth_count', 0),
        childbirth_data=childbirth_data_json
    )

# ================================
# MAIN REGISTRATION HANDLERS
# ================================

@router.callback_query(RegistrationStates.gender_selection, F.data.startswith("gender:"))
async def handle_gender_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора пола"""
    gender = callback.data.split(":")[1]  # "gender:male" -> "male"
    await state.update_data(gender=gender)
    
    await callback.message.edit_text(
        "📅 Введите дату рождения в формате ДД.ММ.ГГГГ\n\n"
        "📝 Например: 15.03.1990"
    )
    await state.set_state(RegistrationStates.birth_date_input)

@router.message(RegistrationStates.birth_date_input)
async def handle_birth_date_input(message: Message, state: FSMContext):
    """Обработка ввода даты рождения"""
    try:
        birth_date = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
        
        # Валидация лунного возраста
        lunar_years, _ = get_lunar_age(birth_date)
        if lunar_years < 8 or lunar_years > 100:
            solar_age = date.today().year - birth_date.year
            await message.answer(
                f"❌ Некорректная дата рождения\n\n"
                f"Ваш возраст: ~{solar_age} солнечных лет ({lunar_years} лунных лет)\n"
                f"Допустимый диапазон: 8-100 лунных лет"
            )
            return
        
        await state.update_data(birth_date=birth_date)
        
        await message.answer(
            "🏙️ Укажите город проживания\n\n"
            "📝 Например: Москва, Казань, Баку"
        )
        await state.set_state(RegistrationStates.city_input)
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты\n\n"
            "📅 Используйте формат: ДД.ММ.ГГГГ\n"
            "📝 Например: 15.03.1990"
        )

@router.message(RegistrationStates.city_input)
async def handle_city_input(message: Message, state: FSMContext):
    """Обработка ввода города"""
    city = message.text.strip()
    await state.update_data(city=city)
    
    data = await state.get_data()
    
    if False and data['gender'] == 'female':
        await message.answer(
            "🌙 Укажите среднюю продолжительность хайда (от 3 до 10 дней)",
            reply_markup=get_hayd_duration_presets_keyboard()
        )
        await state.set_state(RegistrationStates.hayd_duration_input)
    else:
        await show_confirmation(message, state)

# ================================
# FEMALE-SPECIFIC HANDLERS
# ================================

@router.callback_query(RegistrationStates.hayd_duration_input, F.data.startswith("hayd:"))
async def handle_hayd_duration_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора продолжительности хайда"""
    hayd_data = callback.data.split(":")[1]
    
    if hayd_data == "manual":
        await callback.message.edit_text(
            "🌙 Введите продолжительность хайда в днях\n\n"
            f"📏 Допустимый диапазон: {config.HAYD_MIN_DAYS}-{config.HAYD_MAX_DAYS} дней\n"
            "📝 Например: 5"
        )
        return
    
    hayd_days = float(hayd_data)
    await state.update_data(hayd_average_days=hayd_days)
    
    await callback.message.edit_text(
        "👶 Сколько у вас было родов?",
        reply_markup=get_childbirth_count_keyboard()
    )
    await state.set_state(RegistrationStates.childbirth_count_input)

@router.message(RegistrationStates.hayd_duration_input)
async def handle_hayd_duration_manual_input(message: Message, state: FSMContext):
    """Обработка ручного ввода продолжительности хайда"""
    try:
        hayd_days = float(message.text.strip())
        if not (config.HAYD_MIN_DAYS <= hayd_days <= config.HAYD_MAX_DAYS):
            await message.answer(
                f"❌ Значение должно быть от {config.HAYD_MIN_DAYS} до {config.HAYD_MAX_DAYS} дней"
            )
            return
        
        await state.update_data(hayd_average_days=hayd_days)
        
        await message.answer(
            "👶 Сколько у вас было родов?",
            reply_markup=get_childbirth_count_keyboard()
        )
        await state.set_state(RegistrationStates.childbirth_count_input)
        
    except ValueError:
        await message.answer("❌ Введите корректное число")

@router.callback_query(RegistrationStates.childbirth_count_input, F.data.startswith("births:"))
async def handle_childbirth_count_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора количества родов"""
    births_data = callback.data.split(":")[1]
    
    if births_data == "manual":
        await callback.message.edit_text(
            "👶 Введите количество родов числом\n\n"
            "📝 Например: 7"
        )
        return
    
    count = int(births_data)
    await state.update_data(
        childbirth_count=count,
        childbirth_data=[],
        current_birth=1
    )
    
    if count > 0:
        await start_childbirth_data_collection(callback, state)
    else:
        await show_confirmation_inline(callback, state)

@router.message(RegistrationStates.childbirth_count_input)
async def handle_childbirth_count_manual_input(message: Message, state: FSMContext):
    """Обработка ручного ввода количества родов"""
    try:
        count = int(message.text.strip())
        if count < 0:
            await message.answer("❌ Количество не может быть отрицательным")
            return
        
        await state.update_data(
            childbirth_count=count,
            childbirth_data=[],
            current_birth=1
        )
        
        if count > 0:
            data = await state.get_data()
            await message.answer(
                f"📊 Продолжительность хайда ДО 1-х родов\n\n"
                f"💡 По умолчанию: {data['hayd_average_days']} дней",
                reply_markup=get_use_default_hayd_keyboard(data['hayd_average_days'])
            )
            await state.set_state(RegistrationStates.pre_birth_hayd_input)
        else:
            await show_confirmation(message, state)
            
    except ValueError:
        await message.answer("❌ Введите корректное число")

async def start_childbirth_data_collection(callback: CallbackQuery, state: FSMContext):
    """Начинает сбор данных о родах"""
    data = await state.get_data()
    await callback.message.edit_text(
        f"📊 Продолжительность хайда ДО 1-х родов\n\n"
        f"💡 По умолчанию: {data['hayd_average_days']} дней",
        reply_markup=get_use_default_hayd_keyboard(data['hayd_average_days'])
    )
    await state.set_state(RegistrationStates.pre_birth_hayd_input)

# ================================
# CHILDBIRTH DATA COLLECTION
# ================================

@router.callback_query(RegistrationStates.pre_birth_hayd_input, F.data.startswith("hayd:"))
async def handle_pre_birth_hayd_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора хайда до родов"""
    hayd_data = callback.data.split(":")[1]
    
    if hayd_data == "manual":
        await callback.message.edit_text(
            "📊 Введите продолжительность хайда до родов в днях\n\n"
            f"📏 Диапазон: {config.HAYD_MIN_DAYS}-{config.HAYD_MAX_DAYS} дней"
        )
        return
    
    hayd_before = float(hayd_data)
    await state.update_data(current_hayd_before=hayd_before)
    
    data = await state.get_data()
    current_birth = data['current_birth']
    
    await callback.message.edit_text(
        f"📅 Введите дату {current_birth}-х родов\n\n"
        f"📝 Формат: ДД.ММ.ГГГГ\n"
        f"📝 Например: 15.03.2020"
    )
    await state.set_state(RegistrationStates.childbirth_date_input)

@router.message(RegistrationStates.pre_birth_hayd_input)
async def handle_pre_birth_hayd_manual_input(message: Message, state: FSMContext):
    """Обработка ручного ввода хайда до родов"""
    try:
        hayd_before = float(message.text.strip())
        if not (config.HAYD_MIN_DAYS <= hayd_before <= config.HAYD_MAX_DAYS):
            await message.answer(
                f"❌ Значение должно быть от {config.HAYD_MIN_DAYS} до {config.HAYD_MAX_DAYS} дней"
            )
            return
        
        await state.update_data(current_hayd_before=hayd_before)
        
        data = await state.get_data()
        current_birth = data['current_birth']
        
        await message.answer(
            f"📅 Введите дату {current_birth}-х родов\n\n"
            f"📝 Формат: ДД.ММ.ГГГГ\n"
            f"📝 Например: 15.03.2020"
        )
        await state.set_state(RegistrationStates.childbirth_date_input)
        
    except ValueError:
        await message.answer("❌ Введите корректное число")

@router.message(RegistrationStates.childbirth_date_input)
async def handle_childbirth_date_input(message: Message, state: FSMContext):
    """Обработка ввода даты родов"""
    try:
        birth_date = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
        data = await state.get_data()
        
        # Валидация даты
        if birth_date > date.today():
            await message.answer("❌ Дата не может быть в будущем")
            return
        
        if birth_date < data['birth_date']:
            await message.answer("❌ Дата родов не может быть раньше вашего рождения")
            return
        
        await state.update_data(current_birth_date=birth_date)
        
        current_birth = data['current_birth']
        await message.answer(
            f"🌙 Продолжительность нифаса после {current_birth}-х родов",
            reply_markup=get_nifas_duration_presets_keyboard()
        )
        await state.set_state(RegistrationStates.nifas_duration_input)
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты\n\n"
            "📅 Используйте: ДД.ММ.ГГГГ\n"
            "📝 Например: 15.03.2020"
        )

@router.callback_query(RegistrationStates.nifas_duration_input, F.data.startswith("nifas:"))
async def handle_nifas_duration_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора продолжительности нифаса"""
    nifas_data = callback.data.split(":")[1]
    
    if nifas_data == "manual":
        await callback.message.edit_text(
            f"🌙 Введите продолжительность нифаса в днях\n\n"
            f"📏 Максимум: {config.NIFAS_MAX_DAYS} дней\n"
            f"📝 Например: 30"
        )
        return
    
    await process_nifas_duration(callback, int(nifas_data), state)

@router.message(RegistrationStates.nifas_duration_input)
async def handle_nifas_duration_manual_input(message: Message, state: FSMContext):
    """Обработка ручного ввода продолжительности нифаса"""
    try:
        nifas_days = int(message.text.strip())
        if not (0 <= nifas_days <= config.NIFAS_MAX_DAYS):
            await message.answer(
                f"❌ Значение должно быть от 0 до {config.NIFAS_MAX_DAYS} дней"
            )
            return
        
        # Создаем фиктивный callback для совместимости с process_nifas_duration
        class FakeCallback:
            def __init__(self, message):
                self.message = message
        
        await process_nifas_duration(FakeCallback(message), nifas_days, state, is_message=True)
        
    except ValueError:
        await message.answer("❌ Введите корректное число")

async def process_nifas_duration(callback_or_message, nifas_days: int, state: FSMContext, is_message=False):
    """Обрабатывает продолжительность нифаса и переходит к следующему этапу"""
    data = await state.get_data()
    childbirth_data = data['childbirth_data']
    current_birth = data['current_birth']
    
    # Сохраняем информацию о текущих родах
    birth_info = {
        'number': current_birth,
        'date': data['current_birth_date'].isoformat(),
        'nifas_days': nifas_days,
        'hayd_before': data['current_hayd_before']
    }
    childbirth_data.append(birth_info)
    
    # Проверяем, есть ли еще роды для обработки
    if current_birth < data['childbirth_count']:
        next_birth = current_birth + 1
        await state.update_data(
            childbirth_data=childbirth_data,
            current_birth=next_birth
        )
        
        text = (f"📊 Продолжительность хайда ДО {next_birth}-х родов\n\n"
                f"💡 По умолчанию: {data['hayd_average_days']} дней")
        keyboard = get_use_default_hayd_keyboard(data['hayd_average_days'])
        
        if is_message:
            await callback_or_message.answer(text, reply_markup=keyboard)
        else:
            await callback_or_message.message.edit_text(text, reply_markup=keyboard)
            
        await state.set_state(RegistrationStates.pre_birth_hayd_input)
    else:
        # Все роды обработаны
        await state.update_data(childbirth_data=childbirth_data)
        
        if is_message:
            await show_confirmation(callback_or_message, state)
        else:
            await show_confirmation_inline(callback_or_message, state)

# ================================
# CONFIRMATION HANDLERS
# ================================

async def show_confirmation(message: Message, state: FSMContext):
    """Показ подтверждения через обычное сообщение"""
    data = await state.get_data()
    confirmation_text = format_confirmation_text(data)
    
    await message.answer(
        confirmation_text,
        reply_markup=get_data_confirmation_keyboard(),
        parse_mode="MarkdownV2"
    )
    await state.set_state(RegistrationStates.data_confirmation)

async def show_confirmation_inline(callback: CallbackQuery, state: FSMContext):
    """Показ подтверждения через inline сообщение"""
    data = await state.get_data()
    confirmation_text = format_confirmation_text(data)
    
    await callback.message.edit_text(
        confirmation_text,
        reply_markup=get_data_confirmation_keyboard(),
        parse_mode="MarkdownV2"
    )
    await state.set_state(RegistrationStates.data_confirmation)

@router.callback_query(RegistrationStates.data_confirmation, F.data.startswith("confirm:"))
async def handle_confirmation(callback: CallbackQuery, state: FSMContext):
    """Обработка подтверждения или редактирования данных"""
    action = callback.data.split(":")[1]  # "confirm:yes" -> "yes"
    
    if action == "yes":
        await finalize_registration(callback, state)
    elif action == "edit":
        await restart_registration(callback, state)

async def finalize_registration(callback: CallbackQuery, state: FSMContext):
    """Завершает регистрацию пользователя"""
    data = await state.get_data()
    
    success = await save_user_registration(callback, data)
    
    if success:
        await callback.message.edit_text("✅ Регистрация завершена!")
        
        # Получаем пользователя для определения роли
        user = await user_service.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # Выбираем клавиатуру в зависимости от роли
        role_keyboards = {
            config.Roles.ADMIN: (get_admin_menu_keyboard(), "👑 Панель администратора"),
            config.Roles.MODERATOR: (get_moderator_menu_keyboard(), "👮 Панель модератора"),
        }
        
        keyboard, welcome_text = role_keyboards.get(
            user.role, (get_main_menu_keyboard(), "🏠 Главное меню")
        )
        
        await callback.message.answer(
            f"🕌 Добро пожаловать в Яшел Трекер\!\n\n"
            f"Я — ваш помощник в подсчёте и восполнении пропущенных намазов и постов "
            f"по ханафитскому мазхабу\n\n"
            f"Информация о процессе восполнения поклонений доступна в нашем [канале]"
            f"({text_message.CHANNEL_LINK})\n\n"
            f"Изучи информацию и возвращайся для расчета 😊\n\n"
            f"{welcome_text}",
            reply_markup=keyboard,
            parse_mode='MarkdownV2'
        )
        
        await state.clear()
    else:
        await callback.message.edit_text(
            "❌ Ошибка при сохранении данных\n\n"
            "Попробуйте зарегистрироваться заново"
        )

async def restart_registration(callback: CallbackQuery, state: FSMContext):
    """Перезапускает процесс регистрации"""
    await callback.message.edit_text(
        "👤 Укажите пол:",
        reply_markup=get_gender_selection_keyboard()
    )
    await state.set_state(RegistrationStates.gender_selection)