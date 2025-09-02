from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from ...keyboards.user.fasting import (
    get_fasting_keyboard, 
    get_fasting_calculation_method_keyboard,
    get_female_fasting_calculation_method_keyboard,
    get_fasting_confirmation_keyboard
)
from ....core.services.fasting_calculation_service import FastingCalculationService
from ....core.services.user_service import UserService
from ...states.fasting import FastingStates
from ....core.config import config, escape_markdown
from ...utils.date_utils import parse_date, format_date

router = Router()
fasting_calc_service = FastingCalculationService()
user_service = UserService()

@router.message(F.text == "📿 Посты")
async def show_fasting_menu(message: Message, state: FSMContext):
    """Показ меню постов"""
    await state.clear()
    
    user = await user_service.get_or_create_user(message.from_user.id)
    
    if not user.is_registered:
        await message.answer(
            "📊 Сначала пройди регистрацию для работы с постами\.\n"
            "Используй команду /start",
            parse_mode="MarkdownV2"
        )
        return
    
    # Получаем статистику постов
    missed_days = user.fasting_missed_days or 0
    completed_days = user.fasting_completed_days or 0
    remaining_days = max(0, missed_days - completed_days)
    
    stats_text = (
        "📿 *Посты*\n\n"
        f"📝 Пропущено дней: *{missed_days}*\n"
        f"✅ Восполнено дней: *{completed_days}*\n"
        f"⏳ Осталось: *{remaining_days}*\n"
    )
    
    if missed_days > 0:
        progress = (completed_days / missed_days) * 100
        progress_bar = "▓" * int(progress / 10) + "░" * (10 - int(progress / 10))
        stats_text += escape_markdown(f"\n📊 Прогресс: [{progress_bar}] {progress:.1f}%")
    
    await message.answer(
        stats_text,
        reply_markup=get_fasting_keyboard(),
        parse_mode="MarkdownV2"
    )

@router.callback_query(F.data == "fast_calculate")
async def start_fast_calculation(callback: CallbackQuery, state: FSMContext):
    """Начало расчета постов - выбор метода"""
    user = await user_service.get_or_create_user(callback.from_user.id)
    
    if not user.is_registered:
        await callback.answer("❌ Сначала пройди регистрацию", show_alert=True)
        return
    
    # if user.gender == 'male':
    #     reply_markup = get_fasting_calculation_method_keyboard()
    # else:
    #     reply_markup = get_female_fasting_calculation_method_keyboard()
        
    reply_markup = get_fasting_calculation_method_keyboard()
    
    await callback.message.edit_text(
        "🔢 *Расчет пропущенных постов*\n\n"
        "Выбери способ расчета:",
        reply_markup=reply_markup,
        parse_mode="MarkdownV2"
    )
    await state.set_state(FastingStates.choosing_method)

# @router.callback_query(FastingStates.choosing_method, F.data == "fast_calc_from_age")
# async def calc_fasts_from_age(callback: CallbackQuery, state: FSMContext):
#     """Расчет постов от совершеннолетия"""
#     await callback.message.edit_text(
#         "📅 *Расчет от совершеннолетия*\n\n"
#         "Этот метод рассчитает посты от возраста совершеннолетия до даты, "
#         "когда вы начали регулярно соблюдать посты Рамадана.\n\n"
#         "Введите дату, когда вы начали регулярно соблюдать посты в формате ДД.ММ.ГГГГ:\n"
#         "Например: 01.05.2020"
#     )
#     await state.set_state(FastingStates.waiting_for_fast_start_date)

# @router.message(FastingStates.waiting_for_fast_start_date)
# async def process_fast_start_date(message: Message, state: FSMContext):
#     """Обработка даты начала соблюдения постов (от совершеннолетия)"""
#     fast_start_date = parse_date(message.text)
#     if not fast_start_date:
#         await message.answer("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
#         return
    
#     user = await user_service.get_or_create_user(message.from_user.id)
    
#     if not user.birth_date:
#         await message.answer("❌ Для этого расчета нужна дата рождения. Проверьте регистрацию.")
#         return
    
