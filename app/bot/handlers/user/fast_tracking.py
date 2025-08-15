from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from ...keyboards.user.fast_tracking import (
    get_fast_tracking_keyboard,
    get_fast_adjustment_keyboard
)
from ....core.services.fast_service import FastService
from ....core.config import config

router = Router()
fast_service = FastService()

@router.message(F.text == "📿 Отметить посты")
async def show_fast_tracking(message: Message):
    """Показ интерфейса отслеживания постов"""
    fasts = await fast_service.get_user_fasts(message.from_user.id)
    
    if not fasts:
        await message.answer(
            "📊 У вас пока нет данных о постах.\n"
            "Сначала воспользуйтесь функцией '📿 Расчет постов'."
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
        "📿 **Отметить восполненные посты**\n\n"
        "Выберите пост для отметки:",
        reply_markup=get_fast_tracking_keyboard(fasts_to_show),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("fast_info_"))
async def show_fast_info(callback: CallbackQuery):
    """Показ информации о посте"""
    parts = callback.data.split("_")
    fast_type = parts[2]
    year = int(parts[3]) if len(parts) > 3 and parts[3] != "None" else None
    
    fast = await fast_service.fast_repo.get_fast(callback.from_user.id, fast_type, year)
    
    if not fast:
        await callback.answer("❌ Данные не найдены", show_alert=True)
        return
    
    if year:
        fast_name = f"Рамадан {year}"
    else:
        fast_name = config.FAST_TYPES.get(fast_type, fast_type)
    
    info_text = (
        f"📿 **{fast_name}**\n\n"
        f"📝 Всего пропущено: {fast.total_missed} дней\n"
        f"✅ Восполнено: {fast.completed} дней\n"
        f"⏳ Осталось: {fast.remaining} дней\n\n"
    )
    
    if fast.total_missed > 0:
        progress = (fast.completed / fast.total_missed) * 100
        info_text += f"📈 Прогресс: {progress:.1f}%"
    
    await callback.message.answer(
        info_text,
        reply_markup=get_fast_adjustment_keyboard(fast_type, year, fast.remaining),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("fast_dec_"))
async def decrease_fast(callback: CallbackQuery):
    """Уменьшение количества оставшихся постов (восполнение)"""
    parts = callback.data.split("_")
    fast_type = parts[2]
    year = int(parts[3]) if len(parts) > 3 and parts[3] != "None" else None
    
    fast = await fast_service.fast_repo.get_fast(callback.from_user.id, fast_type, year)
    if not fast or fast.remaining <= 0:
        await callback.answer("❌ Нет постов для восполнения", show_alert=True)
        return
    
    success = await fast_service.update_fast_count(
        callback.from_user.id, fast_type, 1, year
    )
    
    if success:
        updated_fast = await fast_service.fast_repo.get_fast(
            callback.from_user.id, fast_type, year
        )
        
        if year:
            fast_name = f"Рамадан {year}"
        else:
            fast_name = config.FAST_TYPES.get(fast_type, fast_type)
        
        await callback.answer(f"✅ {fast_name}: восполнен 1 день")
        
        # Обновляем клавиатуру
        fasts = await fast_service.get_user_fasts(callback.from_user.id)
        fasts_to_show = [f for f in fasts if f.remaining > 0]
        
        if fasts_to_show:
            await callback.message.edit_reply_markup(
                reply_markup=get_fast_tracking_keyboard(fasts_to_show)
            )
        else:
            await callback.message.edit_text(
                "🎉 Все посты восполнены! Машаа Ллах! 🤲"
            )
    else:
        await callback.answer("❌ Ошибка обновления", show_alert=True)

@router.callback_query(F.data.startswith("fast_inc_"))
async def increase_fast(callback: CallbackQuery):
    """Увеличение количества оставшихся постов"""
    parts = callback.data.split("_")
    fast_type = parts[2]
    year = int(parts[3]) if len(parts) > 3 and parts[3] != "None" else None
    
    success = await fast_service.increase_missed_fasts(
        callback.from_user.id, fast_type, 1, year
    )
    
    if success:
        if year:
            fast_name = f"Рамадан {year}"
        else:
            fast_name = config.FAST_TYPES.get(fast_type, fast_type)
        
        await callback.answer(f"➕ {fast_name}: добавлен 1 день")
        
        # Обновляем клавиатуру
        fasts = await fast_service.get_user_fasts(callback.from_user.id)
        fasts_to_show = [f for f in fasts if f.remaining > 0]
        
        await callback.message.edit_reply_markup(
            reply_markup=get_fast_tracking_keyboard(fasts_to_show)
        )
    else:
        await callback.answer("❌ Ошибка обновления", show_alert=True)

@router.callback_query(F.data.startswith("fast_adjust_"))
async def adjust_fast_count(callback: CallbackQuery):
    """Быстрая корректировка количества постов"""
    parts = callback.data.split("_")
    fast_type = parts[2]
    year_str = parts[3] if len(parts) > 3 else "None"
    amount = int(parts[4]) if len(parts) > 4 else 0
    
    year = int(year_str) if year_str != "None" else None
    
    if amount > 0:
        # Восполнение постов
        success = await fast_service.update_fast_count(
            callback.from_user.id, fast_type, amount, year
        )
    else:
        # Добавление пропущенных
        success = await fast_service.increase_missed_fasts(
            callback.from_user.id, fast_type, abs(amount), year
        )
    
    if success:
        updated_fast = await fast_service.fast_repo.get_fast(
            callback.from_user.id, fast_type, year
        )
        
        if year:
            fast_name = f"Рамадан {year}"
        else:
            fast_name = config.FAST_TYPES.get(fast_type, fast_type)
        
        action_text = "восполнено" if amount > 0 else "добавлено"
        result_text = (
            f"{'✅' if amount > 0 else '➕'} **{fast_name}:** {action_text} {abs(amount)} дней\n\n"
            f"📝 Всего пропущено: **{updated_fast.total_missed}**\n"
            f"✅ Восполнено: **{updated_fast.completed}**\n"
            f"⏳ Осталось: **{updated_fast.remaining}**"
        )
        
        await callback.message.edit_text(
            result_text,
            reply_markup=get_fast_adjustment_keyboard(fast_type, year, updated_fast.remaining),
            parse_mode="Markdown"
        )
    else:
        await callback.answer("❌ Ошибка обновления", show_alert=True)