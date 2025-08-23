from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from ...utils.text_messages import text_message

router = Router()

@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
    """Обработчик команды помощи"""
    help_text = text_message.HELP_TEXT
    
    await message.answer(help_text, parse_mode="MarkdownV2")