#     # Рассчитываем посты
#     result = fasting_calc_service.calculate_fasts_from_age(
#         birth_date=user.birth_date,
#         fast_start_date=fast_start_date,
#         gender=user.gender or 'male',
#         hayd_average_days=user.hayd_average_days,
#         childbirth_data=user.get_childbirth_info()
#     )
    
#     await _show_calculation_result(message, result, state, fast_start_date)

@router.callback_query(FastingStates.choosing_method, F.data == "fast_calc_years")
async def calc_fasts_between_dates(callback: CallbackQuery, state: FSMContext):
    """Расчет постов за года"""
    # user = await user_service.get_or_create_user(callback.from_user.id)
    # if user.gender == 'female':
    #     await callback.answer(
    #         "❌ Для женщин этот метод не подходит.\n"
    #         "Используйте другой метод расчета постов.",
    #         reply_markup=get_female_fasting_calculation_method_keyboard()
    #     )

    user = await user_service.get_or_create_user(callback.from_user.id)
    
    if user.gender == 'male':
        await callback.message.edit_text(
            "📅 *Сколько лет постов ты пропустил\?*\n\n"
            "Введи полное число пропущенных лет с момента совершеннолетия по Исламу до начала соблюдения постов\.\n\n"
            "P\.S\. Дальше ты сможешь самостоятельно прибавить дни, если в этом будет необходимость\.",
            parse_mode='MarkdownV2'
        )
    else:
        await callback.message.edit_text(
            "📅 *Расчёт между датами*\n\n"
            "Сколько лет постов ты пропустила\?\n",
            parse_mode='MarkdownV2'
        )
    await state.set_state(FastingStates.waiting_for_fast_year_count)

# @router.message(FastingStates.waiting_for_fast_period_start)
# async def process_fast_period_start(message: Message, state: FSMContext):
#     """Обработка начальной даты периода постов"""
#     start_date = parse_date(message.text)
#     if not start_date:
#         await message.answer("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
#         return
    
#     await state.update_data(fast_period_start=start_date)
    
#     await message.answer(
#         "📅 Введите конечную дату (по какую дату считать пропущенные посты) в формате ДД.ММ.ГГГГ:\n"
#         "Например: 01.06.2020"
#     )
#     await state.set_state(FastingStates.waiting_for_fast_period_end)

# @router.message(FastingStates.waiting_for_fast_period_end)
# async def process_fast_period_end(message: Message, state: FSMContext):
#     """Обработка конечной даты периода постов"""
#     end_date = parse_date(message.text)
#     if not end_date:
#         await message.answer("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
#         return
    
#     data = await state.get_data()
#     start_date = data['fast_period_start']
    
#     if end_date <= start_date:
#         await message.answer("❌ Конечная дата должна быть больше начальной даты.")
#         return
    
#     user = await user_service.get_or_create_user(message.from_user.id)
    
#     # Рассчитываем посты между датами
#     result = fasting_calc_service.calculate_fasts_between_dates(
#         start_date=start_date,
#         end_date=end_date,
#         gender=user.gender or 'male',
#         hayd_average_days=user.hayd_average_days,
#         childbirth_data=user.get_childbirth_info()
#     )
    
#     await _show_calculation_result(message, result, state, end_date, start_date)
    
@router.message(FastingStates.waiting_for_fast_year_count)
async def process_fast_period_end(message: Message, state: FSMContext):
    """Обработка пропущенных"""
    
    try:
        years = int(message.text.strip())
        if years < 0:
            await message.answer("❌ Количество лет не может быть отрицательным\.", parse_mode="MarkdownV2")
            return
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число\.", parse_mode="MarkdownV2")
        return

    
    user = await user_service.get_or_create_user(message.from_user.id)
    
    # Рассчитываем посты между датами
    result = fasting_calc_service.calculate_fasts_by_years(years=years)
    
    await _show_calculation_result(message, result, state, method='years')

