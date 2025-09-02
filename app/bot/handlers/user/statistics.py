from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.filters import Command
from datetime import datetime, date

from ....core.services.prayer_service import PrayerService
from ....core.services.user_service import UserService
from ....core.services.calculation_service import CalculationService
from ....core.config import config, escape_markdown
from ...keyboards.user.statistics import get_statistics_keyboard

router = Router()
prayer_service = PrayerService()
user_service = UserService()
calc_service = CalculationService()

# =======
#  UTILS
# =======

async def _generate_statistics_text(user_id: int) -> tuple[str, InlineKeyboardMarkup]:
    """Генерация текста статистики для пользователя"""
    stats = await prayer_service.get_user_statistics(user_id)
    user = await user_service.get_or_create_user(user_id)
    
    # Получаем данные о постах
    fasting_missed = user.fasting_missed_days or 0
    fasting_completed = user.fasting_completed_days or 0
    fasting_remaining = max(0, fasting_missed - fasting_completed)
    
    # Если нет данных ни о намазах, ни о постах
    if stats['total_missed'] == 0 and fasting_missed == 0:
        return (
            "📊 *Твоя статистика:*\n\n"
            "📭 Данных пока нет\n\n"
            "• 🔢 Расчет намазов\n"
            "• 📿 Посты",
            None
        )
    
    # Формируем краткую статистику
    stats_text = "📊 *Твоя статистика*\n\n"
    
    # Намазы
    if stats['total_missed'] > 0:
        prayer_progress = (stats['total_completed'] / stats['total_missed']) * 100 if stats['total_missed'] > 0 else 0
        progress_bar = "▓" * int(prayer_progress / 10) + "░" * (10 - int(prayer_progress / 10))
        
        stats_text += (
            f"🕌 *Намазы:* {stats['total_completed']}/{stats['total_missed']}\n"
            f"📊 [{progress_bar}] {prayer_progress:.0f}%\n"
            f"⏳ Осталось: *{stats['total_remaining']}*\n\n"
        )
    
    # Посты
    if fasting_missed > 0:
        fasting_progress = (fasting_completed / fasting_missed) * 100 if fasting_missed > 0 else 0
        progress_bar = "▓" * int(fasting_progress / 10) + "░" * (10 - int(fasting_progress / 10))
        
        stats_text += (
            f"📿 *Посты:* {fasting_completed}/{fasting_missed} дней\n"
            f"📊 [{progress_bar}] {fasting_progress:.0f}%\n"
            f"⏳ Осталось: *{fasting_remaining}* дней\n\n"
        )
    
    # Общий прогресс и мотивация
    total_items = stats['total_missed'] + fasting_missed
    total_completed = stats['total_completed'] + fasting_completed
    
    if total_items > 0:
        overall_progress = (total_completed / total_items) * 100
        
        if overall_progress >= 80:
            motivation = "🎯 Отлично! Ты близок к завершению!"
        elif overall_progress >= 50:
            motivation = "💪 Хороший прогресс! Продолжай в том же духе!"
        elif overall_progress >= 25:
            motivation = "📈 Стабильное движение к цели!"
        else:
            motivation = "🌱 Каждый шаг важен. Не останавливайся!"
        
        stats_text += f"{motivation}\n"
    
    # Добавляем мотивационную фразу
    stats_text += "🤲 *Да поможет Аллах в восполнении!*"
    
    stats_text = escape_markdown(stats_text, ".!?()-[]")
    return stats_text, get_statistics_keyboard()


@router.message(F.text == "📊 Моя статистика")
@router.message(Command("stats"))
async def show_user_statistics(message: Message):
    """Показ статистики пользователя"""
    text, keyboard = await _generate_statistics_text(message.from_user.id)
    await message.answer(text, parse_mode="MarkdownV2", reply_markup=keyboard)


