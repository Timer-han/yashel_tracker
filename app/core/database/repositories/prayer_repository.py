from typing import List, Optional, Dict
from ..connection import db_manager
from ..models.prayer import Prayer

class PrayerRepository:
    """Репозиторий для работы с намазами"""
    
    async def create_or_update_prayer(self, user_id: int, prayer_type: str, 
                                      total_missed: int = 0, completed: int = 0) -> bool:
        """Создание или обновление намаза"""
        connection = await db_manager.get_connection()
        try:
            # Сначала проверяем, существует ли запись
            cursor = await connection.execute("""
                SELECT id FROM prayers WHERE user_id = ? AND prayer_type = ?
            """, (user_id, prayer_type))
            existing = await cursor.fetchone()
            
            if existing:
                # Обновляем существующую запись
                await connection.execute("""
                    UPDATE prayers SET total_missed = ?, completed = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND prayer_type = ?
                """, (total_missed, completed, user_id, prayer_type))
            else:
                # Создаем новую запись
                await connection.execute("""
                    INSERT INTO prayers (user_id, prayer_type, total_missed, completed)
                    VALUES (?, ?, ?, ?)
                """, (user_id, prayer_type, total_missed, completed))
            
            await connection.commit()
            return True
        finally:
            await connection.close()
    
    async def get_user_prayers(self, user_id: int) -> List[Prayer]:
        """Получение всех намазов пользователя"""
        connection = await db_manager.get_connection()
        try:
            cursor = await connection.execute("""
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
        finally:
            await connection.close()
    
    async def get_prayer(self, user_id: int, prayer_type: str) -> Optional[Prayer]:
        """Получение конкретного намаза"""
        connection = await db_manager.get_connection()
        try:
            cursor = await connection.execute("""
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
        finally:
            await connection.close()
    
    async def update_completed_prayers(self, user_id: int, prayer_type: str, 
                                       amount: int) -> bool:
        """Обновление количества совершенных намазов"""
        connection = await db_manager.get_connection()
        try:
            await connection.execute("""
                UPDATE prayers SET completed = completed + ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND prayer_type = ?
            """, (amount, user_id, prayer_type))
            await connection.commit()
            return True
        finally:
            await connection.close()
    
    async def reset_user_prayers(self, user_id: int) -> bool:
        """Сброс всех намазов пользователя"""
        connection = await db_manager.get_connection()
        try:
            await connection.execute("DELETE FROM prayers WHERE user_id = ?", (user_id,))
            await connection.commit()
            return True
        finally:
            await connection.close()
    
    async def get_statistics(self) -> Dict:
        """Получение общей статистики"""
        connection = await db_manager.get_connection()
        try:
            # Общее количество пользователей с намазами
            cursor = await connection.execute("""
                SELECT COUNT(DISTINCT user_id) as total_users FROM prayers
            """)
            total_users = (await cursor.fetchone())['total_users']
            
            # Статистика по типам намазов
            cursor = await connection.execute("""
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
        finally:
            await connection.close()