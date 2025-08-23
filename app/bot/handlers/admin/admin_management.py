from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from ...keyboards.admin.admin_menu import (
    get_admin_management_keyboard,
    get_role_selection_keyboard,
    get_admin_confirmation_keyboard
)
from ....core.database.repositories.admin_repository import AdminRepository
from ....core.database.repositories.user_repository import UserRepository
from ....core.database.models.admin import Admin
from ....core.config import config
from ...filters.role_filter import admin_filter
from ...states.admin import AdminStates

router = Router()
router.message.filter(admin_filter)
router.callback_query.filter(admin_filter)

admin_repo = AdminRepository()
user_repo = UserRepository()

@router.message(F.text == "👥 Управление админами")
async def show_admin_management(message: Message, state: FSMContext):
    """Показ меню управления администраторами"""
    await state.clear()
    
    await message.answer(
        "👥 *Управление администраторами*\n\n"
        "Выберите действие:",
        reply_markup=get_admin_management_keyboard(),
        parse_mode="MarkdownV2"
    )

@router.callback_query(F.data == "add_moderator")
async def add_moderator_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления модератора"""
    await state.update_data(role="moderator")
    
    await callback.message.edit_text(
        "➕ *Добавление модератора*\n\n"
        "Отправьте Telegram ID пользователя, которого хотите назначить модератором:"
    )
    await state.set_state(AdminStates.add_admin_id)

@router.callback_query(F.data == "add_admin")
async def add_admin_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления администратора"""
    await state.update_data(role="admin")
    
    await callback.message.edit_text(
        "➕ *Добавление администратора*\n\n"
        "⚠️ *ВНИМАНИЕ*: Администратор получит полные права в системе!\n\n"
        "Отправьте Telegram ID пользователя, которого хотите назначить администратором:"
    )
    await state.set_state(AdminStates.add_admin_id)

@router.message(AdminStates.add_admin_id)
async def process_admin_id(message: Message, state: FSMContext):
    """Обработка ID для добавления админа"""
    try:
        user_id = int(message.text.strip())
        
        # Проверяем, не является ли уже админом
        existing_admin = await admin_repo.get_admin(user_id)
        if existing_admin:
            await message.answer(f"❌ Пользователь {user_id} уже является {existing_admin.role}")
            return
        
        data = await state.get_data()
        role = data['role']
        
        # Сохраняем данные для подтверждения
        await state.update_data(user_id=user_id)
        
        role_text = "модератором" if role == "moderator" else "администратором"
        
        await message.answer(
            f"👤 *Подтверждение назначения*\n\n"
            f"Пользователь ID: `{user_id}`\n"
            f"Роль: *{role_text.capitalize()}*\n\n"
            f"❓ Назначить этого пользователя {role_text}?",
            reply_markup=get_admin_confirmation_keyboard(),
            parse_mode="MarkdownV2"
        )
        await state.set_state(AdminStates.confirmation)
        
    except ValueError:
        await message.answer("❌ Неверный формат. Введите числовой Telegram ID.")

@router.callback_query(AdminStates.confirmation, F.data == "confirm_admin_action")
async def confirm_add_admin(callback: CallbackQuery, state: FSMContext):
    """Подтверждение добавления админа"""
    data = await state.get_data()
    user_id = data['user_id']
    role = data['role']
    
    # Создаем админа
    new_admin = Admin(
        telegram_id=user_id,
        role=role,
        added_by=callback.from_user.id
    )
    
    success = await admin_repo.add_admin(new_admin)
    
    if success:
        # Обновляем роль в таблице пользователей
        await user_repo.update_user(user_id, role=role)
        
        role_text = "модератором" if role == "moderator" else "администратором"
        await callback.message.edit_text(
            f"✅ Пользователь {user_id} успешно назначен {role_text}!"
        )
    else:
        await callback.message.edit_text("❌ Ошибка при добавлении. Возможно, пользователь уже существует.")
    
    await state.clear()

