from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime
import logging

from ...keyboards.user.female_periods import (
    get_childbirth_keyboard,
    get_continue_keyboard
)
from ....core.database.repositories.female_periods_repository import FemalePeriodsRepository
from ....core.database.repositories.user_repository import UserRepository
from ....core.database.models.hayd import HaydInfo
from ....core.database.models.nifas import NifasInfo
from ....core.config import config
from ...states.female_periods import FemalePeriodsStates
from ...utils.date_utils import parse_date

logger = logging.getLogger(__name__)
router = Router()

periods_repo = FemalePeriodsRepository()
user_repo = UserRepository()

async def start_female_periods_input(message: Message, state: FSMContext):
    """Начало ввода информации о женских периодах"""
    user = await user_repo.get_user_by_telegram_id(message.from_user.id)
    
    if user.gender != 'female':
        # Для мужчин пропускаем этот этап
        return False
    
    await message.answer(
        "👩 **Информация о женских периодах**\n\n"
        "Для точного расчета намазов и постов необходимо учесть периоды, "
        "когда женщинам не нужно совершать намаз.\n\n"
        "📍 Укажите среднюю продолжительность хайда в днях (от 3 до 10):",
        parse_mode="Markdown"
    )
    await state.set_state(FemalePeriodsStates.entering_hayd_duration)
    return True

@router.message(FemalePeriodsStates.entering_hayd_duration)
async def process_hayd_duration(message: Message, state: FSMContext):
    """Обработка продолжительности хайда"""
    try:
        duration = int(message.text)
        
        if duration < config.HAYD_MIN_DAYS or duration > config.HAYD_MAX_DAYS:
            await message.answer(
                f"❌ Продолжительность должна быть от {config.HAYD_MIN_DAYS} до {config.HAYD_MAX_DAYS} дней."
            )
            return
        
        # Сохраняем общую продолжительность хайда (период 0)
        await state.update_data(hayd_duration_general=duration)
        
        # Спрашиваем о родах
        await message.answer(
            "👶 Были ли у вас роды?",
            reply_markup=get_childbirth_keyboard()
        )
        await state.set_state(FemalePeriodsStates.asking_childbirth)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число.")

@router.callback_query(FemalePeriodsStates.asking_childbirth, F.data == "has_childbirth_yes")
async def process_has_childbirth(callback: CallbackQuery, state: FSMContext):
    """Обработка наличия родов"""
    await callback.message.edit_text(
        "👶 Сколько раз у вас были роды?\n\n"
        "Введите число:"
    )
    await state.set_state(FemalePeriodsStates.entering_childbirth_count)

@router.callback_query(FemalePeriodsStates.asking_childbirth, F.data == "has_childbirth_no")
async def process_no_childbirth(callback: CallbackQuery, state: FSMContext):
    """Обработка отсутствия родов"""
    data = await state.get_data()
    user_id = callback.from_user.id
    
    # Сохраняем только общую информацию о хайд
    hayd_info = HaydInfo(
        user_id=user_id,
        average_duration=data['hayd_duration_general'],
        period_number=0
    )
    await periods_repo.save_hayd_info(hayd_info)
    
    # Обновляем информацию пользователя
    await user_repo.update_user(
        telegram_id=user_id,
        has_childbirth=False,
        childbirth_count=0
    )
    
    await callback.message.edit_text(
        "✅ Информация о женских периодах сохранена.\n\n"
        "Теперь можно приступить к расчету намазов и постов."
    )
    await state.clear()

@router.message(FemalePeriodsStates.entering_childbirth_count)
async def process_childbirth_count(message: Message, state: FSMContext):
    """Обработка количества родов"""
    try:
        count = int(message.text)
        
        if count < 1 or count > 20:
            await message.answer("❌ Пожалуйста, введите корректное число (от 1 до 20).")
            return
        
        await state.update_data(
            childbirth_count=count,
            current_childbirth=1,
            childbirth_data=[]
        )
        
        # Начинаем сбор информации о первых родах
        await message.answer(
            "📅 **Информация о 1-х родах**\n\n"
            "Введите среднюю продолжительность хайда ДО первых родов (в днях):",
            parse_mode="Markdown"
        )
        await state.set_state(FemalePeriodsStates.entering_hayd_before_childbirth)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число.")

@router.message(FemalePeriodsStates.entering_hayd_before_childbirth)
async def process_hayd_before(message: Message, state: FSMContext):
    """Обработка хайда до родов"""
    try:
        duration = int(message.text)
        
        if duration < config.HAYD_MIN_DAYS or duration > config.HAYD_MAX_DAYS:
            await message.answer(
                f"❌ Продолжительность должна быть от {config.HAYD_MIN_DAYS} до {config.HAYD_MAX_DAYS} дней."
            )
            return
        
        data = await state.get_data()
        current_num = data['current_childbirth']
        
        await state.update_data(**{f"hayd_before_{current_num}": duration})
        
        await message.answer(
            f"📅 Введите дату {current_num}-х родов в формате ДД.ММ.ГГГГ\n"
            "Например: 15.03.2020"
        )
        await state.set_state(FemalePeriodsStates.entering_childbirth_date)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число.")

