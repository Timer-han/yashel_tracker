from typing import List, Optional, Dict
from ..connection import db_manager
from ..models.prayer import Prayer

class PrayerRepository:
    """Репозиторий для работы с намазами"""
    
    async def create_or_update_prayer(self, user_id: int, prayer_type: str, 
                                      total_missed: int = 0, completed: int = 0) -> bool:
        """Создание или обновление намаза"""
        async with await db_manager.get_connection() as db:
            await db.execute("""
                INSERT INTO prayers (user_id, prayer_type, total_missed, completed)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, prayer_type) DO UPDATE SET
                    total_missed = excluded.total_missed,
                    completed = excluded.completed,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, prayer_type, total_missed, completed))
            await db.commit()
            return True
    
    async def get_user_prayers(self, user_id: int) -> List[Prayer]:
        """Получение всех намазов пользователя"""
        async with await db_manager.get_connection() as db:
            cursor = await db.execute("""
                SELECT * FROM prayers WHERE user_id = ?
            """, (user_id,))
            rows = await cursor.fetchall()
            
            prayers = []
            for row in rows:
                prayers.append(Prayer(
                    user_id=row['user_id'],
                    prayer_type=row['prayer_type'],
                    total_missed=row['total_missed'],
                    completed=row['completed']
                ))
            return prayers
    
    async def get_prayer(self, user_id: int, prayer_type: str) -> Optional[Prayer]:
        """Получение конкретного намаза"""
        async with await db_manager.get_connection() as db:
            cursor = await db.execute("""
                SELECT * FROM prayers WHERE user_id = ? AND prayer_type = ?
            """, (user_id, prayer_type))
            row = await cursor.fetchone()
            if not row:
                return None
            
            return Prayer(
                user_id=row['user_id'],
                prayer_type=row['prayer_type'],
                total_missed=row['total_missed'],
                completed=row['completed']
            )
    
    async def update_completed_prayers(self, user_id: int, prayer_type: str, 
                                       amount: int) -> bool:
        """Обновление количества совершенных намазов"""
        async with await db_manager.get_connection() as db:
            await db.execute("""
                UPDATE prayers SET completed = completed + ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND prayer_type = ?
            """, (amount, user_id, prayer_type))
            await db.commit()
            return True
    
    async def reset_user_prayers(self, user_id: int) -> bool:
        """Сброс всех намазов пользователя"""
        async with await db_manager.get_connection() as db:
            await db.execute("DELETE FROM prayers WHERE user_id = ?", (user_id,))
            await db.commit()
            return True
    
    async def get_statistics(self) -> Dict:
        """Получение общей статистики"""
        async with await db_manager.get_connection() as db:
            # Общее количество пользователей с намазами
            cursor = await db.execute("""
                SELECT COUNT(DISTINCT user_id) as total_users FROM prayers
            """)
            total_users = (await cursor.fetchone())['total_users']
            
            # Статистика по типам намазов
            cursor = await db.execute("""
                SELECT prayer_type, 
                       SUM(total_missed) as total_missed,
                       SUM(completed) as total_completed,
                       SUM(total_missed - completed) as total_remaining
                FROM prayers 
                GROUP BY prayer_type
            """)
            prayer_stats = await cursor.fetchall()
            
            return {
                'total_users': total_users,
                'prayer_statistics': [dict(row) for row in prayer_stats]
            }
