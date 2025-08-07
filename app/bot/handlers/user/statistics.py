from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from ....core.services.prayer_service import PrayerService

router = Router()
prayer_service = PrayerService()

@router.message(F.text == "📊 Моя статистика")
@router.message(Command("stats"))
async def show_user_statistics(message: Message):
    """Показ статистики пользователя"""
    stats = await prayer_service.get_user_statistics(message.from_user.id)
    
    if stats['total_missed'] == 0:
        await message.answer(
            "📊 **Ваша статистика:**\n\n"
            "У вас пока нет данных о намазах.\n"
            "Используйте 🔢 Расчет намазов для настройки.",
            parse_mode="Markdown"
        )
        return
    
    # Формируем текст статистики
    stats_text = (
        "📊 **Ваша статистика восполнения намазов:**\n\n"
        f"📝 Всего пропущено: **{stats['total_missed']}**\n"
        f"✅ Восполнено: **{stats['total_completed']}**\n"
        f"⏳ Осталось: **{stats['total_remaining']}**\n\n"
    )
    
    if stats['total_completed'] > 0:
        progress = (stats['total_completed'] / stats['total_missed']) * 100
        stats_text += f"📈 Прогресс: **{progress:.1f}%**\n\n"
    
    stats_text += "**Детализация по намазам:**\n"
    
    for prayer_name, data in stats['prayers'].items():
        if data['total'] > 0:
            stats_text += (
                f"\n🕌 **{prayer_name}:**\n"
                f"   Пропущено: {data['total']}\n"
                f"   Восполнено: {data['completed']}\n"
                f"   Осталось: {data['remaining']}\n"
            )
    
    # Добавляем мотивационное сообщение
    if stats['total_remaining'] > 0:
        stats_text += "\n\n🤲 Да поможет вам Аллах в восполнении намазов!"
    else:
        stats_text += "\n\n🎉 Машаа Ллах! Все намазы восполнены!"
    
    await message.answer(stats_text, parse_mode="Markdown")
