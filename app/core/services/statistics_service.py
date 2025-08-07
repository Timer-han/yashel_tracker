from typing import Dict, List
from datetime import date, timedelta
from ..database.repositories.prayer_repository import PrayerRepository
from ..database.repositories.user_repository import UserRepository
from .calculation_service import CalculationService

class StatisticsService:
    """Сервис для работы со статистикой"""
    
    def __init__(self):
        self.prayer_repo = PrayerRepository()
        self.user_repo = UserRepository()
        self.calc_service = CalculationService()
    
    async def get_global_statistics(self) -> Dict:
        """Получение глобальной статистики"""
        stats = await self.prayer_repo.get_statistics()
        
        # Добавляем информацию о пользователях
        all_users = await self.user_repo.get_all_registered_users()
        
        user_stats = {
            'total_registered': len(all_users),
            'by_gender': {},
            'by_city': {},
            'by_age_group': {}
        }
        
        for user in all_users:
            # Статистика по полу
            if user.gender:
                user_stats['by_gender'][user.gender] = user_stats['by_gender'].get(user.gender, 0) + 1
            
            # Статистика по городу
            if user.city:
                user_stats['by_city'][user.city] = user_stats['by_city'].get(user.city, 0) + 1
            
            # Статистика по возрастным группам
            if user.birth_date:
                age = self.calc_service.calculate_age(user.birth_date)
                age_group = self._get_age_group(age)
                user_stats['by_age_group'][age_group] = user_stats['by_age_group'].get(age_group, 0) + 1
        
        return {
            **stats,
            'user_statistics': user_stats
        }
    
    def _get_age_group(self, age: int) -> str:
        """Определение возрастной группы"""
        if age < 18:
            return "До 18"
        elif age < 25:
            return "18-24"
        elif age < 35:
            return "25-34"
        elif age < 45:
            return "35-44"
        elif age < 55:
            return "45-54"
        else:
            return "55+"
