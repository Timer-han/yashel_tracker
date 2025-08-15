from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import date, datetime
import logging

from ...keyboards.user.fast_calc import get_fast_calculation_method_keyboard
from ...keyboards.user.main_menu import get_main_menu_keyboard
from ....core.services.fast_service import FastService
from ....core.services.enhanced_calculation_service import EnhancedCalculationService
from ....core.database.repositories.female_periods_repository import FemalePeriodsRepository
from ....core.database.repositories.user_repository import UserRepository
from ....core.config import config
from ...states.female_periods import FastCalculationStates
from ...utils.date_utils import parse_date, format_date

logger = logging.getLogger(__name__)
router = Router()

fast_service = FastService()
calc_service = EnhancedCalculationService()
periods_repo = FemalePeriodsRepository()
user_repo = UserRepository()

@router.message(F.text == "📿 Расчет постов")
async def start_fast_calculation(message: Message, state: FSMContext):
    """Начало расчета постов"""
    await state.clear()
    
    await message.answer(
        "📿 **Расчет пропущенных постов**\n\n"
        "Выберите способ расчета:",
        reply_markup=get_fast_calculation_method_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(FastCalculationStates.choosing_method)

@router.callback_query(FastCalculationStates.choosing_method, F.data == "fast_calc_from_age")
async def calc_fast_from_age(callback: CallbackQuery, state: FSMContext):
    """Расчет постов от возраста совершеннолетия"""
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    
    if not user.birth_date:
        await callback.message.edit_text(
            "❌ Для этого расчета нужна ваша дата рождения. "
            "Пожалуйста, укажите ее в настройках профиля."
        )
        return
    
    await callback.message.edit_text(
        "📅 Введите дату, когда вы начали регулярно держать посты в формате ДД.ММ.ГГГГ:\n"
        "Например: 01.01.2020"
    )
    await state.set_state(FastCalculationStates.waiting_for_fasting_start_date)

@router.message(FastCalculationStates.waiting_for_fasting_start_date)
async def process_fasting_start_date(message: Message, state: FSMContext):
    """Обработка даты начала постов"""
    fasting_start_date = parse_date(message.text)
    
    if not fasting_start_date:
        await message.answer("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
        return
    
    user = await user_repo.get_user_by_telegram_id(message.from_user.id)
    
    # Получаем возраст совершеннолетия по полу
    adult_age = calc_service.get_adult_age_by_gender(user.gender)
    adult_date = user.birth_date.replace(year=user.birth_date.year + adult_age)
    
    if fasting_start_date <= adult_date:
        await message.answer(
            f"❌ Дата начала постов должна быть после даты совершеннолетия "
            f"({format_date(adult_date)})"
        )
        return
    
    # Получаем информацию о женских периодах, если это женщина
    hayd_info_list = []
    nifas_info_list = []
    
    if user.gender == 'female':
        hayd_info_list = await periods_repo.get_all_hayd_info(message.from_user.id)
        nifas_info_list = await periods_repo.get_all_nifas_info(message.from_user.id)
    
    # Рассчитываем посты
    fasts_data = calc_service.calculate_fasts_with_female_periods(
        start_date=adult_date,
        end_date=fasting_start_date,
        gender=user.gender,
        hayd_info_list=hayd_info_list,
        nifas_info_list=nifas_info_list
    )
    
    # Сохраняем результаты
    await fast_service.set_user_fasts(message.from_user.id, fasts_data)
    
    # Сохраняем дату начала постов
    await user_repo.update_user(
        telegram_id=message.from_user.id,
        fasting_start_date=fasting_start_date
    )
    
    # Формируем результат
    total_fasts = sum(fasts_data.values())
    result_text = (
        f"✅ **Расчет постов завершен!**\n\n"
        f"📊 Период: с {format_date(adult_date)} по {format_date(fasting_start_date)}\n"
    )
    
    if user.gender == 'female' and (hayd_info_list or nifas_info_list):
        result_text += "📍 Учтены женские периоды (хайд и нифас)\n"
    
    result_text += f"\n📝 **Всего пропущенных постов: {total_fasts}**\n\n"
    
    if fasts_data:
        result_text += "**Детализация по годам:**\n"
        for fast_key, count in sorted(fasts_data.items()):
            if count > 0:
                if "ramadan" in fast_key:
                    year = fast_key.split("_")[1]
                    result_text += f"• Рамадан {year}: {count} дней\n"
                else:
                    result_text += f"• {fast_key}: {count} дней\n"
    
    result_text += "\n🤲 Пусть Аллах облегчит вам восполнение постов!"
    
    await message.answer(
        result_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
    await state.clear()

@router.callback_query(FastCalculationStates.choosing_method, F.data == "fast_calc_manual")
async def calc_fast_manual(callback: CallbackQuery, state: FSMContext):
    """Ручной ввод постов"""
    await callback.message.edit_text(
        "📝 **Ручной ввод пропущенных постов**\n\n"
        "Введите годы, за которые вы пропустили посты Рамадана, через запятую.\n"
        "Например: 2018, 2019, 2020\n\n"
        "Или введите 0, если не пропускали посты Рамадана.",
        parse_mode="Markdown"
    )
    await state.set_state(FastCalculationStates.entering_ramadan_years)

@router.message(FastCalculationStates.entering_ramadan_years)
async def process_ramadan_years(message: Message, state: FSMContext):
    """Обработка годов Рамадана"""
    
    if message.text.strip() == "0":
        # Пользователь не пропускал посты
        await message.answer(
            "✅ Отлично! У вас нет пропущенных постов Рамадана.\n\n"
            "🤲 Машаа Ллах!",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        return
    
    try:
        # Парсим годы
        years_str = message.text.replace(" ", "").split(",")
        years = []
        
        for year_str in years_str:
            year = int(year_str.strip())
            if year < 1950 or year > date.today().year:
                await message.answer(
                    f"❌ Некорректный год: {year}. "
                    f"Введите годы от 1950 до {date.today().year}"
                )
                return
            years.append(year)
        
        # Формируем данные о постах
        fasts_data = {}
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        for year in years:
            # Для каждого года добавляем 30 дней Рамадана
            # Если женщина, нужно учесть периоды
            if user.gender == 'female':
                # Упрощенно добавляем 30 дней
                # В реальности нужно вычесть дни хайд в Рамадане
                fasts_data[f"ramadan_{year}"] = 30
            else:
                fasts_data[f"ramadan_{year}"] = 30
        
        # Сохраняем данные
        await fast_service.set_user_fasts(message.from_user.id, fasts_data)
        
        # Показываем результат
        total_fasts = sum(fasts_data.values())
        result_text = (
            f"✅ **Посты сохранены!**\n\n"
            f"📝 **Всего пропущенных постов: {total_fasts}**\n\n"
            "**Детализация:**\n"
        )
        
        for year in sorted(years):
            result_text += f"• Рамадан {year}: 30 дней\n"
        
        if user.gender == 'female':
            result_text += (
                "\n📍 *Примечание для женщин:*\n"
                "Посты, пропущенные во время хайд или нифас в Рамадане, "
                "нужно восполнить 1:1 (один день за один день)."
            )
        
        result_text += "\n\n🤲 Пусть Аллах облегчит вам восполнение!"
        
        await message.answer(
            result_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Введите годы через запятую.\n"
            "Например: 2018, 2019, 2020"
        )