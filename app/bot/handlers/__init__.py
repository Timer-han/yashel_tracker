from aiogram import Dispatcher

from .common import start, help, cancel
from .user import registration, statistics, prayer_calculation, prayer_tracking
from .moderator import broadcast, user_statistics
from .admin import admin_management
from .user.settings import router as settings_router

def register_all_handlers(dp: Dispatcher):
    """Регистрация всех обработчиков"""
    
    # Общие обработчики
    dp.include_router(start.router)
    dp.include_router(help.router)
    dp.include_router(cancel.router)
    
    # Обработчики пользователей
    dp.include_router(registration.router)
    dp.include_router(statistics.router)
    dp.include_router(prayer_calculation.router)
    dp.include_router(prayer_tracking.router)
    
    # Обработчики модераторов
    dp.include_router(broadcast.router)
    dp.include_router(user_statistics.router)
    
    # Обработчики администраторов
    dp.include_router(admin_management.router)

    dp.include_router(settings_router)