@router.callback_query(F.data == "show_history")
async def show_prayer_history(callback: CallbackQuery):
    """Показ истории изменений"""
    from ....core.database.repositories.prayer_history_repository import PrayerHistoryRepository
    history_repo = PrayerHistoryRepository()
    
    history = await history_repo.get_user_history(callback.from_user.id, limit=10)
    
    if not history:
        await callback.answer("📝 История изменений пуста", show_alert=True)
        return
    
    history_text = "📋 *Последние действия:*\n\n"
    
    for record in history:
        prayer_name = config.PRAYER_TYPES.get(record.prayer_type, record.prayer_type)
        action_emoji = {
            'add': '➕',
            'remove': '➖', 
            'set': '📝',
            'reset': '🔄',
            'add_missed': '⬆️'
        }.get(record.action, '•')
        
        history_text += (
            f"{action_emoji} {prayer_name} "
            f"({record.previous_value} → {record.new_value})\n"
        )
    history_text = escape_markdown(history_text, "().!?-[]")
    await callback.message.answer(history_text, parse_mode="MarkdownV2")

@router.callback_query(F.data == "detailed_breakdown")
async def show_detailed_breakdown(callback: CallbackQuery):
    """Детальная разбивка по намазам и постам"""
    prayers = await prayer_service.get_user_prayers(callback.from_user.id)
    user = await user_service.get_or_create_user(callback.from_user.id)
    
    breakdown_text = "🔍 *Детальная статистика*\n\n"
    
    # Намазы по типам
    if prayers:
        breakdown_text += "🕌 *Намазы по типам:*\n"
        
        # Обычные намазы
        regular_prayers = [p for p in prayers if not p.prayer_type.endswith('_safar')]
        if regular_prayers:
            for prayer in regular_prayers:
                if prayer.total_missed > 0:
                    prayer_name = config.PRAYER_TYPES[prayer.prayer_type]
                    progress = (prayer.completed / prayer.total_missed) * 100
                    breakdown_text += (
                        f"• {prayer_name}: {prayer.completed}/{prayer.total_missed} "
                        f"({progress:.0f}%)\n"
                    )
        
        # Сафар намазы
        safar_prayers = [p for p in prayers if p.prayer_type.endswith('_safar')]
        if safar_prayers and any(p.total_missed > 0 for p in safar_prayers):
            breakdown_text += "\n✈️ *Сафар намазы:*\n"
            for prayer in safar_prayers:
                if prayer.total_missed > 0:
                    prayer_name = config.PRAYER_TYPES[prayer.prayer_type]
                    progress = (prayer.completed / prayer.total_missed) * 100
                    breakdown_text += (
                        f"• {prayer_name}: {prayer.completed}/{prayer.total_missed} "
                        f"({progress:.0f}%)\n"
                    )
        
        breakdown_text += "\n"
    
    # Посты
    fasting_missed = user.fasting_missed_days or 0
    fasting_completed = user.fasting_completed_days or 0
    
    if fasting_missed > 0:
        fasting_progress = (fasting_completed / fasting_missed) * 100
        breakdown_text += (
            f"📿 *Посты Рамадана:*\n"
            f"• Восполнено: {fasting_completed}/{fasting_missed} дней ({fasting_progress:.0f}%)\n"
        )
        
        # if user.gender == 'female' and user.hayd_average_days:
        #     breakdown_text += f"• Учтен хайд: {user.hayd_average_days} дней/месяц\n"
        #     if user.childbirth_count > 0:
        #         breakdown_text += f"• Учтено родов: {user.childbirth_count}\n"
    
    breakdown_text = escape_markdown(breakdown_text, "().?![]-")
    await callback.message.answer(breakdown_text, parse_mode="MarkdownV2")

@router.callback_query(F.data == "refresh_stats")
async def refresh_statistics(callback: CallbackQuery):
    """Обновление статистики"""
    try:
        text, keyboard = await _generate_statistics_text(callback.from_user.id)
        await callback.message.edit_text(
            text, 
            parse_mode="MarkdownV2", 
            reply_markup=keyboard
        )
        await callback.answer("🔄 Статистика обновлена")
    except Exception as e:
        if "message is not modified" in str(e):
            await callback.answer("📊 Данные уже актуальны", show_alert=False)
        else:
            # Логируем другие ошибки
            print(f"Ошибка при обновлении статистики: {e}")
            await callback.answer("❌ Ошибка при обновлении", show_alert=True)