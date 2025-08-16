from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, date
import json

from ...keyboards.user.registration import get_gender_keyboard, get_confirmation_keyboard
from ...keyboards.user.main_menu import get_main_menu_keyboard, get_moderator_menu_keyboard, get_admin_menu_keyboard
from ....core.services.user_service import UserService
from ....core.config import config
from ...states.registration import RegistrationStates

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
    
    data = await state.get_data()
    
    # # Если женщина, спрашиваем про хайд
    # if data.get('gender') == 'female':
    #     await message.answer(
    #         "📊 Для точного расчета намазов и постов нужна дополнительная информация.\n\n"
    #         "🌙 Укажите ТЕКУЩУЮ среднюю продолжительность хайда в днях (от 3 до 10):\n"
    #         "Например: 5\n\n"
    #         "💡 Это ваша текущая продолжительность цикла"
    #     )
    #     await state.set_state(RegistrationStates.waiting_for_hayd_average)
    # else:
    #     # Для мужчин сразу показываем подтверждение
    #     await show_confirmation(message, state)
    
    await show_confirmation(message, state)

@router.message(RegistrationStates.waiting_for_hayd_average)
async def process_hayd_average(message: Message, state: FSMContext):
    """Обработка текущей продолжительности хайда"""
    try:
        hayd_days = float(message.text.strip())
        if hayd_days < config.HAYD_MIN_DAYS or hayd_days > config.HAYD_MAX_DAYS:
            await message.answer(f"❌ Продолжительность должна быть от {config.HAYD_MIN_DAYS} до {config.HAYD_MAX_DAYS} дней.")
            return
        
        await state.update_data(hayd_average_days=hayd_days)
        
        await message.answer(
            "👶 Сколько у вас было родов?\n\n"
            "Введите число (0 - если не было):"
        )
        await state.set_state(RegistrationStates.waiting_for_childbirth_count)
        
    except ValueError:
        await message.answer(f"❌ Введите число от {config.HAYD_MIN_DAYS} до {config.HAYD_MAX_DAYS}.")

@router.message(RegistrationStates.waiting_for_childbirth_count)
async def process_childbirth_count(message: Message, state: FSMContext):
    """Обработка количества родов"""
    try:
        count = int(message.text.strip())
        if count < 0:
            await message.answer("❌ Количество не может быть отрицательным.")
            return
        
        await state.update_data(
            childbirth_count=count, 
            childbirth_data=[], 
            current_birth=1
        )
        
        if count > 0:
            data = await state.get_data()
            await message.answer(
                f"📊 Средняя продолжительность хайда ДО 1-х родов (дней):\n"
                f"По умолчанию: {data['hayd_average_days']} дней\n\n"
                "💡 Это продолжительность цикла до первых родов\n"
                "Введите число или отправьте 0 для использования текущего значения:"
            )
            await state.set_state(RegistrationStates.waiting_for_hayd_before_birth)
        else:
            await show_confirmation(message, state)
            
    except ValueError:
        await message.answer("❌ Введите число.")

@router.message(RegistrationStates.waiting_for_hayd_before_birth)
async def process_hayd_before_birth(message: Message, state: FSMContext):
    """Обработка хайда до родов"""
    try:
        data = await state.get_data()
        hayd_before = float(message.text.strip())
        
        if hayd_before == 0:
            hayd_before = data['hayd_average_days']
        elif hayd_before < config.HAYD_MIN_DAYS or hayd_before > config.HAYD_MAX_DAYS:
            await message.answer(f"❌ Продолжительность должна быть от {config.HAYD_MIN_DAYS} до {config.HAYD_MAX_DAYS} дней.")
            return
        
        await state.update_data(current_hayd_before=hayd_before)
        
        current_birth = data['current_birth']
        await message.answer(
            f"📅 Введите дату {current_birth}-х родов в формате ДД.ММ.ГГГГ:\n"
            "Например: 15.03.2020"
        )
        await state.set_state(RegistrationStates.waiting_for_childbirth_date)
        
    except ValueError:
        await message.answer("❌ Введите число.")

