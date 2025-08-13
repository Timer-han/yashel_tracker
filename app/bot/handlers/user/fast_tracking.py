from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from ...keyboards.user.fast_tracking import get_fast_tracking_keyboard, get_fast_adjustment_keyboard
from ....core.services.fast_service import FastService
from ....core.config import config

router = Router()
fast_service = FastService()

@router.message(F.text == "🥗 Отметить посты")
async def show_fast_tracking(message: Message):
    """Показ интерфейса отслеживания постов"""
    fasts = await fast_service.get_user_fasts(message.from_user.id)
    
    if not fasts:
        await message.answer(
            "📊 У вас пока нет данных о постах.\n"
            "Сначала воспользуйтесь функцией '🥗 Расчет постов'."
        )
        return
    
    # Фильтруем только те посты, которые нужно восполнить
    fasts_to_show = [f for f in fasts if f.remaining > 0]
    
    if not fasts_to_show:
        await message.answer(
            "🎉 Поздравляем! Все ваши посты восполнены!\n"
            "Машаа Ллах! 🤲"
        )
        return
    
    await message.answer(
        "🥗 **Отметить восполненные посты**",
        reply_markup=get_fast_tracking_keyboard(fasts),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("fast_inc_"))
async def increase_fast(callback: CallbackQuery):
    """Увеличение количества ОСТАВШИХСЯ постов"""
    fast_type = callback.data.split("_")[2]
    
    # Проверяем текущее состояние
    fast = await fast_service.fast_repo.get_fast(callback.from_user.id, fast_type)
    
    if not fast:
        await callback.answer("❌ Данные не найдены", show_alert=True)
        return
    
    # Если восполненных <= 0, добавляем к пропущенным
    if fast.completed <= 0:
        success = await fast_service.increase_missed_fasts(
            callback.from_user.id, fast_type, 1
        )
        
        if success:
            updated_fast = await fast_service.fast_repo.get_fast(callback.from_user.id, fast_type)
            await send_fast_action_message_and_update_menu(callback, fast_type, "increase_missed", updated_fast)
        else:
            await callback.answer("❌ Ошибка обновления", show_alert=True)
    else:
        # Уменьшаем восполненные (увеличиваем оставшиеся)
        success = await fast_service.update_fast_count(
            callback.from_user.id, fast_type, -1
        )
        
        if success:
            updated_fast = await fast_service.fast_repo.get_fast(callback.from_user.id, fast_type)
            await send_fast_action_message_and_update_menu(callback, fast_type, "decrease_completed", updated_fast)
        else:
            await callback.answer("❌ Ошибка обновления", show_alert=True)

@router.callback_query(F.data.startswith("fast_dec_"))
async def decrease_fast(callback: CallbackQuery):
    """Уменьшение количества ОСТАВШИХСЯ постов (увеличение восполненных)"""
    fast_type = callback.data.split("_")[2]
    
    # Проверяем, есть ли что восполнять
    fast = await fast_service.fast_repo.get_fast(callback.from_user.id, fast_type)
    if not fast or fast.remaining <= 0:
        await callback.answer("❌ Нет постов для восполнения", show_alert=True)
        return
    
    success = await fast_service.update_fast_count(
        callback.from_user.id, fast_type, 1
    )
    
    if success:
        updated_fast = await fast_service.fast_repo.get_fast(callback.from_user.id, fast_type)
        await send_fast_action_message_and_update_menu(callback, fast_type, "increase_completed", updated_fast)
    else:
        await callback.answer("❌ Ошибка обновления", show_alert=True)

async def send_fast_action_message_and_update_menu(callback_query, fast_type: str, action_type: str, fast_data):
    """Отправка уведомления о действии с постами и обновление меню"""
    fast_name = config.FAST_TYPES[fast_type]
    
    # Формируем текст уведомления в зависимости от действия
    if action_type == "increase_completed":
        action_text = "восполнен 1 пост"
        action_emoji = "✅"
    elif action_type == "decrease_completed":
        action_text = "убран 1 пост из восполненных"
        action_emoji = "➖"
    elif action_type == "increase_missed":
        action_text = "добавлен 1 пропущенный пост"
        action_emoji = "➕"
    else:
        action_text = "изменен"
        action_emoji = "🔄"
    
    # Определяем progress bar
    if fast_data.total_missed > 0:
        progress = (fast_data.completed / fast_data.total_missed) * 100
        progress_bar = "▓" * int(progress / 10) + "░" * (10 - int(progress / 10))
        progress_text = f"\n📊 [{progress_bar}] {progress:.1f}%"
    else:
        progress_text = ""
    
    notification_text = (
        f"{action_emoji} **{fast_name}:** {action_text}\n\n"
        f"📝 Всего: **{fast_data.total_missed}** \n "
        f"✅ Восполнено: **{fast_data.completed}** \n "
        f"⏳ Осталось: **{fast_data.remaining}**"
        f"{progress_text}"
    )
    
    # Мотивационное сообщение
    if fast_data.remaining == 0:
        notification_text += f"\n\n🎉 **Машаа Ллах!** Все {fast_name} восполнены!"
    
    # 1. Редактируем текущее сообщение в уведомление
    await callback_query.message.edit_text(notification_text, parse_mode="Markdown")
    
    # 2. Отправляем новое меню
    fasts = await fast_service.get_user_fasts(callback_query.from_user.id)
    
    await callback_query.message.answer(
        "🥗 **Отметить восполненные посты**",
        reply_markup=get_fast_tracking_keyboard(fasts),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("fast_info_"))
