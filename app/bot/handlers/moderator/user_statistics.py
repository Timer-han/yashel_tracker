from aiogram import Router, F
from aiogram.types import Message

from ....core.services.statistics_service import StatisticsService
from ...filters.role_filter import moderator_filter

router = Router()
router.message.filter(moderator_filter)

statistics_service = StatisticsService()

@router.message(F.text == "📈 Общая статистика")
async def show_global_statistics(message: Message):
    """Показ общей статистики для модераторов"""
    stats = await statistics_service.get_global_statistics()
    
    stats_text = (
        "📈 **Общая статистика системы**\n\n"
        f"👥 **Пользователи:** {stats['user_statistics']['total_registered']}\n\n"
    )
    
    # Статистика по полу
    gender_stats = stats['user_statistics']['by_gender']
    if gender_stats:
        stats_text += "**По полу:**\n"
        for gender, count in gender_stats.items():
            gender_text = "👨 Мужчины" if gender == 'male' else "👩 Женщины"
            stats_text += f"• {gender_text}: {count}\n"
        stats_text += "\n"
    
    # Топ-5 городов
    city_stats = stats['user_statistics']['by_city']
    if city_stats:
        sorted_cities = sorted(city_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        stats_text += "**Топ-5 городов:**\n"
        for city, count in sorted_cities:
            stats_text += f"• 📍 {city}: {count}\n"
        stats_text += "\n"
    
    # Статистика по возрасту
    age_stats = stats['user_statistics']['by_age_group']
    if age_stats:
        stats_text += "**По возрастным группам:**\n"
        for age_group, count in age_stats.items():
            stats_text += f"• {age_group} лет: {count}\n"
        stats_text += "\n"
    
    # Статистика намазов
    if stats['prayer_statistics']:
        stats_text += "🕌 **Статистика намазов:**\n\n"
        
        total_missed = sum(p['total_missed'] for p in stats['prayer_statistics'])
        total_completed = sum(p['total_completed'] for p in stats['prayer_statistics'])
        total_remaining = sum(p['total_remaining'] for p in stats['prayer_statistics'])
        
        stats_text += f"📝 Всего пропущено: **{total_missed:,}**\n"
        stats_text += f"✅ Восполнено: **{total_completed:,}**\n"
        stats_text += f"⏳ Осталось: **{total_remaining:,}**\n\n"
        
        if total_missed > 0:
            progress = (total_completed / total_missed) * 100
            stats_text += f"📈 Общий прогресс: **{progress:.1f}%**\n\n"
        
        stats_text += "**По типам намазов:**\n"
        for prayer_stat in stats['prayer_statistics']:
            from ....core.config import config
            prayer_name = config.PRAYER_TYPES.get(prayer_stat['prayer_type'], prayer_stat['prayer_type'])
            if prayer_stat['total_missed'] > 0:
                stats_text += f"• {prayer_name}: {prayer_stat['total_remaining']:,} осталось\n"
    
    await message.answer(stats_text, parse_mode="Markdown")
