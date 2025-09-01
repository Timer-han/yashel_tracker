from typing import List, Dict, Optional
from ..database.repositories.prayer_repository import PrayerRepository
from ..database.repositories.prayer_history_repository import PrayerHistoryRepository
from ..database.repositories.user_repository import UserRepository
from ..database.models.prayer import Prayer
from ..database.models.prayer_history import PrayerHistory
from ..config import config

class PrayerService:
    """Сервис для работы с намазами"""
    
    def __init__(self):
        self.prayer_repo = PrayerRepository()
        self.history_repo = PrayerHistoryRepository()
        self.user_repo = UserRepository()
    
    async def set_user_prayers(self, telegram_id: int, prayers_data: Dict[str, int]) -> bool:
        """Установка намазов пользователя"""
        user = await self.user_repo.get_user_by_telegram_id(telegram_id)
        if not user:
            return False
        
        # Получаем ID пользователя из базы
        user_data = await self.user_repo.get_user_by_telegram_id(telegram_id)
        
        for prayer_type, count in prayers_data.items():
            if prayer_type in config.PRAYER_TYPES:
                await self.prayer_repo.create_or_update_prayer(
                    user_id=telegram_id, prayer_type=prayer_type, 
                    total_missed=count, completed=0
                )
                
                # Добавляем в историю
                await self.history_repo.add_history_record(
                    PrayerHistory(
                        user_id=telegram_id,
                        prayer_type=prayer_type,
                        action='set',
                        amount=count,
                        previous_value=0,
                        new_value=count,
                        comment='Установка начального количества'
                    )
                )
        
        return True
    
    async def update_prayer_count(self, telegram_id: int, prayer_type: str, 
                                  change: int) -> bool:
        """Изменение количества намазов"""
        prayer = await self.prayer_repo.get_prayer(telegram_id, prayer_type)
        if not prayer:
            # Создаем новый намаз если не существует
            await self.prayer_repo.create_or_update_prayer(
                telegram_id, prayer_type, max(0, change), 0
            )
            
            await self.history_repo.add_history_record(
                PrayerHistory(
                    user_id=telegram_id,
                    prayer_type=prayer_type,
                    action='add' if change > 0 else 'remove',
                    amount=abs(change),
                    previous_value=0,
                    new_value=max(0, change)
                )
            )
            return True
        
        # Обновляем существующий
        old_value = prayer.completed
        new_value = max(0, old_value + change)
        
        await self.prayer_repo.update_completed_prayers(
            telegram_id, prayer_type, change
        )
        
        # Добавляем в историю
        await self.history_repo.add_history_record(
            PrayerHistory(
                user_id=telegram_id,
                prayer_type=prayer_type,
                action='add' if change > 0 else 'remove',
                amount=abs(change),
                previous_value=old_value,
                new_value=new_value
            )
        )
        
        return True
    
    async def get_user_prayers(self, telegram_id: int) -> List[Prayer]:
        """Получение намазов пользователя"""
        return await self.prayer_repo.get_user_prayers(telegram_id)
    
    async def reset_user_prayers(self, telegram_id: int) -> bool:
        """Сброс всех намазов пользователя"""
        await self.prayer_repo.reset_user_prayers(telegram_id)
        
        # Добавляем в историю
        await self.history_repo.add_history_record(
            PrayerHistory(
                user_id=telegram_id,
                prayer_type='all',
                action='reset',
                amount=0,
                previous_value=0,
                new_value=0,
                comment='Полный сброс статистики'
            )
        )
        
        return True
    
    async def get_user_statistics(self, telegram_id: int) -> Dict:
        """Получение статистики пользователя"""
        prayers = await self.get_user_prayers(telegram_id)
        
        total_missed = sum(p.total_missed for p in prayers)
        total_completed = sum(p.completed for p in prayers)
        total_remaining = sum(p.remaining for p in prayers)
        
        prayer_details = {}
        for prayer in prayers:
            prayer_name = config.PRAYER_TYPES.get(prayer.prayer_type, prayer.prayer_type)
            prayer_details[prayer_name] = {
                'total': prayer.total_missed,
                'completed': prayer.completed,
                'remaining': prayer.remaining
            }
        
        return {
            'total_missed': total_missed,
            'total_completed': total_completed,
            'total_remaining': total_remaining,
            'prayers': prayer_details
        }
    
    async def increase_missed_prayers(self, telegram_id: int, prayer_type: str, 
                                      amount: int = 1) -> bool:
        """Увеличение количества пропущенных намазов"""
        prayer = await self.prayer_repo.get_prayer(telegram_id, prayer_type)
        
        if not prayer:
            # Создаем новый намаз
            await self.prayer_repo.create_or_update_prayer(
                telegram_id, prayer_type, amount, 0
            )
        else:
            # Обновляем существующий
            await self.prayer_repo.create_or_update_prayer(
                telegram_id, prayer_type, 
                prayer.total_missed + amount, prayer.completed
            )
        
        # Добавляем в историю
        await self.history_repo.add_history_record(
            PrayerHistory(
                user_id=telegram_id,
                prayer_type=prayer_type,
                action='add_missed',
                amount=amount,
                previous_value=prayer.total_missed if prayer else 0,
                new_value=(prayer.total_missed if prayer else 0) + amount,
                comment='Увеличение пропущенных намазов'
            )
        )
        
        return True
    
    async def update_specific_prayers(self, telegram_id: int, prayers_data: Dict[str, int]) -> bool:
        """Обновление только указанных типов намазов"""
        user = await self.user_repo.get_user_by_telegram_id(telegram_id)
        if not user:
            return False
        
        for prayer_type, count in prayers_data.items():
            if prayer_type in config.PRAYER_TYPES:
                # Получаем текущий намаз
                existing_prayer = await self.prayer_repo.get_prayer(telegram_id, prayer_type)
                
                if existing_prayer:
                    # Обновляем существующий (сохраняем completed)
                    await self.prayer_repo.create_or_update_prayer(
                        user_id=telegram_id, prayer_type=prayer_type, 
                        total_missed=count, completed=existing_prayer.completed
                    )
                else:
                    # Создаем новый
                    await self.prayer_repo.create_or_update_prayer(
                        user_id=telegram_id, prayer_type=prayer_type, 
                        total_missed=count, completed=0
                    )
                
                # Добавляем в историю
                await self.history_repo.add_history_record(
                    PrayerHistory(
                        user_id=telegram_id,
                        prayer_type=prayer_type,
                        action='update',
                        amount=count,
                        previous_value=existing_prayer.total_missed if existing_prayer else 0,
                        new_value=count,
                        comment='Индивидуальное обновление количества'
                    )
                )
        
        return True