@router.callback_query(FastingStates.choosing_method, F.data == "fast_calc_manual")
async def calc_fasts_manual(callback: CallbackQuery, state: FSMContext):
    """Ручной ввод количества постов"""
    await callback.message.edit_text(
        "✋ *Ручной ввод количества*\n\n"
        "Введите количество пропущенных дней поста:\n\n"
        "Например: 120",
        parse_mode='MarkdownV2'
    )
    await state.set_state(FastingStates.waiting_for_manual_days)

@router.message(FastingStates.waiting_for_manual_days)
async def process_manual_fast_days(message: Message, state: FSMContext):
    """Обработка ручного ввода дней поста"""
    try:
        days = int(message.text)
        if days < 0:
            await message.answer("❌ Количество не может быть отрицательным\.", parse_mode="MarkdownV2")
            return
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число\.", parse_mode="MarkdownV2")
        return
    
    result = {
        'fasting_days': days,
        'total_days': days,
        'excluded_days': 0,
        'details': 'Ручной ввод количества дней',
        'years': 0
    }
    
    await _show_calculation_result(message, result, state, method="manual")

async def _show_calculation_result(message: Message, result: dict, state: FSMContext, 
                                   end_date=None, start_date=None, method=None):
    """Показ результата расчета с подтверждением"""
    
    # Формируем текст результата
    result_text = "✅ *Расчет завершен\!*\n\n"
    
    if method == "manual" or method == "years":
        result_text += f"📝 *Количество пропущенных дней поста: {result['fasting_days']}*\n\n"
    else:
        if start_date and end_date:
            result_text += f"📅 Период: с {format_date(start_date)} по {format_date(end_date)}\n"
        elif end_date:
            result_text += f"📅 Период: до {format_date(end_date)}\n"
        
        if result.get('years', 0) > 0:
            result_text += f"🗓️ Количество лет: {result['years']}\n"
        
        result_text += f"📊 Базовых дней поста: {result['total_days']}\n"
        
        if result['excluded_days'] > 0:
            result_text += f"❌ Исключено \(хайд/нифас\): {result['excluded_days']}\n"
        
        result_text += f"\n📝 *Итого пропущенных дней поста: {result['fasting_days']}*\n\n"
        
        # Добавляем детали для женщин
        if result.get('details'):
            result_text += result['details'] + "\n\n"
    
    result_text += "💾 Сохранить этот результат\?"
    
    # Сохраняем результат в состоянии
    await state.update_data(calculation_result=result['fasting_days'])
    
    await message.answer(
        result_text,
        reply_markup=get_fasting_confirmation_keyboard(),
        parse_mode="MarkdownV2"
    )
    await state.set_state(FastingStates.confirmation)

@router.callback_query(FastingStates.confirmation, F.data == "fast_confirm_save")
async def save_calculation_result(callback: CallbackQuery, state: FSMContext):
    """Сохранение результата расчета"""
    data = await state.get_data()
    fasting_days = data.get('calculation_result', 0)
    
    # Сохраняем в базу данных
    from ....core.database.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    
    success = await user_repo.update_user(
        telegram_id=callback.from_user.id,
        fasting_missed_days=fasting_days,
        fasting_completed_days=0  # Сбрасываем восполненные при новом расчете
    )
    
    if success:
        await callback.message.edit_text(
            f"✅ Результат сохранен\!\n\n"
            f"📝 Пропущенных дней поста: *{fasting_days}*\n\n"
            "🤲 Пусть Аллах облегчит тебе восполнение постов\!",
            parse_mode="MarkdownV2"
        )
    else:
        await callback.message.edit_text("❌ Ошибка при сохранении данных.")
    
    await state.clear()

@router.callback_query(F.data.in_(["fast_confirm_cancel", "fast_calc_cancel"]))
async def cancel_calculation(callback: CallbackQuery, state: FSMContext):
    """Отмена расчета постов"""
    await callback.message.edit_text("❌ Расчет отменен.")
    await state.clear()

