from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, date

from ...keyboards.user.registration import get_gender_keyboard, get_confirmation_keyboard, get_childbirth_keyboard
from ...keyboards.user.main_menu import get_main_menu_keyboard, get_moderator_menu_keyboard, get_admin_menu_keyboard
from ....core.services.user_service import UserService
from ....core.config import config
from ...states.registration import RegistrationStates
from ...utils.date_utils import parse_date

import logging
logger = logging.getLogger(__name__)

router = Router()
user_service = UserService()

@router.message(RegistrationStates.waiting_for_gender)
async def process_gender(message: Message, state: FSMContext):
    """Обработка выбора пола"""
    if message.text == "👨 Мужской":
        gender = "male"
    elif message.text == "👩 Женский":
        gender = "female"
    else:
        await message.answer("Пожалуйста, выберите пол, используя кнопки.")
        return
    
    await state.update_data(gender=gender)
    
    await message.answer(
        "📅 Введите вашу дату рождения в формате ДД.ММ.ГГГГ\n"
        "Например: 15.03.1990",
        reply_markup=None
    )
    await state.set_state(RegistrationStates.waiting_for_birth_date)

@router.message(RegistrationStates.waiting_for_birth_date)
async def process_birth_date(message: Message, state: FSMContext):
    """Обработка даты рождения"""
    birth_date = parse_date(message.text)
    if not birth_date:
        await message.answer(
            "❌ Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ\n"
            "Например: 15.03.1990"
        )
        return
    
    # Проверяем разумность даты
    today = date.today()
    age = today.year - birth_date.year
    if age < 8 or age > 100:
        await message.answer("❌ Пожалуйста, введите корректную дату рождения.")
        return
    
    await state.update_data(birth_date=birth_date)
    
    await message.answer(
        "🏙️ В каком городе вы проживаете?\n"
        "Например: Москва, Казань, Баку\n\n"
        "Или отправьте 'Пропустить', если не хотите указывать город."
    )
    await state.set_state(RegistrationStates.waiting_for_city)

@router.message(RegistrationStates.waiting_for_city)
async def process_city(message: Message, state: FSMContext):
    """Обработка города"""
    city = None if message.text.lower() == "пропустить" else message.text.strip()
    await state.update_data(city=city)
    
    data = await state.get_data()
    
    # Если пользователь женщина, спрашиваем о родах
    if data['gender'] == 'female':
        await message.answer(
            "👶 Были ли у вас роды?",
            reply_markup=get_childbirth_keyboard()
        )
        await state.set_state(RegistrationStates.asking_about_childbirths)
    else:
        # Для мужчин сразу переходим к подтверждению
        await show_confirmation(message, state)

@router.callback_query(RegistrationStates.asking_about_childbirths, F.data == "has_childbirths")
async def has_childbirths(callback: CallbackQuery, state: FSMContext):
    """Пользователь имеет роды"""
    await callback.message.edit_text(
        "👶 Сколько раз вы рожали?\n"
        "Введите число:"
    )
    await state.set_state(RegistrationStates.waiting_for_childbirth_count)

@router.callback_query(RegistrationStates.asking_about_childbirths, F.data == "no_childbirths")
async def no_childbirths(callback: CallbackQuery, state: FSMContext):
    """Пользователь не имеет родов"""
    await state.update_data(
        childbirth_count=0,
        childbirths=[],
        nifas_lengths=[]
    )
    
    await callback.message.edit_text(
        "🩸 Введите среднюю продолжительность хайда (месячных) в днях:\n"
        "Например: 5\n\n"
        "Минимум 3 дня, максимум 10 дней по ханафи."
    )
    await state.set_state(RegistrationStates.waiting_for_average_hyde)

@router.message(RegistrationStates.waiting_for_childbirth_count)
async def process_childbirth_count(message: Message, state: FSMContext):
    """Обработка количества родов"""
    try:
        count = int(message.text)
        if count < 1 or count > 20:
            await message.answer("❌ Введите число от 1 до 20")
            return
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число")
        return
    
    await state.update_data(
        childbirth_count=count,
        childbirths=[],
        hyde_periods=[],
        nifas_lengths=[],
        current_birth_index=0
    )
    
    await message.answer(
        "🩸 Введите среднюю продолжительность хайда (месячных) ДО первых родов в днях:\n"
        "Например: 5\n\n"
        "Минимум 3 дня, максимум 10 дней по ханафи."
    )
    await state.set_state(RegistrationStates.waiting_for_hyde_before_first)

@router.message(RegistrationStates.waiting_for_hyde_before_first)
async def process_hyde_before_first(message: Message, state: FSMContext):
    """Обработка хайда до первых родов"""
    try:
        hyde_days = int(message.text)
        if hyde_days < 3 or hyde_days > 10:
            await message.answer("❌ Продолжительность хайда должна быть от 3 до 10 дней")
            return
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число")
        return
    
    data = await state.get_data()
    hyde_periods = data.get('hyde_periods', [])
    hyde_periods.append(hyde_days)
    
    await state.update_data(hyde_periods=hyde_periods)
    
    await message.answer(
        "🤱 Введите продолжительность 1-го нифаса (послеродового периода) в днях:\n"
        "Например: 30\n\n"
        "Максимум 40 дней по ханафи."
    )
    await state.set_state(RegistrationStates.waiting_for_nifas_length)

