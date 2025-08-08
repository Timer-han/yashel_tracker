from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    """Показ настроек (заглушка)"""
    await message.answer(
        "⚙️ **Настройки**\n\n"
        "Данный раздел находится в разработке.\n"
        "Скоро здесь появятся:\n\n"
        "• Изменение личных данных\n"
        "• Настройки уведомлений\n" 
        "• Экспорт данных\n"
        "• Сброс статистики",
        parse_mode="Markdown"
    )