@router.callback_query(F.data.startswith("fast_"))
async def handle_fasting_actions(callback: CallbackQuery):
    """Обработка действий с постами"""
    action = callback.data.split("_")[1]
    
    user = await user_service.get_or_create_user(callback.from_user.id)
    
    if not user.is_registered:
        await callback.answer("❌ Сначала пройдите регистрацию", show_alert=True)
        return
    
    from ....core.database.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    
    if action == "completed":
        # Увеличиваем восполненные дни
        new_completed = user.fasting_completed_days + 1
        await user_repo.update_user(
            telegram_id=callback.from_user.id,
            fasting_completed_days=new_completed
        )
        
        # Получаем обновленные данные
        updated_user = await user_service.get_or_create_user(callback.from_user.id)
        await send_fasting_action_message_and_update_menu(callback, "completed", updated_user)
        
    elif action == "missed":
        # Увеличиваем пропущенные дни
        new_missed = user.fasting_missed_days + 1
        await user_repo.update_user(
            telegram_id=callback.from_user.id,
            fasting_missed_days=new_missed
        )
        
        # Получаем обновленные данные
        updated_user = await user_service.get_or_create_user(callback.from_user.id)
        await send_fasting_action_message_and_update_menu(callback, "missed", updated_user)
    
    elif action == "stats":
        # Показываем детальную статистику
        missed_days = user.fasting_missed_days or 0
        completed_days = user.fasting_completed_days or 0
        remaining_days = max(0, missed_days - completed_days)
        
        stats_text = (
            f"📊 *Детальная статистика постов:*\n\n"
            f"📝 Всего пропущено: *{missed_days}*\n"
            f"✅ Восполнено: *{completed_days}*\n"
            f"⏳ Осталось: *{remaining_days}*\n\n"
        )
        
        if missed_days > 0:
            progress = (completed_days / missed_days) * 100
            progress_bar = "▓" * int(progress / 10) + "░" * (10 - int(progress / 10))
            stats_text += escape_markdown(f"📈 Прогресс: [{progress_bar}] {progress:.1f}%\n\n")
            
            if progress >= 80:
                stats_text += "🎯 Вы почти у цели\! Не останавливайтесь\!"
            elif progress >= 50:
                stats_text += "💪 Отличный прогресс\! Продолжайте в том же духе\!"
            elif progress >= 25:
                stats_text += "📈 Хорошее начало\! Держите темп\!"
            else:
                stats_text += "🌱 Каждый день поста приближает к цели\!"
        elif missed_days == 0:
            stats_text += "💡 Сначала рассчитайте количество пропущенных постов"
        else:
            stats_text += "🎉 Все посты восполнены\! Машаа Ллах\!"
        
        # if user.gender == 'female' and user.hayd_average_days:
        #     stats_text += f"\n\n📋 *Примечание для женщин:*\n"
        #     stats_text += f"• Текущая продолжительность хайда: {user.hayd_average_days} дней\n"
        #     stats_text += f"• Расчет учитывает дни хайда и нифаса\n"
        #     if user.childbirth_count > 0:
        #         stats_text += f"• Количество родов: {user.childbirth_count}\n"
                
        stats_text += "\n\n🤲 Да примет Аллах ваши усилия\!"
        
        await callback.message.answer(stats_text, parse_mode="MarkdownV2")
        return
    
    elif action == "reset":
        # Сброс всех данных о постах
        await user_repo.update_user(
            telegram_id=callback.from_user.id,
            fasting_missed_days=0,
            fasting_completed_days=0
        )
        await callback.answer("🔄 Данные о постах сброшены")
        
        # Обновляем меню после сброса
        updated_user = await user_service.get_or_create_user(callback.from_user.id)
        
        # Отправляем новое меню после сброса
        menu_text = (
            "📿 *Посты*\n\n"
            f"📝 Пропущено дней: *{updated_user.fasting_missed_days or 0}*\n"
            f"✅ Восполнено дней: *{updated_user.fasting_completed_days or 0}*\n"
            f"⏳ Осталось: *{max(0, (updated_user.fasting_missed_days or 0) - (updated_user.fasting_completed_days or 0))}*\n"
        )
        
        await callback.message.edit_text(
            menu_text,
            reply_markup=get_fasting_keyboard(),
            parse_mode="MarkdownV2"
        )

