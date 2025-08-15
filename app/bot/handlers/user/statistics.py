from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from datetime import datetime, date

from ....core.services.prayer_service import PrayerService
from ....core.services.user_service import UserService
from ....core.services.calculation_service import CalculationService
from ....core.config import config
from ...keyboards.user.statistics import get_statistics_keyboard

router = Router()
prayer_service = PrayerService()
user_service = UserService()
calc_service = CalculationService()

@router.message(F.text == "📊 Моя статистика")
@router.message(Command("stats"))
async def show_user_statistics(message: Message):
    """Показ статистики пользователя"""
    stats = await prayer_service.get_user_statistics(message.from_user.id)
    user = await user_service.get_or_create_user(message.from_user.id)
    
    if stats['total_missed'] == 0:
        await message.answer(
            "📊 **Ваша статистика:**\n\n"
            "У вас пока нет данных о намазах.\n"
            "Используйте 🔢 Расчет намазов для настройки.",
            parse_mode="Markdown"
        )
        return
    
    # Основная статистика
    stats_text = (
        "📊 **Подробная статистика восполнения намазов:**\n\n"
        f"👤 Пользователь: {user.full_name or user.first_name}\n"
        f"📅 Возраст: {calc_service.calculate_age(user.birth_date) if user.birth_date else 'Не указан'} лет\n"
        f"🏙️ Город: {user.city or 'Не указан'}\n\n"
        f"📝 **Всего пропущено: {stats['total_missed']}**\n"
        f"✅ **Восполнено: {stats['total_completed']}**\n"
        f"⏳ **Осталось: {stats['total_remaining']}**\n\n"
    )
    
    # Прогресс
    if stats['total_missed'] > 0:
        progress = (stats['total_completed'] / stats['total_missed']) * 100
        stats_text += f"📈 **Общий прогресс: {progress:.1f}%**\n\n"
        
        # Прогресс-бар
        progress_bar = "▓" * int(progress / 10) + "░" * (10 - int(progress / 10))
        stats_text += f"[{progress_bar}] {progress:.1f}%\n\n"
    
    # Расчет среднего в день
    if stats['total_completed'] > 0:
        # Приблизительно считаем, что пользователь восполняет намазы последние 30 дней
        avg_per_day = stats['total_completed'] / 30 if stats['total_completed'] > 30 else stats['total_completed']
        stats_text += f"📊 Среднее восполнение: ~{avg_per_day:.1f} намазов/день\n\n"
        
        # Прогноз завершения
        if stats['total_remaining'] > 0 and avg_per_day > 0:
            days_to_complete = stats['total_remaining'] / avg_per_day
            if days_to_complete < 365:
                stats_text += f"⏰ Прогноз завершения: ~{days_to_complete:.0f} дней\n\n"
    
    stats_text += "**📋 Детализация по намазам:**\n\n"
    
    # Группировка намазов
    regular_prayers = {}
    safar_prayers = {}
    
    for prayer_name, data in stats['prayers'].items():
        if data['total'] > 0:
            if 'сафар' in prayer_name.lower():
                safar_prayers[prayer_name] = data
            else:
                regular_prayers[prayer_name] = data
    
    # Обычные намазы
    if regular_prayers:
        stats_text += "🕌 **Обычные намазы:**\n"
        for prayer_name, data in regular_prayers.items():
            progress_pct = (data['completed'] / data['total']) * 100 if data['total'] > 0 else 0
            stats_text += (
                f"• **{prayer_name}:** {data['completed']}/{data['total']} "
                f"({progress_pct:.1f}% - осталось {data['remaining']})\n"
            )
        stats_text += "\n"
    
    # Сафар намазы
    if safar_prayers:
        stats_text += "✈️ **Сафар намазы:**\n"
        for prayer_name, data in safar_prayers.items():
            progress_pct = (data['completed'] / data['total']) * 100 if data['total'] > 0 else 0
            stats_text += (
                f"• **{prayer_name}:** {data['completed']}/{data['total']} "
                f"({progress_pct:.1f}% - осталось {data['remaining']})\n"
            )
        stats_text += "\n"
    
    # Мотивационное сообщение
    if stats['total_remaining'] > 0:
        if progress >= 80:
            stats_text += "🎯 Вы почти у цели! Не останавливайтесь!"
        elif progress >= 50:
            stats_text += "💪 Отличный прогресс! Продолжайте в том же духе!"
        elif progress >= 25:
            stats_text += "📈 Хорошее начало! Держите темп!"
        else:
            stats_text += "🌱 Каждый намаз приближает к цели. Начните с малого!"
        stats_text += "\n\n🤲 Да поможет вам Аллах в восполнении намазов!"
    else:
        stats_text += "🎉 **Машаа Ллах! Все намазы восполнены!**\n🤲 Да примет Аллах ваши усилия!"
    
    await message.answer(
        stats_text, 
        parse_mode="Markdown",
        reply_markup=get_statistics_keyboard()
    )

