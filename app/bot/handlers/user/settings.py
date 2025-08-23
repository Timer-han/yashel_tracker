from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from app import __version__

from ...keyboards.user.settings import (
    get_settings_menu_keyboard, 
    get_change_confirmation_keyboard,
    get_notifications_confirmation_keyboard
)
from ...keyboards.user.registration import get_gender_keyboard, get_gender_inline_keyboard
from ....core.config import escape_markdown
from ....core.services.user_service import UserService
from ....core.services.prayer_service import PrayerService
from ...states.settings import SettingsStates
from ...utils.text_messages import text_message


router = Router()
user_service = UserService()
prayer_service = PrayerService()

@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    """Показ настроек"""
    user = await user_service.get_or_create_user(message.from_user.id)
    
    display_name = escape_markdown(user.display_name)
    birth_date = escape_markdown(user.birth_date.strftime('%d.%m.%Y') if user.birth_date else 'Не указана')
    city = escape_markdown(user.city or 'Не указан')
    gender = 'Мужской' if user.gender == 'male' else 'Женский' if user.gender == 'female' else 'Не указан'
    notifications = 'Включены' if user.notifications_enabled else 'Отключены'
    settings_text = text_message.SETTINGS_TEXT.format(
        display_name=display_name,
        birth_date=birth_date,
        city=city,
        gender=gender,
        notifications=notifications
    )
    
    await message.answer(
        settings_text,
        reply_markup=get_settings_menu_keyboard(user.notifications_enabled),
        parse_mode="MarkdownV2"
    )

@router.callback_query(F.data == "change_gender")
async def change_gender(callback: CallbackQuery, state: FSMContext):
    """Изменение пола"""
    await callback.message.edit_text(
        "👤 Выбери ваш пол:",
        reply_markup=get_gender_inline_keyboard()
    )
    await state.set_state(SettingsStates.waiting_for_gender)

@router.callback_query(F.data.startswith("set_gender_"))
async def process_gender_change(callback: CallbackQuery, state: FSMContext):
    """Обработка изменения пола"""
    gender = callback.data.split("_")[2]  # male или female
    
    success = await user_service.user_repo.update_user(
        telegram_id=callback.from_user.id,
        gender=gender
    )
    
    if success:
        gender_text = "мужской" if gender == "male" else "женский"
        await callback.message.edit_text(f"✅ Пол изменен на {gender_text}!")
    else:
        await callback.message.edit_text("❌ Ошибка при изменении пола.")
    
    await state.clear()

@router.callback_query(F.data == "change_birth_date")
async def change_birth_date(callback: CallbackQuery, state: FSMContext):
    """Изменение даты рождения"""
    await callback.message.edit_text(
        "📅 Введи новую дату рождения в формате ДД.ММ.ГГГГ\n"
        "Например: 15.03.1990"
    )
    await state.set_state(SettingsStates.waiting_for_birth_date)

@router.message(SettingsStates.waiting_for_birth_date)
async def process_new_birth_date(message: Message, state: FSMContext):
    """Обработка новой даты рождения"""
    try:
        birth_date = datetime.strptime(message.text, "%d.%m.%Y").date()
        
        success = await user_service.user_repo.update_user(
            telegram_id=message.from_user.id,
            birth_date=birth_date
        )
        
        if success:
            await message.answer("✅ Дата рождения успешно изменена!")
        else:
            await message.answer("❌ Ошибка при изменении даты рождения.")
    
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты. Используй формат ДД.ММ.ГГГГ\n"
            "Например: 15.03.1990"
        )
        return
    
    await state.clear()

@router.callback_query(F.data == "change_city")
async def change_city(callback: CallbackQuery, state: FSMContext):
    """Изменение города"""
    await callback.message.edit_text("🏙️ Введи новый город:")
    await state.set_state(SettingsStates.waiting_for_city)

@router.message(SettingsStates.waiting_for_city)
async def process_new_city(message: Message, state: FSMContext):
    """Обработка нового города"""
    new_city = message.text.strip()
    
    success = await user_service.user_repo.update_user(
        telegram_id=message.from_user.id,
        city=new_city
    )
    
    if success:
        await message.answer("✅ Город успешно изменен!")
    else:
        await message.answer("❌ Ошибка при изменении города.")
    
    await state.clear()

