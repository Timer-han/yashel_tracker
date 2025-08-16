from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from ...keyboards.user.fasting import get_fasting_keyboard, get_fasting_action_keyboard
from ....core.services.women_calculation_service import WomenCalculationService
from ....core.services.user_service import UserService
from ...states.fasting import FastingStates
from ....core.config import config

router = Router()
women_calc_service = WomenCalculationService()
user_service = UserService()

@router.message(F.text == "📿 Посты")
async def show_fasting_menu(message: Message):
    """Показ меню постов"""
    user = await user_service.get_or_create_user(message.from_user.id)
    
    if not user.is_registered:
        await message.answer(
            "📊 Сначала пройдите регистрацию для расчета постов."
        )
        return
    
    stats_text = (
        "📿 **Управление постами**\n\n"
        f"📝 Пропущено дней: **{user.fasting_missed_days}**\n"
        f"✅ Восполнено дней: **{user.fasting_completed_days}**\n"
        f"⏳ Осталось: **{user.fasting_remaining_days}**\n"
    )
    
    if user.fasting_missed_days > 0:
        progress = (user.fasting_completed_days / user.fasting_missed_days) * 100
        progress_bar = "▓" * int(progress / 10) + "░" * (10 - int(progress / 10))
        stats_text += f"\n📊 Прогресс: [{progress_bar}] {progress:.1f}%"
    
    await message.answer(
        stats_text,
        reply_markup=get_fasting_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "fast_calculate")
async def start_fast_calculation(callback: CallbackQuery, state: FSMContext):
    """Начало расчета пропущенных постов"""
    user = await user_service.get_or_create_user(callback.from_user.id)
    
    if not user.birth_date:
        await callback.answer("❌ Укажите дату рождения в настройках", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📅 Введите дату, когда вы начали регулярно соблюдать посты в Рамадан\n"
        "Формат: ДД.ММ.ГГГГ\n\n"
        "Например: 01.05.2023"
    )
    await state.set_state(FastingStates.waiting_for_fast_start_date)

@router.message(FastingStates.waiting_for_fast_start_date)
async def process_fast_start_date(message: Message, state: FSMContext):
    """Обработка даты начала соблюдения постов"""
    from ...utils.date_utils import parse_date
    
    fast_start_date = parse_date(message.text)
    if not fast_start_date:
        await message.answer("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
        return
    
    user = await user_service.get_or_create_user(message.from_user.id)
    
    # Проверяем корректность даты
    adult_age = config.ADULT_AGE_FEMALE if user.gender == 'female' else config.ADULT_AGE_MALE
    adult_date = user.birth_date.replace(year=user.birth_date.year + adult_age)
    
    if fast_start_date <= adult_date:
        await message.answer(
            f"✅ Отлично! Вы начали соблюдать посты с момента совершеннолетия.\n"
            "Пропущенных постов нет."
        )
        await state.clear()
        return
    
    # Получаем данные о родах для женщин
    childbirth_data = user.get_childbirth_info() if user.gender == 'female' else None
    
    # Рассчитываем пропущенные посты
    result = women_calc_service.calculate_missed_fasts_detailed(
        birth_date=user.birth_date,
        adult_date=adult_date,
        fast_start_date=fast_start_date,
        gender=user.gender,
        hayd_average_days=user.hayd_average_days,
        childbirth_data=childbirth_data
    )
    
    # Сохраняем результат
    from ....core.database.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    await user_repo.update_user(
        telegram_id=message.from_user.id,
        fasting_missed_days=result['total']
    )
    
    # Формируем детальный отчет
    report_text = (
        f"✅ **Расчет завершен!**\n\n"
        f"📅 Период: с {adult_date.strftime('%d.%m.%Y')} по {fast_start_date.strftime('%d.%m.%Y')}\n"
        f"📊 Количество Рамаданов: {result['ramadan_count']}\n\n"
        f"📝 **Всего пропущено дней поста: {result['total']}**\n\n"
    )
    
    if user.gender == 'female':
        report_text += (
            "**Детализация для женщин:**\n"
            f"• Дней хайда во время Рамаданов: ~{result['hayd_days']}\n"
            f"• Дней нифаса во время Рамаданов: {result['nifas_days']}\n\n"
            "💫 **Важно:** Посты, пропущенные из-за хайда и нифаса, "
            "также нужно восполнить в соотношении 1:1\n"
        )
    
    report_text += "\n🤲 Пусть Аллах облегчит вам восполнение!"
    
    await message.answer(report_text, parse_mode="Markdown")
    await state.clear()

@router.callback_query(F.data.startswith("fast_"))
async def handle_fasting_actions(callback: CallbackQuery):
    """Обработка действий с постами"""
    action = callback.data.split("_")[1]
    
    from ....core.database.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    user = await user_service.get_or_create_user(callback.from_user.id)
    
    if action == "add":
        # Увеличиваем восполненные
        await user_repo.update_user(
            telegram_id=callback.from_user.id,
            fasting_completed_days=user.fasting_completed_days + 1
        )
        await callback.answer("✅ Добавлен 1 день поста")
        
    elif action == "remove":
        # Уменьшаем восполненные
        if user.fasting_completed_days > 0:
            await user_repo.update_user(
                telegram_id=callback.from_user.id,
                fasting_completed_days=user.fasting_completed_days - 1
            )
            await callback.answer("➖ Убран 1 день поста")
        else:
            await callback.answer("❌ Нет восполненных дней", show_alert=True)
    
    # Обновляем меню
    await show_fasting_menu(callback.message)