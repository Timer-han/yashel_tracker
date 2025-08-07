from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from ...keyboards.user.prayer_tracking import (
    get_prayer_tracking_keyboard, 
    get_prayer_adjustment_keyboard,
    get_reset_confirmation_keyboard
)
from ....core.services.prayer_service import PrayerService
from ....core.config import config

router = Router()
prayer_service = PrayerService()

@router.message(F.text == "➕ Отметить намазы")
async def show_prayer_tracking(message: Message):
    """Показ интерфейса отслеживания намазов"""
    prayers = await prayer_service.get_user_prayers(message.from_user.id)
    
    if not prayers:
        await message.answer(
            "📊 У вас пока нет данных о намазах.\n"
            "Сначала воспользуйтесь функцией '🔢 Расчет намазов'."
        )
        return
    
    # Фильтруем только те намазы, которые нужно восполнить
    prayers_to_show = [p for p in prayers if p.remaining > 0]
    
    if not prayers_to_show:
        await message.answer(
            "🎉 Поздравляем! Все ваши намазы восполнены!\n"
            "Машаа Ллах! 🤲"
        )
        return
    
    await message.answer(
        "➕ **Отметить восполненные намазы**\n\n"
        "Используйте кнопки ➖ и ➕ для изменения количества восполненных намазов.\n"
        "Нажмите на название намаза для детальной настройки.",
        reply_markup=get_prayer_tracking_keyboard(prayers),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("prayer_inc_"))
async def increase_prayer(callback: CallbackQuery):
    """Увеличение количества восполненных намазов"""
    prayer_type = callback.data.split("_")[2]
    
    success = await prayer_service.update_prayer_count(
        callback.from_user.id, prayer_type, 1
    )
    
    if success:
        # Обновляем клавиатуру
        prayers = await prayer_service.get_user_prayers(callback.from_user.id)
        await callback.message.edit_reply_markup(
            reply_markup=get_prayer_tracking_keyboard(prayers)
        )
        
        prayer_name = config.PRAYER_TYPES[prayer_type]
        await callback.answer(f"✅ {prayer_name} +1", show_alert=False)
    else:
        await callback.answer("❌ Ошибка обновления", show_alert=True)

@router.callback_query(F.data.startswith("prayer_dec_"))
async def decrease_prayer(callback: CallbackQuery):
    """Уменьшение количества восполненных намазов"""
    prayer_type = callback.data.split("_")[2]
    
    # Проверяем, можно ли уменьшить
    prayer = await prayer_service.prayer_repo.get_prayer(callback.from_user.id, prayer_type)
    if not prayer or prayer.completed <= 0:
        await callback.answer("❌ Нельзя уменьшить ниже 0", show_alert=True)
        return
    
    success = await prayer_service.update_prayer_count(
        callback.from_user.id, prayer_type, -1
    )
    
    if success:
        # Обновляем клавиатуру
        prayers = await prayer_service.get_user_prayers(callback.from_user.id)
        await callback.message.edit_reply_markup(
            reply_markup=get_prayer_tracking_keyboard(prayers)
        )
        
        prayer_name = config.PRAYER_TYPES[prayer_type]
        await callback.answer(f"➖ {prayer_name} -1", show_alert=False)
    else:
        await callback.answer("❌ Ошибка обновления", show_alert=True)

@router.callback_query(F.data.startswith("prayer_info_"))
async def show_prayer_info(callback: CallbackQuery):
    """Показ детальной информации о намазе"""
    prayer_type = callback.data.split("_")[2]
    prayer = await prayer_service.prayer_repo.get_prayer(callback.from_user.id, prayer_type)
    
    if not prayer:
        await callback.answer("❌ Данные не найдены", show_alert=True)
        return
    
    prayer_name = config.PRAYER_TYPES[prayer_type]
    info_text = (
        f"🕌 **{prayer_name}**\n\n"
        f"📝 Всего пропущено: {prayer.total_missed}\n"
        f"✅ Восполнено: {prayer.completed}\n"
        f"⏳ Осталось: {prayer.remaining}\n\n"
    )
    
    if prayer.total_missed > 0:
        progress = (prayer.completed / prayer.total_missed) * 100
        info_text += f"📈 Прогресс: {progress:.1f}%"
    
    await callback.message.answer(
        info_text,
        reply_markup=get_prayer_adjustment_keyboard(prayer_type, prayer.remaining),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "show_stats")
async def show_stats_from_tracking(callback: CallbackQuery):
    """Показ статистики из интерфейса отслеживания"""
    stats = await prayer_service.get_user_statistics(callback.from_user.id)
    
    stats_text = (
        "📊 **Ваша статистика:**\n\n"
        f"📝 Всего пропущено: **{stats['total_missed']}**\n"
        f"✅ Восполнено: **{stats['total_completed']}**\n"
        f"⏳ Осталось: **{stats['total_remaining']}**\n\n"
    )
    
    if stats['total_completed'] > 0:
        progress = (stats['total_completed'] / stats['total_missed']) * 100
        stats_text += f"📈 Прогресс: **{progress:.1f}%**"
    
    await callback.answer()
    await callback.message.answer(stats_text, parse_mode="Markdown")

@router.callback_query(F.data == "reset_prayers")
async def confirm_reset_prayers(callback: CallbackQuery):
    """Подтверждение сброса всех намазов"""
    await callback.message.answer(
        "🔄 **Сброс всех данных**\n\n"
        "⚠️ Вы уверены, что хотите сбросить всю статистику восполнения намазов?\n"
        "Это действие нельзя отменить!",
        reply_markup=get_reset_confirmation_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "confirm_reset")
async def reset_prayers_confirmed(callback: CallbackQuery):
    """Подтвержденный сброс намазов"""
    success = await prayer_service.reset_user_prayers(callback.from_user.id)
    
    if success:
        await callback.message.edit_text(
            "✅ Статистика успешно сброшена.\n\n"
            "Воспользуйтесь функцией '🔢 Расчет намазов' для настройки новых данных."
        )
    else:
        await callback.message.edit_text("❌ Ошибка при сбросе данных.")

@router.callback_query(F.data == "cancel_reset")
async def cancel_reset_prayers(callback: CallbackQuery):
    """Отмена сброса намазов"""
    await callback.message.edit_text("❌ Сброс отменен.")
    await callback.answer()
