from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, date

from ...keyboards.user.registration import get_gender_keyboard, get_confirmation_keyboard
from ...keyboards.user.main_menu import get_main_menu_keyboard, get_moderator_menu_keyboard, get_admin_menu_keyboard
from ....core.services.user_service import UserService
from ....core.config import config
from ..states.registration import RegistrationStates

router = Router()
user_service = UserService()

@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка ввода имени"""
    if message.text == "⏭️ Пропустить":
        full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
    else:
        full_name = message.text
    
    await state.update_data(full_name=full_name)
    
    await message.answer(
        "👤 Укажите ваш пол:",
        reply_markup=get_gender_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_gender)

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
    try:
        birth_date = datetime.strptime(message.text, "%d.%m.%Y").date()
        
        # Проверяем разумность даты
        today = date.today()
        age = today.year - birth_date.year
        if age < 8 or age > 100:
            await message.answer("❌ Пожалуйста, введите корректную дату рождения.")
            return
        
        await state.update_data(birth_date=birth_date)
        
        await message.answer(
            "🏙️ В каком городе вы проживаете?\n"
            "Например: Москва, Казань, Баку"
        )
        await state.set_state(RegistrationStates.waiting_for_city)
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ\n"
            "Например: 15.03.1990"
        )

@router.message(RegistrationStates.waiting_for_city)
async def process_city(message: Message, state: FSMContext):
    """Обработка города"""
    city = message.text.strip()
    await state.update_data(city=city)
    
    # Показываем данные для подтверждения
    data = await state.get_data()
    
    confirmation_text = (
        "📋 **Проверьте введенные данные:**\n\n"
        f"👤 Имя: {data['full_name']}\n"
        f"👤 Пол: {'Мужской' if data['gender'] == 'male' else 'Женский'}\n"
        f"📅 Дата рождения: {data['birth_date'].strftime('%d.%m.%Y')}\n"
        f"🏙️ Город: {data['city']}\n\n"
        "Все верно?"
    )
    
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
        full_name=data['full_name'],
        gender=data['gender'],
        birth_date=data['birth_date'],
        city=data['city']
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
            "Теперь вы можете приступить к расчету пропущенных намазов.",
            reply_markup=keyboard
        )
        
        await state.clear()
    else:
        await callback.message.edit_text("❌ Ошибка при сохранении данных. Попробуйте еще раз.")

@router.callback_query(RegistrationStates.confirmation, F.data == "edit_registration")
async def edit_registration(callback: CallbackQuery, state: FSMContext):
    """Редактирование регистрации"""
    await callback.message.edit_text("Как вас зовут?")
    await state.set_state(RegistrationStates.waiting_for_name)