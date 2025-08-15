from typing import List, Dict, Optional
from ..database.repositories.fast_repository import FastRepository
from ..database.repositories.user_repository import UserRepository
from ..database.models.fast import Fast
from ..config import config

class FastService:
    """Сервис для работы с постами"""
    
    def __init__(self):
        self.fast_repo = FastRepository()
        self.user_repo = UserRepository()
    
    async def set_user_fasts(self, telegram_id: int, fasts_data: Dict[str, int]) -> bool:
        """Установка постов пользователя"""
        user = await self.user_repo.get_user_by_telegram_id(telegram_id)
        if not user:
            return False
        
        for fast_key, count in fasts_data.items():
            # Парсим ключ для определения типа и года
            if "ramadan" in fast_key:
                parts = fast_key.split("_")
                fast_type = "ramadan"
                year = int(parts[1]) if len(parts) > 1 else None
            else:
                fast_type = fast_key
                year = None
            
            await self.fast_repo.create_or_update_fast(
                user_id=telegram_id,
                fast_type=fast_type,
                year=year,
                total_missed=count,
                completed=0
            )
        
        return True
    
    async def update_fast_count(self, telegram_id: int, fast_type: str, 
                                change: int, year: Optional[int] = None) -> bool:
        """Изменение количества восполненных постов"""
        fast = await self.fast_repo.get_fast(telegram_id, fast_type, year)
        
        if not fast:
            # Создаем новый пост если не существует
            await self.fast_repo.create_or_update_fast(
                telegram_id, fast_type, year, 0, max(0, change)
            )
            return True
        
        # Обновляем существующий
        await self.fast_repo.update_completed_fasts(
            telegram_id, fast_type, change, year
        )
        
        return True
    
    async def get_user_fasts(self, telegram_id: int) -> List[Fast]:
        """Получение постов пользователя"""
        return await self.fast_repo.get_user_fasts(telegram_id)
    
    async def reset_user_fasts(self, telegram_id: int) -> bool:
        """Сброс всех постов пользователя"""
        return await self.fast_repo.reset_user_fasts(telegram_id)
    
    async def get_user_fast_statistics(self, telegram_id: int) -> Dict:
        """Получение статистики постов пользователя"""
        fasts = await self.get_user_fasts(telegram_id)
        
        total_missed = sum(f.total_missed for f in fasts)
        total_completed = sum(f.completed for f in fasts)
        total_remaining = sum(f.remaining for f in fasts)
        
        fast_details = {}
        
        # Группируем посты по типам
        ramadan_fasts = [f for f in fasts if f.fast_type == 'ramadan']
        other_fasts = [f for f in fasts if f.fast_type != 'ramadan']
        
        # Детализация по Рамадану
        if ramadan_fasts:
            for fast in sorted(ramadan_fasts, key=lambda x: x.year or 0):
                year_label = f"Рамадан {fast.year}" if fast.year else "Рамадан"
                fast_details[year_label] = {
                    'total': fast.total_missed,
                    'completed': fast.completed,
                    'remaining': fast.remaining
                }
        
        # Детализация по другим постам
        for fast in other_fasts:
            fast_name = config.FAST_TYPES.get(fast.fast_type, fast.fast_type)
            fast_details[fast_name] = {
                'total': fast.total_missed,
                'completed': fast.completed,
                'remaining': fast.remaining
            }
        
        return {
            'total_missed': total_missed,
            'total_completed': total_completed,
            'total_remaining': total_remaining,
            'fasts': fast_details
        }
    
    async def increase_missed_fasts(self, telegram_id: int, fast_type: str,
                                    amount: int = 1, year: Optional[int] = None) -> bool:
        """Увеличение количества пропущенных постов"""
        fast = await self.fast_repo.get_fast(telegram_id, fast_type, year)
        
        if not fast:
            # Создаем новый пост
            await self.fast_repo.create_or_update_fast(
                telegram_id, fast_type, year, amount, 0
            )
        else:
            # Обновляем существующий
            await self.fast_repo.create_or_update_fast(
                telegram_id, fast_type, year,
                fast.total_missed + amount, fast.completed
            )
        
        return True