@router.message(RegistrationStates.waiting_for_nifas_length)
async def process_nifas_length(message: Message, state: FSMContext):
    """Обработка длительности нифаса"""
    try:
        nifas_days = int(message.text)
        if nifas_days < 0 or nifas_days > 40:
            await message.answer("❌ Продолжительность нифаса должна быть от 0 до 40 дней")
            return
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число")
        return
    
    data = await state.get_data()
    nifas_lengths = data.get('nifas_lengths', [])
    nifas_lengths.append(nifas_days)
    current_birth_index = data.get('current_birth_index', 0)
    childbirth_count = data.get('childbirth_count', 0)
    
    await state.update_data(nifas_lengths=nifas_lengths)
    
    # Проверяем, нужно ли спрашивать о следующих родах
    if current_birth_index + 1 < childbirth_count:
        next_birth = current_birth_index + 2  # +2 потому что считаем с 1
        await state.update_data(current_birth_index=current_birth_index + 1)
        
        await message.answer(
            f"🩸 Введите среднюю продолжительность хайда ПОСЛЕ {current_birth_index + 1}-х родов в днях:\n"
            "Например: 5"
        )
        await state.set_state(RegistrationStates.waiting_for_hyde_after_birth)
    else:
        # Все роды обработаны
        await show_confirmation(message, state)

@router.message(RegistrationStates.waiting_for_hyde_after_birth)
async def process_hyde_after_birth(message: Message, state: FSMContext):
    """Обработка хайда после родов"""
    try:
        hyde_days = int(message.text)
        if hyde_days < 3 or hyde_days > 10:
            await message.answer("❌ Продолжительность хайда должна быть от 3 до 10 дней")
            return
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число")
        return
    
    data = await state.get_data()
    hyde_periods = data.get('hyde_periods', [])
    hyde_periods.append(hyde_days)
    current_birth_index = data.get('current_birth_index', 0)
    childbirth_count = data.get('childbirth_count', 0)
    
    await state.update_data(hyde_periods=hyde_periods)
    
    # Если есть еще роды, спрашиваем о следующем нифасе
    if current_birth_index + 1 < childbirth_count:
        next_birth = current_birth_index + 2
        await message.answer(
            f"🤱 Введите продолжительность {next_birth}-го нифаса в днях:\n"
            "Например: 35"
        )
        await state.set_state(RegistrationStates.waiting_for_nifas_length)
    else:
        # Все роды обработаны
        await show_confirmation(message, state)

@router.message(RegistrationStates.waiting_for_average_hyde)
async def process_average_hyde(message: Message, state: FSMContext):
    """Обработка средней продолжительности хайда"""
    try:
        hyde_days = int(message.text)
        if hyde_days < 3 or hyde_days > 10:
            await message.answer("❌ Продолжительность хайда должна быть от 3 до 10 дней")
            return
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число")
        return
    
    await state.update_data(hyde_periods=[hyde_days])
    await show_confirmation(message, state)

async def show_confirmation(message: Message, state: FSMContext):
    """Показ данных для подтверждения"""
    data = await state.get_data()
    
    confirmation_text = (
        "📋 **Проверьте введенные данные:**\n\n"
        f"👤 Пол: {'Мужской' if data['gender'] == 'male' else 'Женский'}\n"
        f"📅 Дата рождения: {data['birth_date'].strftime('%d.%m.%Y')}\n"
        f"🏙️ Город: {data.get('city', 'Не указан')}\n"
    )
    
    if data['gender'] == 'female':
        if data.get('childbirth_count', 0) > 0:
            confirmation_text += f"\n👶 Количество родов: {data['childbirth_count']}\n"
            confirmation_text += f"🩸 Периоды хайда: {', '.join(map(str, data.get('hyde_periods', [])))}\n"
            confirmation_text += f"🤱 Длительность нифаса: {', '.join(map(str, data.get('nifas_lengths', [])))}\n"
        else:
            confirmation_text += f"\n🩸 Средняя продолжительность хайда: {data.get('hyde_periods', [0])[0]} дней\n"
    
    confirmation_text += "\nВсе верно?"
    
    await message.answer(
        confirmation_text,
        reply_markup=get_confirmation_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(RegistrationStates.confirmation)

@router.callback_query(RegistrationStates.confirmation, F.data == "confirm_registration")
async def confirm_registration(callback: CallbackQuery, state: FSMContext):
    """Подтверждение регистрации"""
    data = await state.get_data()
    
    # Сохраняем данные пользователя
    success = await user_service.complete_registration(
        telegram_id=callback.from_user.id,
        gender=data['gender'],
        birth_date=data['birth_date'],
        city=data.get('city'),
        childbirth_count=data.get('childbirth_count', 0),
        childbirths=data.get('childbirths', []),
        hyde_periods=data.get('hyde_periods', []),
        nifas_lengths=data.get('nifas_lengths', [])
    )
    
    if success:
        await callback.message.edit_text("✅ Регистрация завершена!")
        
        # Получаем пользователя для определения роли
        user = await user_service.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name
        )
        
        # Выбираем клавиатуру в зависимости от роли
        if user.role == config.Roles.ADMIN:
            keyboard = get_admin_menu_keyboard()
            welcome_text = "👑 Панель администратора"
        elif user.role == config.Roles.MODERATOR:
            keyboard = get_moderator_menu_keyboard()
            welcome_text = "👮 Панель модератора"
        else:
            keyboard = get_main_menu_keyboard()
            welcome_text = "🏠 Главное меню"
        
        await callback.message.answer(
            f"🕌 Добро пожаловать в Яшел Трекер!\n\n"
            f"{welcome_text}\n\n"
            "Теперь вы можете приступить к расчету пропущенных намазов и постов.",
            reply_markup=keyboard
        )
        
        await state.clear()
    else:
        await callback.message.edit_text("❌ Ошибка при сохранении данных. Попробуйте еще раз.")

@router.callback_query(RegistrationStates.confirmation, F.data == "edit_registration")
async def edit_registration(callback: CallbackQuery, state: FSMContext):
    """Редактирование регистрации"""
    await callback.message.edit_text(
        "👤 Укажите ваш пол:",
        reply_markup=get_gender_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_gender)