# Обработчики для быстрых действий (изменение на несколько дней)
@router.callback_query(F.data.startswith("fast_adjust_"))
async def handle_fast_adjustment(callback: CallbackQuery):
    """Обработка быстрого изменения количества дней поста"""
    try:
        parts = callback.data.split("_")
        action_type = parts[2]  # "completed" или "missed"
        amount = int(parts[3])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка данных", show_alert=True)
        return
    
    user = await user_service.get_or_create_user(callback.from_user.id)
    
    if not user.is_registered:
        await callback.answer("❌ Сначала пройдите регистрацию", show_alert=True)
        return
    
    from ....core.database.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    
    if action_type == "completed":
        # Увеличиваем восполненные дни
        new_completed = user.fasting_completed_days + amount
        await user_repo.update_user(
            telegram_id=callback.from_user.id,
            fasting_completed_days=new_completed
        )
        
    elif action_type == "missed":
        # Увеличиваем пропущенные дни
        new_missed = user.fasting_missed_days + amount
        await user_repo.update_user(
            telegram_id=callback.from_user.id,
            fasting_missed_days=new_missed
        )
    
    # Получаем обновленные данные и отправляем уведомление
    updated_user = await user_service.get_or_create_user(callback.from_user.id)
    await send_fasting_action_message_and_update_menu(callback, action_type, updated_user, amount)

@router.callback_query(F.data == "fast_done")
async def finish_fast_actions(callback: CallbackQuery):
    """Завершение работы с постами"""
    await show_fasting_menu(callback.message)

async def send_fasting_action_message_and_update_menu(callback_query, action_type: str, user_data, amount: int = 1):
    """Отправка уведомления о действии и обновление меню постов"""
    
    # Формируем текст уведомления в зависимости от действия
    if action_type == "completed":
        if amount == 1:
            action_text = "восполнен 1 день поста"
            action_emoji = "✅"
        else:
            action_text = f"восполнено {amount} дней поста"
            action_emoji = "✅"
    elif action_type == "missed":
        if amount == 1:
            action_text = "добавлен 1 пропущенный день поста"
            action_emoji = "➕"
        else:
            action_text = f"добавлено {amount} пропущенных дней поста"
            action_emoji = "➕"
    else:
        action_text = "изменен"
        action_emoji = "🔄"
    
    missed_days = user_data.fasting_missed_days or 0
    completed_days = user_data.fasting_completed_days or 0
    remaining_days = max(0, missed_days - completed_days)
    
    # Определяем progress bar
    if missed_days > 0:
        progress = (completed_days / missed_days) * 100
        progress_bar = "▓" * int(progress / 10) + "░" * (10 - int(progress / 10))
        progress_text = escape_markdown(f"\n📊 [{progress_bar}] {progress:.1f}%")
    else:
        progress_text = ""
    
    notification_text = (
        f"{action_emoji} *Посты:* {action_text}\n\n"
        f"📝 Всего пропущено: *{missed_days}*\n"
        f"✅ Восполнено: *{completed_days}*\n"
        f"⏳ Осталось: *{remaining_days}*"
        f"{progress_text}"
    )
    
    # Мотивационное сообщение
    if remaining_days == 0 and missed_days > 0:
        notification_text += f"\n\n🎉 *Машаа Ллах\!* Все посты восполнены\!"
    
    # 1. Редактируем текущее сообщение в уведомление
    await callback_query.message.edit_text(notification_text, parse_mode="MarkdownV2")
    
    # 2. Отправляем новое меню постов
    menu_text = (
        "📿 *Посты*\n\n"
        f"📝 Пропущено дней: *{missed_days}*\n"
        f"✅ Восполнено дней: *{completed_days}*\n"
        f"⏳ Осталось: *{remaining_days}*\n"
    )
    
    if missed_days > 0:
        progress = (completed_days / missed_days) * 100
        progress_bar = "▓" * int(progress / 10) + "░" * (10 - int(progress / 10))
        menu_text += escape_markdown(f"\n📊 Прогресс: [{progress_bar}] {progress:.1f}%")
    
    await callback_query.message.answer(
        menu_text,
        reply_markup=get_fasting_keyboard(),
        parse_mode="MarkdownV2"
    )