@router.callback_query(F.data == "disable_notifications")
async def disable_notifications(callback: CallbackQuery):
    """Отключение ежедневных уведомлений"""
    await callback.message.edit_text(
        "🔕 *Отключение ежедневных уведомлений*\n\n"
        "Ты уверен, что хочешь отключить ежедневные напоминания о восполнении намазов\?\n\n"
        "⚠️ Обрати внимание: административные рассылки ты будешь получать по\-прежнему\.",
        reply_markup=get_notifications_confirmation_keyboard(),
        parse_mode="MarkdownV2"
    )
    await callback.answer()

@router.callback_query(F.data == "enable_notifications")
async def enable_notifications(callback: CallbackQuery):
    """Включение ежедневных уведомлений"""
    await callback.message.edit_text(
        "🔔 *Включение ежедневных уведомлений*\n\n"
        "Хочешь включить ежедневные напоминания о восполнении намазов\?\n\n"
        "📱 Уведомления будут приходить каждый день в 20:00\.",
        reply_markup=get_notifications_confirmation_keyboard(),
        parse_mode="MarkdownV2"
    )
    await callback.answer()

@router.callback_query(F.data == "confirm_notifications_change")
async def confirm_notifications_change(callback: CallbackQuery):
    """Подтверждение изменения настроек уведомлений"""
    user = await user_service.get_or_create_user(callback.from_user.id)
    
    # Инвертируем текущее состояние
    new_state = 0 if user.notifications_enabled else 1
    
    success = await user_service.user_repo.update_user(
        telegram_id=callback.from_user.id,
        daily_notifications_enabled=new_state
    )
    
    if success:
        if new_state == 1:
            text = (
                "✅ *Ежедневные уведомления включены\!*\n\n"
                "🔔 Ты будешь получать напоминания о восполнении долгов каждый день в 20:00\.\n\n"
                "🤲 Пусть Аллах облегчит тебе восполнение намазов и постов\!"
            )
        else:
            text = (
                "✅ *Ежедневные уведомления отключены\!*\n\n"
                "🔕 Ты больше не будешь получать автоматические напоминания\.\n\n"
                "💡 Обратно сможешь включить их в любое время через настройки\."
            )
        
        await callback.message.edit_text(text, parse_mode="MarkdownV2")
    else:
        await callback.message.edit_text("❌ Ошибка при изменении настроек уведомлений\.")

@router.callback_query(F.data == "cancel_notifications_change")
async def cancel_notifications_change(callback: CallbackQuery):
    """Отмена изменения настроек уведомлений"""
    user = await user_service.get_or_create_user(callback.from_user.id)

    
    display_name = escape_markdown(user.display_name)
    birth_date = escape_markdown(user.birth_date.strftime('%d.%m.%Y') if user.birth_date else 'Не указана')
    city = escape_markdown(user.city or 'Не указан')
    gender = 'Мужской' if user.gender == 'male' else 'Женский' if user.gender == 'female' else 'Не указан'
    notifications = 'Включены' if user.notifications_enabled else 'Отключены'
    
    settings_text = text_message.SETTINGS_TEXT.format(
        display_name=display_name,
        birth_date=birth_date,
        city=city,
        gender=gender,
        notifications=notifications
    )
    
    await callback.message.edit_text(
        settings_text,
        reply_markup=get_settings_menu_keyboard(user.notifications_enabled),
        parse_mode="MarkdownV2"
    )

