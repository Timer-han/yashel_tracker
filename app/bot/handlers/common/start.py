from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from ...keyboards.user.main_menu import get_main_menu_keyboard, get_moderator_menu_keyboard, get_admin_menu_keyboard
from ...keyboards.user.registration import get_skip_name_keyboard
from ....core.services.user_service import UserService
from ....core.config import config
from ...states.registration import RegistrationStates

router = Router()
user_service = UserService()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    
    user = await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip() or None
    )
    
    if not user.is_registered:
        await message.answer(
            "🕌 Ассаляму алейкум! Добро пожаловать в Яшел Трекер!\n\n"
            "Этот бот поможет вам отслеживать восполнение пропущенных намазов.\n\n"
            "📝 Для начала давайте пройдем небольшую регистрацию.\n\n"
            "Как вас зовут? (Или нажмите 'Пропустить', чтобы использовать имя из Telegram)",
            reply_markup=get_skip_name_keyboard()
        )
        await state.set_state(RegistrationStates.waiting_for_name)
    else:
        # Показываем соответствующее меню в зависимости от роли
        if user.role == config.Roles.ADMIN:
            keyboard = get_admin_menu_keyboard()
            welcome_text = "👑 Панель администратора"
        elif user.role == config.Roles.MODERATOR:
            keyboard = get_moderator_menu_keyboard()  
            welcome_text = "👮 Панель модератора"
        else:
            keyboard = get_main_menu_keyboard()
            welcome_text = "🏠 Главное меню"
        
        await message.answer(
            f"🕌 Ассаляму алейкум, {user.full_name or user.username}!\n\n"
            f"{welcome_text}",
            reply_markup=keyboard
        )