@router.callback_query(F.data == "show_history")
async def show_prayer_history(callback: CallbackQuery):
    """Показ истории изменений"""
    from ....core.database.repositories.prayer_history_repository import PrayerHistoryRepository
    history_repo = PrayerHistoryRepository()
    
    history = await history_repo.get_user_history(callback.from_user.id, limit=10)
    
    if not history:
        await callback.answer("📝 История изменений пуста", show_alert=True)
        return
    
    history_text = "📋 **Последние 10 действий:**\n\n"
    
    for record in history:
        prayer_name = config.PRAYER_TYPES.get(record.prayer_type, record.prayer_type)
        action_text = {
            'add': '➕ Добавлено',
            'remove': '➖ Убрано', 
            'set': '📝 Установлено',
            'reset': '🔄 Сброс'
        }.get(record.action, record.action)
        
        history_text += (
            f"• {action_text}: {prayer_name} ({record.amount})\n"
            f"  {record.previous_value} → {record.new_value}\n"
            f"  📅 {record.created_at.strftime('%d.%m %H:%M') if hasattr(record, 'created_at') else 'Недавно'}\n\n"
        )
    
    await callback.message.answer(history_text, parse_mode="Markdown")

@router.callback_query(F.data == "detailed_breakdown")
async def show_detailed_breakdown(callback: CallbackQuery):
    """Детальная разбивка по намазам"""
    prayers = await prayer_service.get_user_prayers(callback.from_user.id)
    
    if not prayers:
        await callback.answer("📊 Нет данных для анализа", show_alert=True)
        return
    
    breakdown_text = "🔍 **Детальный анализ по намазам:**\n\n"
    
    for prayer in prayers:
        if prayer.total_missed > 0:
            prayer_name = config.PRAYER_TYPES[prayer.prayer_type]
            progress = (prayer.completed / prayer.total_missed) * 100
            
            breakdown_text += f"🕌 **{prayer_name}:**\n"
            breakdown_text += f"   📝 Всего пропущено: {prayer.total_missed}\n"
            breakdown_text += f"   ✅ Восполнено: {prayer.completed}\n"
            breakdown_text += f"   ⏳ Осталось: {prayer.remaining}\n"
            breakdown_text += f"   📊 Прогресс: {progress:.1f}%\n"
            
            # Мини прогресс-бар для каждого намаза
            mini_bar = "▓" * int(progress / 20) + "░" * (5 - int(progress / 20))
            breakdown_text += f"   [{mini_bar}]\n\n"
    
    await callback.message.answer(breakdown_text, parse_mode="Markdown")

@router.callback_query(F.data == "refresh_stats")
async def refresh_statistics(callback: CallbackQuery):
    """Обновление статистики"""
    await show_user_statistics(callback.message)
    await callback.answer("🔄 Статистика обновлена")