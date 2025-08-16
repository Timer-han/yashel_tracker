from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime

from ...keyboards.user.settings import get_settings_menu_keyboard, get_change_confirmation_keyboard
from ...keyboards.user.registration import get_gender_keyboard, get_gender_inline_keyboard
from ....core.services.user_service import UserService
from ....core.services.prayer_service import PrayerService
from ...states.settings import SettingsStates

router = Router()
user_service = UserService()
prayer_service = PrayerService()

@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    """Показ настроек"""
    user = await user_service.get_or_create_user(message.from_user.id)
    
    settings_text = (
        "⚙️ **Настройки профиля**\n\n"
        # f"👤 Имя: {user.username or 'Не указано'}\n"
        f"👤 Пол: {'Мужской' if user.gender == 'male' else 'Женский' if user.gender == 'female' else 'Не указан'}\n"
        f"📅 Дата рождения: {user.birth_date.strftime('%d.%m.%Y') if user.birth_date else 'Не указана'}\n"
        f"🏙️ Город: {user.city or 'Не указан'}\n\n"
        "Выберите, что хотите изменить:"
    )
    
    await message.answer(
        settings_text,
        reply_markup=get_settings_menu_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "change_gender")
async def change_gender(callback: CallbackQuery, state: FSMContext):
    """Изменение пола"""
    await callback.message.edit_text(
        "👤 Выберите ваш пол:",
        reply_markup=get_gender_inline_keyboard()
    )
    await state.set_state(SettingsStates.waiting_for_gender)

@router.callback_query(F.data == "change_birth_date")
async def change_birth_date(callback: CallbackQuery, state: FSMContext):
    """Изменение даты рождения"""
    await callback.message.edit_text(
        "📅 Введите новую дату рождения в формате ДД.ММ.ГГГГ\n"
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
            "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ\n"
            "Например: 15.03.1990"
        )
        return
    
    await state.clear()

@router.callback_query(F.data == "change_city")
async def change_city(callback: CallbackQuery, state: FSMContext):
    """Изменение города"""
    await callback.message.edit_text("🏙️ Введите новый город:")
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

@router.callback_query(F.data == "export_data")
async def export_data(callback: CallbackQuery):
    """Экспорт данных пользователя"""
    user = await user_service.get_or_create_user(callback.from_user.id)
    stats = await prayer_service.get_user_statistics(callback.from_user.id)
    
    export_text = (
        f"📊 **Экспорт данных пользователя**\n\n"
        f"**Профиль:**\n"
        f"• Имя: {user.full_name or 'Не указано'}\n"
        f"• Пол: {'Мужской' if user.gender == 'male' else 'Женский' if user.gender == 'female' else 'Не указан'}\n"
        f"• Дата рождения: {user.birth_date.strftime('%d.%m.%Y') if user.birth_date else 'Не указана'}\n"
        f"• Город: {user.city or 'Не указан'}\n"
        f"• Дата регистрации: {user.created_at.strftime('%d.%m.%Y %H:%M') if hasattr(user, 'created_at') else 'Неизвестно'}\n\n"
        f"**Статистика намазов:**\n"
        f"• Всего пропущено: {stats['total_missed']}\n"
        f"• Восполнено: {stats['total_completed']}\n"
        f"• Осталось: {stats['total_remaining']}\n\n"
        f"**Детали по намазам:**\n"
    )
    
    for prayer_name, data in stats['prayers'].items():
        if data['total'] > 0:
            export_text += f"• {prayer_name}: {data['completed']}/{data['total']}\n"
    
    await callback.message.edit_text(export_text, parse_mode="Markdown")

@router.callback_query(F.data == "reset_all_data")
async def confirm_reset_all_data(callback: CallbackQuery):
    """Подтверждение полного сброса"""
    await callback.message.edit_text(
        "🔄 **Полный сброс данных**\n\n"
        "⚠️ **ВНИМАНИЕ!** Это действие:\n"
        "• Удалит всю статистику намазов\n"
        "• Сбросит настройки профиля\n"
        "• Потребует повторной регистрации\n\n"
        "Это действие **НЕОБРАТИМО**!\n\n"
        "Вы действительно хотите продолжить?",
        reply_markup=get_change_confirmation_keyboard("reset_all"),
        parse_mode="Markdown"
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
        full_name=None,
        gender=None,
        birth_date=None,
        city=None
    )
    
    await callback.message.edit_text(
        "✅ Все данные успешно сброшены!\n\n"
        "Используйте команду /start для повторной регистрации."
    )

@router.callback_query(F.data.startswith("cancel_"))
async def cancel_action(callback: CallbackQuery):
    """Отмена действия"""
    await callback.message.edit_text("❌ Действие отменено.")

@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery):
    """Возврат к настройкам"""
    await show_settings(callback.message)