@router.callback_query(F.data == "export_data")
async def export_data(callback: CallbackQuery):
    """Экспорт данных пользователя с полной информацией"""
    user = await user_service.get_or_create_user(callback.from_user.id)
    stats = await prayer_service.get_user_statistics(callback.from_user.id)
    
    telegram_id = user.telegram_id
    display_name = escape_markdown(user.display_name)
    gender = escape_markdown('Мужской' if user.gender == 'male' else 'Женский' if user.gender == 'female' else 'Не указан')
    birth_date = escape_markdown(user.birth_date.strftime('%d.%m.%Y') if user.birth_date else 'Не указана')
    city = escape_markdown(user.city or 'Не указан')
    role = escape_markdown(user.role)
    created_at = escape_markdown(user.created_at.strftime('%d.%m.%Y %H:%M') if hasattr(user, 'created_at') and user.created_at else 'Неизвестно')
    notifications_enabled = escape_markdown('Включены' if user.notifications_enabled else 'Отключены')
    

        
    export_text = (
        f"📊 *Экспорт данных пользователя*\n\n"
        f"*👤 Профиль:*\n"
        f"• Telegram ID: `{telegram_id}`\n"
        f"• Имя: {display_name}\n"
        f"• Пол: {gender}\n"
        f"• Дата рождения: {birth_date}\n"
        f"• Город: {city}\n"
        f"• Роль: {role}\n"
        f"• Дата регистрации: {created_at}\n"
        f"• Ежедневные уведомления: {notifications_enabled}\n\n"
    )
    
    # Статистика намазов
    export_text += (
        f"*🕌 Статистика намазов:*\n"
        f"• Всего пропущено: {stats['total_missed']}\n"
        f"• Восполнено: {stats['total_completed']}\n"
        f"• Осталось: {stats['total_remaining']}\n"
    )
    
    if stats['total_missed'] > 0:
        progress = (stats['total_completed'] / stats['total_missed']) * 100
        export_text += escape_markdown(f"• Прогресс восполнения: {progress:.1f}%\n")
    
    export_text += "\n*📋 Детали по намазам:*\n"
    for prayer_name, data in stats['prayers'].items():
        if data['total'] > 0:
            prayer_progress = (data['completed'] / data['total']) * 100 if data['total'] > 0 else 0
            export_text += escape_markdown(f"• {prayer_name}: {data['completed']}/{data['total']} ({prayer_progress:.1f}%)\n")
    
    # Статистика постов
    missed_fasts = user.fasting_missed_days or 0
    completed_fasts = user.fasting_completed_days or 0
    remaining_fasts = max(0, missed_fasts - completed_fasts)
    
    export_text += (
        f"\n*📿 Статистика постов:*\n"
        f"• Всего пропущено дней: {missed_fasts}\n"
        f"• Восполнено дней: {completed_fasts}\n"
        f"• Осталось дней: {remaining_fasts}\n"
    )
    
    if missed_fasts > 0:
        fast_progress = (completed_fasts / missed_fasts) * 100
        export_text += escape_markdown(f"• Прогресс восполнения: {fast_progress:.1f}%\n")
    
    # # Специальная информация для женщин
    # if False:
    #     if user.gender == 'female':
    #         export_text += f"\n*👩 Информация для женщин:*\n"
            
    #         if user.hayd_average_days:
    #             export_text += f"• Текущая продолжительность хайда: {user.hayd_average_days} дней\n"
    #         else:
    #             export_text += f"• Продолжительность хайда: не указана\n"
            
    #         export_text += f"• Количество родов: {user.childbirth_count or 0}\n"
            
    #         # Детальная информация о родах
    #         if user.childbirth_count and user.childbirth_count > 0:
    #             childbirth_info = user.get_childbirth_info()
    #             if childbirth_info:
    #                 export_text += f"\n*👶 Детали родов:*\n"
    #                 for i, birth in enumerate(childbirth_info, 1):
    #                     birth_date = birth.get('date', 'неизвестно')
    #                     nifas_days = birth.get('nifas_days', 0)
    #                     hayd_before = birth.get('hayd_before', 0)
                        
    #                     export_text += (
    #                         f"• {i}-е роды:\n"
    #                         f"  - Дата: {birth_date}\n"
    #                         f"  - Нифас: {nifas_days} дней\n"
    #                         f"  - Хайд до родов: {hayd_before} дней\n"
    #                     )
            
    #         # Дополнительные расчеты для женщин
    #         if user.birth_date and user.hayd_average_days:
    #             from ....core.services.calculation_service import CalculationService
    #             calc_service = CalculationService()
    #             age = calc_service.calculate_age(user.birth_date)
                
    #             # Примерное количество циклов за репродуктивный период
    #             reproductive_years = max(0, age - 9)  # с 9 лет (совершеннолетие для девочек)
    #             approximate_cycles = reproductive_years * 12  # примерно 12 циклов в год
                
    #             export_text += (
    #                 f"\n*📊 Дополнительные расчеты:*\n"
    #                 f"• Возраст: {age} лет\n"
    #                 f"• Репродуктивный период: ~{reproductive_years} лет\n"
    #                 f"• Примерное количество циклов: ~{approximate_cycles}\n"
    #             )

    adult_date = escape_markdown(user.adult_date.strftime('%d.%m.%Y') if user.adult_date else 'Не установлена')
    prayer_start_date = escape_markdown(user.prayer_start_date.strftime('%d.%m.%Y') if user.prayer_start_date else 'Не установлена')
    last_activity = escape_markdown(user.last_activity.strftime('%d.%m.%Y %H:%M') if hasattr(user, 'last_activity') and user.last_activity else 'Неизвестно')
    is_registered = escape_markdown('Завершена' if user.is_registered else 'Не завершена')
    export_date = escape_markdown((datetime.now() + timedelta(hours=3)).strftime('%d.%m.%Y %H:%M:%S'))
    version = escape_markdown(__version__)

    # Системная информация
    export_text += (
        f"\n*⚙️ Системная информация:*\n"
        # f"• Дата совершеннолетия: {adult_date}\n"
        f"• Дата начала намазов: {prayer_start_date}\n" if user.gender == 'male' else f""
        f"• Последняя активность: {last_activity}\n"
        f"• Статус регистрации: {is_registered}\n"
    )
    
    # Информация об экспорте
    export_text += (
        f"\n*📤 Информация об экспорте:*\n"
        f"• Дата экспорта: {export_date}\n"
        f"• Версия системы: Яшел Трекер v{version}\n"
        f"• Формат данных: Полный экспорт\n"
        f"\n💾 Сохрани эти данные в надежном месте\.\n"
        f"📋 Эти данные можно использовать для восстановления прогресса при необходимости\."
    )
    
    await callback.message.edit_text(export_text, parse_mode="MarkdownV2")

