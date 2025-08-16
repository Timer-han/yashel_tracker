import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from ...keyboards.user.prayer_tracking import (
    get_prayer_tracking_keyboard, 
    get_prayer_adjustment_keyboard,
    get_reset_confirmation_keyboard,
    get_prayer_category_keyboard,
    get_compact_prayer_tracking_keyboard
)
from ....core.services.prayer_service import PrayerService
from ....core.config import config


logger = logging.getLogger(__name__)
router = Router()
prayer_service = PrayerService()

@router.message(F.text == "➕ Отметить намазы")
async def show_prayer_tracking(message: Message):
    """Показ интерфейса отслеживания намазов"""
    prayers = await prayer_service.get_user_prayers(message.from_user.id)
    
    if not prayers:
        await message.answer(
            "Данные о намазах не введены 🥲\n"
            "Сначала воспользуйся функцией '🔢 Расчет намазов'"
        )
        return
    
    # Фильтруем только те намазы, которые нужно восполнить
    prayers_to_show = [p for p in prayers if p.remaining > 0]
    
    if not prayers_to_show:
        await message.answer(
            "🎉 Поздравляем! Все твои намазы восполнены!\n"
            "Ты сделал огромный вклад в Ахират. Пусть Всевышний примет и будет тобой доволен!"
        )
        return
    
    await message.answer(
        "➕ **Отметить восполненные намазы**\n\n"
        "Выбери категорию намазов:",
        reply_markup=get_prayer_category_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("prayer_inc_"))
async def increase_prayer(callback: CallbackQuery):
    """Увеличение количества ОСТАВШИХСЯ намазов"""
    prayer_type = callback.data.split("_")[2]
    if len(callback.data.split("_")) > 3:
        prayer_type += "_" + callback.data.split("_")[3]
    
    # Проверяем текущее состояние
    prayer = await prayer_service.prayer_repo.get_prayer(callback.from_user.id, prayer_type)
    
    if not prayer:
        await callback.answer("❌ Данные не найдены", show_alert=True)
        return
    
    # Если восполненных <= 0, добавляем к пропущенным
    if prayer.completed <= 0:
        success = await prayer_service.increase_missed_prayers(
            callback.from_user.id, prayer_type, 1
        )
        
        if success:
            updated_prayer = await prayer_service.prayer_repo.get_prayer(callback.from_user.id, prayer_type)
            await send_action_message_and_update_menu(callback, prayer_type, "increase_missed", updated_prayer)
        else:
            await callback.answer("❌ Ошибка обновления", show_alert=True)
    else:
        # Уменьшаем восполненные (увеличиваем оставшиеся)
        success = await prayer_service.update_prayer_count(
            callback.from_user.id, prayer_type, -1
        )
        
        if success:
            updated_prayer = await prayer_service.prayer_repo.get_prayer(callback.from_user.id, prayer_type)
            await send_action_message_and_update_menu(callback, prayer_type, "decrease_completed", updated_prayer)
        else:
            await callback.answer("❌ Ошибка обновления", show_alert=True)

@router.callback_query(F.data.startswith("prayer_dec_"))
async def decrease_prayer(callback: CallbackQuery):
    """Уменьшение количества ОСТАВШИХСЯ намазов (увеличение восполненных)"""
    prayer_type = callback.data.split("_")[2]
    if len(callback.data.split("_")) > 3:
        prayer_type += "_" + callback.data.split("_")[3]
    
    # Проверяем, есть ли что восполнять
    prayer = await prayer_service.prayer_repo.get_prayer(callback.from_user.id, prayer_type)
    if not prayer or prayer.remaining <= 0:
        await callback.answer("❌ Нет намазов для восполнения", show_alert=True)
        return
    
    success = await prayer_service.update_prayer_count(
        callback.from_user.id, prayer_type, 1
    )
    
    if success:
        updated_prayer = await prayer_service.prayer_repo.get_prayer(callback.from_user.id, prayer_type)
        await send_action_message_and_update_menu(callback, prayer_type, "increase_completed", updated_prayer)
    else:
        await callback.answer("❌ Ошибка обновления", show_alert=True)

