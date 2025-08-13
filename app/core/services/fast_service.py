from typing import List, Dict, Optional
from ..database.repositories.fast_repository import FastRepository
from ..database.repositories.user_repository import UserRepository
from ..database.models.fast import Fast
from ..database.models.fast_history import FastHistory
from ..config import config

class FastService:
    """Сервис для работы с постами"""
    
    def __init__(self):
        self.fast_repo = FastRepository()
        self.user_repo = UserRepository()
    
    async def set_user_fasts(self, telegram_id: int, fasts_data: Dict[str, int]) -> bool:
        """Установка постов пользователя"""
        for fast_type, count in fasts_data.items():
            if fast_type in config.FAST_TYPES:
                await self.fast_repo.create_or_update_fast(
                    user_id=telegram_id, fast_type=fast_type, 
                    total_missed=count, completed=0
                )
        
        return True
    
    async def update_fast_count(self, telegram_id: int, fast_type: str, 
                                change: int) -> bool:
        """Изменение количества постов"""
        fast = await self.fast_repo.get_fast(telegram_id, fast_type)
        if not fast:
            # Создаем новый пост если не существует
            await self.fast_repo.create_or_update_fast(
                telegram_id, fast_type, max(0, change), 0
            )
            return True
        
        # Обновляем существующий
        await self.fast_repo.update_completed_fasts(
            telegram_id, fast_type, change
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
        for fast in fasts:
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
                                    amount: int = 1) -> bool:
        """Увеличение количества пропущенных постов"""
        fast = await self.fast_repo.get_fast(telegram_id, fast_type)
        
        if not fast:
            # Создаем новый пост
            await self.fast_repo.create_or_update_fast(
                telegram_id, fast_type, amount, 0
            )
        else:
            # Обновляем существующий
            await self.fast_repo.create_or_update_fast(
                telegram_id, fast_type, 
                fast.total_missed + amount, fast.completed
            )
        
        return True