@router.callback_query(F.data == "reset_all_data")
async def confirm_reset_all_data(callback: CallbackQuery):
    """Подтверждение полного сброса"""
    await callback.message.edit_text(
        "🔄 *Полный сброс данных*\n\n"
        "⚠️ *ВНИМАНИЕ\!* Это действие:\n"
        "• Удалит всю статистику намазов\n"
        "• Сбросит настройки профиля\n"
        "• Потребует повторной регистрации\n\n"
        "Это действие *НЕОБРАТИМО*\!\n\n"
        "Ты действительно хочешь продолжить\?",
        reply_markup=get_change_confirmation_keyboard("reset_all"),
        parse_mode="MarkdownV2"
    )

@router.callback_query(F.data == "confirm_reset_all")
async def reset_all_data_confirmed(callback: CallbackQuery):
    """Подтвержденный полный сброс"""
    # Сбрасываем намазы
    await prayer_service.reset_user_prayers(callback.from_user.id)
    
    # Сбрасываем регистрацию пользователя
    await user_service.user_repo.update_user(
        telegram_id=callback.from_user.id,
        is_registered=False,
        gender=None,
        birth_date=None,
        city=None,
        prayer_start_date=None,
        adult_date=None,
        fasting_missed_days=0,
        fasting_completed_days=0,
        hayd_average_days=None,
        childbirth_count=0,
        childbirth_data=None,
        daily_notifications_enabled=1  # Сбрасываем на дефолтное значение
    )
    
    await callback.message.edit_text(
        "✅ Все данные успешно сброшены!\n\n"
        "Используй команду /start для повторной регистрации."
    )

@router.callback_query(F.data.startswith("cancel_"))
async def cancel_action(callback: CallbackQuery):
    """Отмена действия"""
    await callback.message.edit_text("❌ Действие отменено.")

@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery):
    """Возврат к настройкам"""
    await show_settings(callback.message)