async def send_action_message_and_update_menu(callback_query, prayer_type: str, action_type: str, prayer_data):
    """Отправка уведомления о действии и обновление компактного меню"""
    prayer_name = config.PRAYER_TYPES[prayer_type]
    
    # Формируем текст уведомления в зависимости от действия
    if action_type == "increase_completed":
        action_text = "восполнен 1 намаз"
        action_emoji = "✅"
    elif action_type == "decrease_completed":
        action_text = "убран 1 намаз из восполненных"
        action_emoji = "➖"
    elif action_type == "increase_missed":
        action_text = "добавлен 1 пропущенный намаз"
        action_emoji = "➕"
    else:
        action_text = "изменен"
        action_emoji = "🔄"
    
    # Определяем progress bar
    if prayer_data.total_missed > 0:
        progress = (prayer_data.completed / prayer_data.total_missed) * 100
        progress_bar = "▓" * int(progress / 10) + "░" * (10 - int(progress / 10))
        progress_text = f"\n📊 [{progress_bar}] {progress:.1f}%"
    else:
        progress_text = ""
    
    notification_text = (
        f"{action_emoji} **{prayer_name}:** {action_text}\n\n"
        f"📝 Всего: **{prayer_data.total_missed}** \n "
        f"✅ Восполнено: **{prayer_data.completed}** \n "
        f"⏳ Осталось: **{prayer_data.remaining}**"
        f"{progress_text}"
    )
    
    # Мотивационное сообщение
    if prayer_data.remaining == 0:
        notification_text += f"\n\n🎉 **Машаа Ллах!** Все {prayer_name} восполнены!"
    
    # 1. Редактируем текущее сообщение в уведомление
    await callback_query.message.edit_text(notification_text, parse_mode="Markdown")
    
    # 2. Определяем категорию и отправляем новое меню
    prayers = await prayer_service.get_user_prayers(callback_query.from_user.id)
    
    # Определяем категорию по типу намаза
    if prayer_type.endswith('_safar'):
        category = "safar"
        category_name = "✈️ **Сафар намазы**"
    else:
        category = "regular"
        category_name = "🕌 **Обычные намазы**"
    
    await callback_query.message.answer(
        f"{category_name}\n\n"
        "➖ - восполнить намаз (уменьшить оставшиеся)\n"
        "➕ - добавить пропущенный (увеличить оставшиеся)",
        reply_markup=get_compact_prayer_tracking_keyboard(prayers, category),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("prayer_info_"))
async def show_prayer_info(callback: CallbackQuery):
    """Показ детальной информации о намазе"""
    # Парсим prayer_type с учетом сафар намазов
    parts = callback.data.split("_")
    if len(parts) == 4 and parts[3] == "safar":  # prayer_info_zuhr_safar
        prayer_type = f"{parts[2]}_{parts[3]}"
    else:  # prayer_info_fajr
        prayer_type = parts[2]
    
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
        "🔄 **Полный сброс данных**\n"
        "⚠️ **ВНИМАНИЕ!** Это действие:\n"
        "• Удалит всю статистику намазов\n"
        "• Сбросит настройки профиля\n"
        "• Потребует повторной регистрации\n\n"
        "Это действие **НЕОБРАТИМО**!\n"
        "Ты действительно хочешь продолжить?",
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
            "Воспользуйся функцией '🔢 Расчет намазов' для настройки новых данных."
        )
    else:
        await callback.message.edit_text("❌ Ошибка при сбросе данных.")

@router.callback_query(F.data == "cancel_reset")
async def cancel_reset_prayers(callback: CallbackQuery):
    """Отмена сброса намазов"""
    await callback.message.edit_text("❌ Сброс отменен.")
    await callback.answer()

@router.callback_query(F.data == "safar_divider")
async def safar_divider_handler(callback: CallbackQuery):
    """Обработчик разделителя сафар намазов"""
    await callback.answer("✈️ Это сафар намазы - сокращенные намазы для путешествий", show_alert=True)


