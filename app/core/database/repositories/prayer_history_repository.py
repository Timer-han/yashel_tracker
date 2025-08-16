from typing import List
from ..connection import db_manager
from ..models.prayer_history import PrayerHistory

class PrayerHistoryRepository:
    """Репозиторий для работы с историей намазов"""
    
    async def add_history_record(self, history: PrayerHistory) -> bool:
        """Добавление записи в историю"""
        connection = await db_manager.get_connection()
        try:
            await connection.execute("""
                INSERT INTO prayer_history (
                    user_id, prayer_type, action, amount, 
                    previous_value, new_value, comment
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                history.user_id, history.prayer_type, history.action,
                history.amount, history.previous_value, history.new_value,
                history.comment
            ))
            await connection.commit()
            return True
        finally:
            await connection.close()
    
    async def get_user_history(self, user_id: int, limit: int = 50) -> List[PrayerHistory]:
        """Получение истории пользователя"""
        connection = await db_manager.get_connection()
        try:
            cursor = await connection.execute("""
                SELECT * FROM prayer_history 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (user_id, limit))
            rows = await cursor.fetchall()
            
            history = []
            for row in rows:
                history.append(PrayerHistory(
                    user_id=row['user_id'],
                    prayer_type=row['prayer_type'],
                    action=row['action'],
                    amount=row['amount'],
                    previous_value=row['previous_value'],
                    new_value=row['new_value'],
                    comment=row['comment']
                ))
            return history
        finally:
            await connection.close()