async def show_fast_info(callback: CallbackQuery):
    """Показ детальной информации о посте"""
    fast_type = callback.data.split("_")[2]
    
    fast = await fast_service.fast_repo.get_fast(callback.from_user.id, fast_type)
    
    if not fast:
        await callback.answer("❌ Данные не найдены", show_alert=True)
        return
    
    fast_name = config.FAST_TYPES[fast_type]
    info_text = (
        f"🥗 **{fast_name}**\n\n"
        f"📝 Всего пропущено: {fast.total_missed}\n"
        f"✅ Восполнено: {fast.completed}\n"
        f"⏳ Осталось: {fast.remaining}\n\n"
    )
    
    if fast.total_missed > 0:
        progress = (fast.completed / fast.total_missed) * 100
        info_text += f"📈 Прогресс: {progress:.1f}%"
    
    await callback.message.answer(
        info_text,
        reply_markup=get_fast_adjustment_keyboard(fast_type, fast.remaining),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "show_fast_stats")
async def show_fast_stats_from_tracking(callback: CallbackQuery):
    """Показ статистики постов из интерфейса отслеживания"""
    stats = await fast_service.get_user_fast_statistics(callback.from_user.id)
    
    stats_text = (
        "📊 **Ваша статистика постов:**\n\n"
        f"📝 Всего пропущено: **{stats['total_missed']}**\n"
        f"✅ Восполнено: **{stats['total_completed']}**\n"
        f"⏳ Осталось: **{stats['total_remaining']}**\n\n"
    )
    
    if stats['total_completed'] > 0 and stats['total_missed'] > 0:
        progress = (stats['total_completed'] / stats['total_missed']) * 100
        stats_text += f"📈 Прогресс: **{progress:.1f}%**"
    
    await callback.answer()
    await callback.message.answer(stats_text, parse_mode="Markdown")

@router.callback_query(F.data.startswith("fast_adjust_"))
async def fast_adjust_fast(callback: CallbackQuery):
    """Быстрое изменение количества постов"""
    parts = callback.data.split("_")
    fast_type = parts[2]
    amount = int(parts[3])
    
    fast = await fast_service.fast_repo.get_fast(callback.from_user.id, fast_type)
    if not fast:
        await callback.answer("❌ Данные не найдены", show_alert=True)
        return
    
    success = False
    action_type = ""
    
    if amount > 0:
        # Увеличиваем оставшиеся (либо уменьшаем восполненные, либо добавляем к пропущенным)
        if fast.completed >= amount:
            # Уменьшаем восполненные
            success = await fast_service.update_fast_count(
                callback.from_user.id, fast_type, -amount
            )
            action_type = "decrease_completed"
        else:
            # Добавляем к пропущенным
            success = await fast_service.increase_missed_fasts(
                callback.from_user.id, fast_type, amount
            )
            action_type = "increase_missed"
    else:
        # Уменьшаем оставшиеся (увеличиваем восполненные)
        if fast.remaining >= abs(amount):
            success = await fast_service.update_fast_count(
                callback.from_user.id, fast_type, abs(amount)
            )
            action_type = "increase_completed"
        else:
            await callback.answer(f"❌ Недостаточно постов для восполнения (доступно: {fast.remaining})", show_alert=True)
            return
    
    if success:
        updated_fast = await fast_service.fast_repo.get_fast(callback.from_user.id, fast_type)
        
        # Показываем результат изменения
        fast_name = config.FAST_TYPES[fast_type]
        
        if amount > 0:
            if action_type == "decrease_completed":
                action_text = f"убрано {amount} из восполненных"
                action_emoji = "➖"
            else:
                action_text = f"добавлено {amount} пропущенных"
                action_emoji = "➕"
        else:
            action_text = f"восполнено {abs(amount)} постов"
            action_emoji = "✅"
        
        result_text = (
            f"{action_emoji} **{fast_name}:** {action_text}\n\n"
            f"📝 Всего пропущено: **{updated_fast.total_missed}**\n"
            f"✅ Восполнено: **{updated_fast.completed}**\n"
            f"⏳ Осталось: **{updated_fast.remaining}**"
        )
        
        # Обновляем клавиатуру с новыми данными
        await callback.message.edit_text(
            result_text,
            reply_markup=get_fast_adjustment_keyboard(fast_type, updated_fast.remaining),
            parse_mode="Markdown"
        )
        
        await callback.answer()
    else:
        await callback.answer("❌ Ошибка обновления", show_alert=True)

@router.callback_query(F.data == "fast_adjustment_done")
async def finish_fast_adjustment(callback: CallbackQuery):
    """Завершение точной настройки поста"""
    fasts = await fast_service.get_user_fasts(callback.from_user.id)
    
    await callback.message.edit_text(
        "🥗 **Отметить восполненные посты**",
        reply_markup=get_fast_tracking_keyboard(fasts),
        parse_mode="Markdown"
    )