@router.callback_query(F.data.startswith("fast_adjust_"))
async def fast_adjust_prayer(callback: CallbackQuery):
    """Быстрое изменение количества намазов"""
    parts = callback.data.split("_")

    logger.critical(callback.data)
    
    # Обрабатываем как сафар, так и обычные намазы
    if len(parts) == 4:  # fast_adjust_fajr_10
        prayer_type = parts[2]
        amount = int(parts[3])
    elif len(parts) == 5:  # fast_adjust_zuhr_safar_10
        prayer_type = f"{parts[2]}_{parts[3]}"  # zuhr_safar
        amount = int(parts[4])
    else:
        await callback.answer("❌ Ошибка данных", show_alert=True)
        return
    
    logger.critical(prayer_type)
    
    prayer = await prayer_service.prayer_repo.get_prayer(callback.from_user.id, prayer_type)
    if not prayer:
        await callback.answer("❌ Данные не найдены", show_alert=True)
        return
    
    success = False
    action_type = ""
    
    if amount > 0:
        # Увеличиваем оставшиеся (либо уменьшаем восполненные, либо добавляем к пропущенным)
        if prayer.completed >= amount:
            # Уменьшаем восполненные
            success = await prayer_service.update_prayer_count(
                callback.from_user.id, prayer_type, -amount
            )
            action_type = "decrease_completed"
        else:
            # Добавляем к пропущенным
            success = await prayer_service.increase_missed_prayers(
                callback.from_user.id, prayer_type, amount
            )
            action_type = "increase_missed"
    else:
        # Уменьшаем оставшиеся (увеличиваем восполненные)
        if prayer.remaining >= abs(amount):
            success = await prayer_service.update_prayer_count(
                callback.from_user.id, prayer_type, abs(amount)
            )
            action_type = "increase_completed"
        else:
            await callback.answer(f"❌ Недостаточно намазов для восполнения (доступно: {prayer.remaining})", show_alert=True)
            return
    
    if success:
        updated_prayer = await prayer_service.prayer_repo.get_prayer(callback.from_user.id, prayer_type)
        
        # Показываем результат изменения
        prayer_name = config.PRAYER_TYPES[prayer_type]
        
        if amount > 0:
            if action_type == "decrease_completed":
                action_text = f"убрано {amount} из восполненных"
                action_emoji = "➖"
            else:
                action_text = f"добавлено {amount} пропущенных"
                action_emoji = "➕"
        else:
            action_text = f"восполнено {abs(amount)} намазов"
            action_emoji = "✅"
        
        result_text = (
            f"{action_emoji} **{prayer_name}:** {action_text}\n\n"
            f"📝 Всего пропущено: **{updated_prayer.total_missed}**\n"
            f"✅ Восполнено: **{updated_prayer.completed}**\n"
            f"⏳ Осталось: **{updated_prayer.remaining}**"
        )
        
        # Обновляем клавиатуру с новыми данными
        await callback.message.edit_text(
            result_text,
            reply_markup=get_prayer_adjustment_keyboard(prayer_type, updated_prayer.remaining),
            parse_mode="Markdown"
        )
        
        await callback.answer()
    else:
        await callback.answer("❌ Ошибка обновления", show_alert=True)


@router.callback_query(F.data == "adjustment_done")
async def finish_adjustment(callback: CallbackQuery):
    """Завершение точной настройки намаза"""
    await callback.message.edit_text(
        "➕ **Отметить восполненные намазы**\n\n"
        "Выбери категорию намазов:",
        reply_markup=get_prayer_category_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "category_regular")
async def show_regular_prayers(callback: CallbackQuery):
    """Показ обычных намазов"""
    prayers = await prayer_service.get_user_prayers(callback.from_user.id)
    regular_order = ['fajr', 'zuhr', 'asr', 'maghrib', 'isha', 'witr']
    
    # Проверяем, есть ли обычные намазы для восполнения
    has_regular = any(p for p in prayers if p.prayer_type in regular_order and p.remaining > 0)
    
    if not has_regular:
        await callback.message.edit_text(
            "✅ Все обычные намазы восполнены!\n\n"
            "Выбери другую категорию:",
            reply_markup=get_prayer_category_keyboard()
        )
        return
    
    await callback.message.edit_text(
        "🕌 **Обычные намазы**\n\n"
        "➖ - восполнить намаз (уменьшить оставшиеся)\n"
        "➕ - добавить пропущенный (увеличить оставшиеся)",
        reply_markup=get_compact_prayer_tracking_keyboard(prayers, "regular"),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "category_safar")
async def show_safar_prayers(callback: CallbackQuery):
    """Показ сафар намазов"""
    prayers = await prayer_service.get_user_prayers(callback.from_user.id)
    safar_order = ['zuhr_safar', 'asr_safar', 'isha_safar']
    
    # Проверяем, есть ли сафар намазы для восполнения
    has_safar = any(p for p in prayers if p.prayer_type in safar_order and p.remaining > 0)
    
    if not has_safar:
        await callback.message.edit_text(
            "✅ Все сафар намазы восполнены!\n\nВыбери другую категорию:",
            reply_markup=get_prayer_category_keyboard()
        )
        return
    
    await callback.message.edit_text(
        "✈️ **Сафар намазы**\n\n"
        "➖ - восполнить намаз (уменьшить оставшиеся)\n"
        "➕ - добавить пропущенный (увеличить оставшиеся)",
        reply_markup=get_compact_prayer_tracking_keyboard(prayers, "safar"),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "switch_to_safar")
async def switch_to_safar(callback: CallbackQuery):
    """Переключение на сафар намазы"""
    await show_safar_prayers(callback)

@router.callback_query(F.data == "switch_to_regular")
async def switch_to_regular(callback: CallbackQuery):
    """Переключение на обычные намазы"""
    await show_regular_prayers(callback)

@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    """Возврат к выбору категорий"""
    await callback.message.edit_text(
        "➕ **Отметить восполненные намазы**\n\n"
        "Выбери категорию намазов:",
        reply_markup=get_prayer_category_keyboard(),
        parse_mode="Markdown"
    )