@router.message(FemalePeriodsStates.entering_childbirth_date)
async def process_childbirth_date(message: Message, state: FSMContext):
    """Обработка даты родов"""
    childbirth_date = parse_date(message.text)
    
    if not childbirth_date:
        await message.answer("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
        return
    
    data = await state.get_data()
    current_num = data['current_childbirth']
    
    await state.update_data(**{f"childbirth_date_{current_num}": childbirth_date})
    
    await message.answer(
        f"📅 Введите продолжительность нифаса после {current_num}-х родов (в днях, максимум {config.NIFAS_MAX_DAYS}):"
    )
    await state.set_state(FemalePeriodsStates.entering_nifas_duration)

@router.message(FemalePeriodsStates.entering_nifas_duration)
async def process_nifas_duration(message: Message, state: FSMContext):
    """Обработка продолжительности нифаса"""
    try:
        duration = int(message.text)
        
        if duration < 1 or duration > config.NIFAS_MAX_DAYS:
            await message.answer(
                f"❌ Продолжительность должна быть от 1 до {config.NIFAS_MAX_DAYS} дней."
            )
            return
        
        data = await state.get_data()
        current_num = data['current_childbirth']
        
        await state.update_data(**{f"nifas_duration_{current_num}": duration})
        
        # Проверяем, есть ли еще роды
        if current_num < data['childbirth_count']:
            await message.answer(
                f"📅 Введите среднюю продолжительность хайда ПОСЛЕ {current_num}-х родов (в днях):"
            )
            await state.set_state(FemalePeriodsStates.entering_hayd_after_childbirth)
        else:
            # Это были последние роды
            await message.answer(
                f"📅 Введите среднюю продолжительность хайда ПОСЛЕ {current_num}-х родов (в днях):"
            )
            await state.set_state(FemalePeriodsStates.entering_hayd_after_childbirth)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число.")

@router.message(FemalePeriodsStates.entering_hayd_after_childbirth)
async def process_hayd_after(message: Message, state: FSMContext):
    """Обработка хайда после родов"""
    try:
        duration = int(message.text)
        
        if duration < config.HAYD_MIN_DAYS or duration > config.HAYD_MAX_DAYS:
            await message.answer(
                f"❌ Продолжительность должна быть от {config.HAYD_MIN_DAYS} до {config.HAYD_MAX_DAYS} дней."
            )
            return
        
        data = await state.get_data()
        current_num = data['current_childbirth']
        
        await state.update_data(**{f"hayd_after_{current_num}": duration})
        
        # Проверяем, есть ли еще роды
        if current_num < data['childbirth_count']:
            # Переходим к следующим родам
            await state.update_data(current_childbirth=current_num + 1)
            
            await message.answer(
                f"📅 **Информация о {current_num + 1}-х родах**\n\n"
                f"Введите дату {current_num + 1}-х родов в формате ДД.ММ.ГГГГ:",
                parse_mode="Markdown"
            )
            await state.set_state(FemalePeriodsStates.entering_childbirth_date)
        else:
            # Сохраняем всю информацию
            await save_all_periods_info(message, state)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число.")

async def save_all_periods_info(message: Message, state: FSMContext):
    """Сохранение всей информации о периодах"""
    data = await state.get_data()
    user_id = message.from_user.id
    
    # Сохраняем информацию о хайд для каждого периода
    # Период 0 - до первых родов
    if 'hayd_before_1' in data:
        hayd_info = HaydInfo(
            user_id=user_id,
            average_duration=data['hayd_before_1'],
            period_number=0
        )
        await periods_repo.save_hayd_info(hayd_info)
    
    # Сохраняем информацию о каждых родах и хайд после них
    for i in range(1, data['childbirth_count'] + 1):
        # Информация о нифас
        nifas_info = NifasInfo(
            user_id=user_id,
            childbirth_number=i,
            childbirth_date=data[f'childbirth_date_{i}'],
            nifas_duration=data[f'nifas_duration_{i}']
        )
        await periods_repo.save_nifas_info(nifas_info)
        
        # Информация о хайд после родов
        if f'hayd_after_{i}' in data:
            hayd_info = HaydInfo(
                user_id=user_id,
                average_duration=data[f'hayd_after_{i}'],
                period_number=i
            )
            await periods_repo.save_hayd_info(hayd_info)
    
    # Обновляем информацию пользователя
    await user_repo.update_user(
        telegram_id=user_id,
        has_childbirth=True,
        childbirth_count=data['childbirth_count']
    )
    
    await message.answer(
        "✅ **Информация сохранена!**\n\n"
        f"📊 Записано:\n"
        f"• Количество родов: {data['childbirth_count']}\n"
        f"• Периоды хайд и нифас учтены\n\n"
        "Теперь расчет намазов и постов будет производиться с учетом этих периодов.",
        parse_mode="Markdown"
    )
    
    await state.clear()