@router.message(RegistrationStates.waiting_for_childbirth_date)
async def process_childbirth_date(message: Message, state: FSMContext):
    """Обработка даты родов"""
    try:
        birth_date = datetime.strptime(message.text, "%d.%m.%Y").date()
        data = await state.get_data()
        
        # Проверяем корректность даты
        if birth_date > date.today():
            await message.answer("❌ Дата не может быть в будущем.")
            return
        
        if data['birth_date'] and birth_date < data['birth_date']:
            await message.answer("❌ Дата родов не может быть раньше даты вашего рождения.")
            return
        
        await state.update_data(current_birth_date=birth_date)
        
        current_birth = data['current_birth']
        await message.answer(
            f"🌙 Продолжительность нифаса после {current_birth}-х родов (дней):\n"
            f"Максимум: {config.NIFAS_MAX_DAYS} дней\n\n"
            "Введите количество дней:"
        )
        await state.set_state(RegistrationStates.waiting_for_nifas_days)
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ\n"
            "Например: 15.03.2020"
        )

@router.message(RegistrationStates.waiting_for_nifas_days)
async def process_nifas_days(message: Message, state: FSMContext):
    """Обработка продолжительности нифаса"""
    try:
        nifas_days = int(message.text.strip())
        if nifas_days < 0 or nifas_days > config.NIFAS_MAX_DAYS:
            await message.answer(f"❌ Продолжительность должна быть от 0 до {config.NIFAS_MAX_DAYS} дней.")
            return
        
        data = await state.get_data()
        childbirth_data = data['childbirth_data']
        current_birth = data['current_birth']
        
        # Сохраняем данные о текущих родах (без hayd_after!)
        birth_info = {
            'number': current_birth,
            'date': data['current_birth_date'].isoformat(),
            'nifas_days': nifas_days,
            'hayd_before': data['current_hayd_before']
        }
        
        childbirth_data.append(birth_info)
        
        # Переходим к следующим родам если есть
        if current_birth < data['childbirth_count']:
            next_birth = current_birth + 1
            await state.update_data(
                childbirth_data=childbirth_data,
                current_birth=next_birth
            )
            
            await message.answer(
                f"📊 Средняя продолжительность хайда ДО {next_birth}-х родов (дней):\n"
                f"По умолчанию: {data['hayd_average_days']} дней\n\n"
                "💡 Это продолжительность цикла между родами\n"
                "Введите число или отправьте 0 для использования текущего значения:"
            )
            await state.set_state(RegistrationStates.waiting_for_hayd_before_birth)
        else:
            # Все роды обработаны
            await state.update_data(childbirth_data=childbirth_data)
            await show_confirmation(message, state)
        
    except ValueError:
        await message.answer("❌ Введите число.")

async def show_confirmation(message: Message, state: FSMContext):
    """Показ данных для подтверждения"""
    data = await state.get_data()
    
    confirmation_text = (
        "📋 **Проверьте введенные данные:**\n\n"
        f"👤 Пол: {'Мужской' if data['gender'] == 'male' else 'Женский'}\n"
        f"📅 Дата рождения: {data['birth_date'].strftime('%d.%m.%Y')}\n"
        f"🏙️ Город: {data['city']}\n"
    )
    
    if False and data['gender'] == 'female':
        confirmation_text += f"\n🌙 Текущий хайд: {data.get('hayd_average_days', 0)} дней\n"
        confirmation_text += f"👶 Количество родов: {data.get('childbirth_count', 0)}\n"
        
        if data.get('childbirth_data'):
            confirmation_text += "\n**Информация о родах:**\n"
            for birth in data['childbirth_data']:
                confirmation_text += f"• {birth['number']}-е роды: {birth['date']}, нифас {birth['nifas_days']} дней, хайд до родов {birth['hayd_before']} дней\n"
    
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
    
    # Вычисляем дату совершеннолетия
    adult_age = config.ADULT_AGE_FEMALE if data['gender'] == 'female' else config.ADULT_AGE_MALE
    adult_date = data['birth_date'].replace(year=data['birth_date'].year + adult_age)
    
    # Подготавливаем данные о родах для JSON (без hayd_after)
    childbirth_data_json = None
    if data.get('childbirth_data'):
        childbirth_data_json = json.dumps(data['childbirth_data'])
    
    # Сохраняем данные пользователя
    success = await user_service.complete_registration(
        telegram_id=callback.from_user.id,
        gender=data['gender'],
        birth_date=data['birth_date'],
        city=data['city'],
        adult_date=adult_date,
        hayd_average_days=data.get('hayd_average_days'),
        childbirth_count=data.get('childbirth_count', 0),
        childbirth_data=childbirth_data_json
    )
    
    if success:
        await callback.message.edit_text("✅ Регистрация завершена!")
        
        # Получаем пользователя для определения роли
        user = await user_service.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
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