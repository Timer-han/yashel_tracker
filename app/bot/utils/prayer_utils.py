from typing import Dict, List
from ...core.config import config
from ...core.database.models.prayer import Prayer

def format_prayer_statistics(prayers: List[Prayer]) -> str:
    """Форматирование статистики намазов для отображения"""
    if not prayers:
        return "У вас пока нет данных о намазах."
    
    total_missed = sum(p.total_missed for p in prayers)
    total_completed = sum(p.completed for p in prayers)
    total_remaining = sum(p.remaining for p in prayers)
    
    stats_text = (
        f"📝 Всего пропущено: **{total_missed}**\n"
        f"✅ Восполнено: **{total_completed}**\n"
        f"⏳ Осталось: **{total_remaining}**\n\n"
    )
    
    if total_completed > 0 and total_missed > 0:
        progress = (total_completed / total_missed) * 100
        stats_text += f"📈 Прогресс: **{progress:.1f}%**\n\n"
    
    stats_text += "**Детализация по намазам:**\n"
    
    for prayer in prayers:
        if prayer.total_missed > 0:
            prayer_name = config.PRAYER_TYPES.get(prayer.prayer_type, prayer.prayer_type)
            stats_text += (
                f"\n🕌 **{prayer_name}:**\n"
                f"   Пропущено: {prayer.total_missed}\n"
                f"   Восполнено: {prayer.completed}\n"
                f"   Осталось: {prayer.remaining}\n"
            )
    
    return stats_text

def get_prayer_display_name(prayer_type: str) -> str:
    """Получение отображаемого имени намаза"""
    return config.PRAYER_TYPES.get(prayer_type, prayer_type)

def format_prayer_count_button(prayer_type: str, count: int) -> str:
    """Форматирование текста кнопки с количеством намазов"""
    prayer_name = get_prayer_display_name(prayer_type)
    return f"{prayer_name}: {count}"