@router.callback_query(F.data == "list_admins")
async def list_admins(callback: CallbackQuery):
    """Список всех администраторов"""
    admins = await admin_repo.get_all_admins()
    
    if not admins:
        await callback.message.edit_text("📋 Список администраторов пуст.")
        return
    
    admins_text = "📋 *Список администраторов:*\n\n"
    
    # Группируем по ролям
    admin_list = [a for a in admins if a.role == "admin"]
    moderator_list = [a for a in admins if a.role == "moderator"]
    
    if admin_list:
        admins_text += "👑 *Администраторы:*\n"
        for admin in admin_list:
            admins_text += f"• ID: `{admin.telegram_id}`\n"
        admins_text += "\n"
    
    if moderator_list:
        admins_text += "👮 *Модераторы:*\n"
        for moderator in moderator_list:
            admins_text += f"• ID: `{moderator.telegram_id}`\n"
    
    await callback.message.edit_text(admins_text, parse_mode="MarkdownV2")

@router.callback_query(F.data == "remove_admin")
async def remove_admin_start(callback: CallbackQuery, state: FSMContext):
    """Начало удаления админа"""
    await callback.message.edit_text(
        "➖ *Удаление администратора/модератора*\n\n"
        "Отправьте Telegram ID пользователя, которого хотите лишить прав:"
    )
    await state.set_state(AdminStates.remove_admin_id)

@router.message(AdminStates.remove_admin_id)
async def process_remove_admin_id(message: Message, state: FSMContext):
    """Обработка ID для удаления админа"""
    try:
        user_id = int(message.text.strip())
        
        # Проверяем, является ли админом
        admin = await admin_repo.get_admin(user_id)
        if not admin:
            await message.answer(f"❌ Пользователь {user_id} не является администратором или модератором.")
            return
        
        # Нельзя удалить самого себя
        if user_id == message.from_user.id:
            await message.answer("❌ Нельзя лишить прав самого себя!")
            return
        
        # Сохраняем данные для подтверждения
        await state.update_data(user_id=user_id, current_role=admin.role)
        
        role_text = "администратора" if admin.role == "admin" else "модератора"
        
        await message.answer(
            f"⚠️ *Подтверждение удаления*\n\n"
            f"Пользователь ID: `{user_id}`\n"
            f"Текущая роль: *{role_text.capitalize()}*\n\n"
            f"❓ Лишить этого пользователя прав {role_text}?",
            reply_markup=get_admin_confirmation_keyboard(),
            parse_mode="MarkdownV2"
        )
        await state.set_state(AdminStates.confirmation)
        
    except ValueError:  
        await message.answer("❌ Неверный формат. Введите числовой Telegram ID.")

@router.callback_query(AdminStates.confirmation, F.data == "confirm_admin_action")
async def confirm_remove_admin(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления админа"""
    data = await state.get_data()
    
    if 'current_role' in data:  # Это удаление
        user_id = data['user_id']
        
        success = await admin_repo.remove_admin(user_id)
        
        if success:
            # Возвращаем обычную роль пользователя
            await user_repo.update_user(user_id, role="user")
            
            role_text = "администратора" if data['current_role'] == "admin" else "модератора"
            await callback.message.edit_text(
                f"✅ Пользователь {user_id} лишен прав {role_text}."
            )
        else:
            await callback.message.edit_text("❌ Ошибка при удалении прав.")
    
    await state.clear()

@router.callback_query(F.data == "cancel_admin_action")
async def cancel_admin_action(callback: CallbackQuery, state: FSMContext):
    """Отмена действия с админами"""
    await callback.message.edit_text("❌ Действие отменено.")
    await state.clear()

@router.callback_query(F.data == "back_to_menu")
async def back_to_admin_menu(callback: CallbackQuery):
    """Возврат в меню управления админами"""
    await callback.message.edit_text(
        "👥 *Управление администраторами*\n\n"
        "Выберите действие:",
        reply_markup=get_admin_management_keyboard(),
        parse_mode="MarkdownV2"
    )
