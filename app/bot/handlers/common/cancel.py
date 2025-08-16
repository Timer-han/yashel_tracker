from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from ...keyboards.user.main_menu import get_main_menu_keyboard, get_moderator_menu_keyboard, get_admin_menu_keyboard
from ....core.services.user_service import UserService
from ....core.config import config

router = Router()
user_service = UserService()

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Обработчик отмены текущего действия"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активных действий для отмены.")
        return
    
    await state.clear()
    
    # Получаем пользователя для определения клавиатуры
    user = await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username
    )
    
    # Выбираем клавиатуру в зависимости от роли
    if user.role == config.Roles.ADMIN:
        keyboard = get_admin_menu_keyboard()
    elif user.role == config.Roles.MODERATOR:
        keyboard = get_moderator_menu_keyboard()
    else:
        keyboard = get_main_menu_keyboard()
    
    await message.answer("❌ Действие отменено. Возвращаемся в главное меню.", reply_markup=keyboard)