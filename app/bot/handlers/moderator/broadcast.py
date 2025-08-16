from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from ...keyboards.moderator.mod_menu import (
    get_broadcast_filters_keyboard,
    get_age_filter_keyboard, 
    get_broadcast_confirmation_keyboard
)
from ....core.services.broadcast_service import BroadcastService
from ....core.config import config
from ...filters.role_filter import moderator_filter
from ...states.moderator import ModeratorStates

router = Router()
router.message.filter(moderator_filter)
router.callback_query.filter(moderator_filter)

broadcast_service = BroadcastService()

@router.message(F.text == "📢 Рассылка")
async def start_broadcast(message: Message, state: FSMContext):
    """Начало создания рассылки"""
    await state.clear()
    
    await message.answer(
        "📢 *Создание рассылки*\n\n"
        "Выберите фильтры для целевой аудитории:",
        reply_markup=get_broadcast_filters_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(ModeratorStates.broadcast_filters)

@router.callback_query(ModeratorStates.broadcast_filters, F.data.startswith("filter_"))
async def process_filter(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора фильтров"""
    filter_type = callback.data.split("_", 1)[1]
    
    current_filters = (await state.get_data()).get('filters', {})
    
    if filter_type == "gender_male":
        current_filters['gender'] = 'male'
        await callback.answer("✅ Фильтр: только мужчины")
        
    elif filter_type == "gender_female":
        current_filters['gender'] = 'female'
        await callback.answer("✅ Фильтр: только женщины")
        
    elif filter_type == "city":
        await callback.message.edit_text(
            "📍 Введите название города для фильтрации:"
        )
        await state.update_data(filters=current_filters, waiting_for='city')
        await state.set_state(ModeratorStates.broadcast_message)
        return
        
    elif filter_type == "age":
        await callback.message.edit_text(
            "🎂 Выберите возрастную группу:",
            reply_markup=get_age_filter_keyboard()
        )
        await state.update_data(filters=current_filters)
        return
        
    elif filter_type.startswith("age_"):
        age_range = filter_type.split("_", 1)[1]
        age_ranges = {
            "0_18": (0, 18),
            "18_24": (18, 24),
            "25_34": (25, 34),
            "35_44": (35, 44), 
            "45_54": (45, 54),
            "55_plus": (55, 150)
        }
        current_filters['age_range'] = age_ranges.get(age_range, (0, 150))
        await callback.answer(f"✅ Фильтр: возраст {age_range.replace('_', '-')}")
        
    elif filter_type == "all":
        current_filters = {}
        await callback.answer("✅ Рассылка всем пользователям")
    
    await state.update_data(filters=current_filters)
    
    # Переходим к вводу сообщения
    await callback.message.edit_text(_get_filter_text(current_filters))

    await state.set_state(ModeratorStates.broadcast_message)

def _get_filter_text(filters: dict):
    filter_text = "📢 *Настройка рассылки*\n\n"
    filter_text += "*Выбранные фильтры:*\n"
    
    if 'gender' in filters:
        gender_text = "Мужчины" if filters['gender'] == 'male' else "Женщины"
        filter_text += f"👤 Пол: {gender_text}\n"
    
    if 'city' in filters:
        filter_text += f"📍 Город: {filters['city']}\n"
        
    if 'age_range' in filters:
        min_age, max_age = filters['age_range']
        age_text = f"{min_age}-{max_age}" if max_age < 150 else f"{min_age}+"
        filter_text += f"🎂 Возраст: {age_text}\n"
    
    if not filters:
        filter_text += "Всем пользователям\n"
    
    filter_text += "\n📝 Теперь введите текст сообщения для рассылки:"
    
    return filter_text

async def _show_message_input(callback: CallbackQuery, filters: dict):
    """Показ интерфейса ввода сообщения"""
    filter_text = "📢 *Настройка рассылки*\n\n"
    filter_text += "*Выбранные фильтры:*\n"
    
    if 'gender' in filters:
        gender_text = "Мужчины" if filters['gender'] == 'male' else "Женщины"
        filter_text += f"👤 Пол: {gender_text}\n"
    
    if 'city' in filters:
        filter_text += f"📍 Город: {filters['city']}\n"
        
    if 'age_range' in filters:
        min_age, max_age = filters['age_range']
        age_text = f"{min_age}-{max_age}" if max_age < 150 else f"{min_age}+"
        filter_text += f"🎂 Возраст: {age_text}\n"
    
    if not filters:
        filter_text += "Всем пользователям\n"
    
    filter_text += "\n📝 Теперь введите текст сообщения для рассылки:"
    
    await callback.message.edit_text(filter_text, parse_mode="Markdown")

@router.message(ModeratorStates.broadcast_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """Обработка текста сообщения для рассылки"""
    data = await state.get_data()
    
    # Проверяем, ожидается ли ввод города
    if data.get('waiting_for') == 'city':
        filters = data.get('filters', {})
        filters['city'] = message.text.strip()
        await state.update_data(filters=filters, waiting_for=None)
        await message.answer(
            _get_filter_text(filters),
            parse_mode="Markdown"
        )
        # await _show_message_input(, filters)
        await state.set_state(ModeratorStates.broadcast_message)
        return
    
    await state.update_data(message_text=message.text)
    
    # Показываем предпросмотр
    preview_text = (
        "📋 *Предпросмотр рассылки*\n\n"
        "*Сообщение:*\n"
        f"{message.text}\n\n"
        "*Фильтры:* "
    )
    
    filters = data.get('filters', {})
    if not filters:
        preview_text += "Всем пользователям"
    else:
        filter_parts = []
        if 'gender' in filters:
            gender_text = "мужчины" if filters['gender'] == 'male' else "женщины"
            filter_parts.append(gender_text)
        if 'city' in filters:
            filter_parts.append(f"г. {filters['city']}")
        if 'age_range' in filters:
            min_age, max_age = filters['age_range']
            age_text = f"возраст {min_age}-{max_age}" if max_age < 150 else f"возраст {min_age}+"
            filter_parts.append(age_text)
        
        preview_text += ", ".join(filter_parts)
    
    preview_text += "\n\n⚠️ Отправить рассылку?"
    
    await message.answer(
        preview_text,
        reply_markup=get_broadcast_confirmation_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(ModeratorStates.broadcast_confirmation)

@router.callback_query(ModeratorStates.broadcast_confirmation, F.data == "confirm_broadcast")
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и отправка рассылки"""
    data = await state.get_data()
    
    await callback.message.edit_text("📤 Отправка рассылки... Пожалуйста, подождите.")
    
    # Отправляем рассылку
    try:
        result = await broadcast_service.send_broadcast(
            message_text=data['message_text'],
            filters=data.get('filters', {})
        )
        
        result_text = (
            "✅ *Рассылка завершена!*\n\n"
            f"📊 Статистика:\n"
            f"• Отправлено: {result['sent']}\n"
            f"• Ошибок: {result['errors']}\n"
            f"• Всего пользователей: {result['total_users']}"
        )
        
        await callback.message.edit_text(result_text, parse_mode="Markdown")
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ *Ошибка при отправке рассылки*\n\n"
            f"Детали: {str(e)}"
        )
    
    await state.clear()

@router.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    """Отмена рассылки"""
    await callback.message.edit_text("❌ Рассылка отменена.")
    await state.clear()

@router.callback_query(F.data == "back_to_filters")
async def back_to_filters(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору фильтров"""
    await callback.message.edit_text(
        "📢 *Создание рассылки*\n\n"
        "Выберите фильтры для целевой аудитории:",
        reply_markup=get_broadcast_filters_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(ModeratorStates.broadcast_filters)