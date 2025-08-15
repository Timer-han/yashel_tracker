from typing import List, Optional, Dict
from ..connection import db_manager
from ..models.fast import Fast

class FastRepository:
    """Репозиторий для работы с постами"""
    
    async def create_or_update_fast(self, user_id: int, fast_type: str, 
                                    year: Optional[int] = None,
                                    total_missed: int = 0, 
                                    completed: int = 0) -> bool:
        """Создание или обновление поста"""
        connection = await db_manager.get_connection()
        try:
            # Проверяем существующую запись
            if year:
                cursor = await connection.execute("""
                    SELECT id FROM fasts 
                    WHERE user_id = ? AND fast_type = ? AND year = ?
                """, (user_id, fast_type, year))
            else:
                cursor = await connection.execute("""
                    SELECT id FROM fasts 
                    WHERE user_id = ? AND fast_type = ? AND year IS NULL
                """, (user_id, fast_type))
            
            existing = await cursor.fetchone()
            
            if existing:
                # Обновляем существующую запись
                if year:
                    await connection.execute("""
                        UPDATE fasts 
                        SET total_missed = ?, completed = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ? AND fast_type = ? AND year = ?
                    """, (total_missed, completed, user_id, fast_type, year))
                else:
                    await connection.execute("""
                        UPDATE fasts 
                        SET total_missed = ?, completed = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ? AND fast_type = ? AND year IS NULL
                    """, (total_missed, completed, user_id, fast_type))
            else:
                # Создаем новую запись
                await connection.execute("""
                    INSERT INTO fasts (user_id, fast_type, year, total_missed, completed)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, fast_type, year, total_missed, completed))
            
            await connection.commit()
            return True
        finally:
            await connection.close()
    
    async def get_user_fasts(self, user_id: int) -> List[Fast]:
        """Получение всех постов пользователя"""
        connection = await db_manager.get_connection()
        try:
            cursor = await connection.execute("""
                SELECT * FROM fasts WHERE user_id = ?
                ORDER BY year DESC NULLS LAST, fast_type
            """, (user_id,))
            rows = await cursor.fetchall()
            
            fasts = []
            for row in rows:
                fasts.append(Fast(
                    user_id=row['user_id'],
                    fast_type=row['fast_type'],
                    year=row['year'],
                    total_missed=row['total_missed'],
                    completed=row['completed']
                ))
            return fasts
        finally:
            await connection.close()
    
    async def get_fast(self, user_id: int, fast_type: str, 
                       year: Optional[int] = None) -> Optional[Fast]:
        """Получение конкретного поста"""
        connection = await db_manager.get_connection()
        try:
            if year:
                cursor = await connection.execute("""
                    SELECT * FROM fasts 
                    WHERE user_id = ? AND fast_type = ? AND year = ?
                """, (user_id, fast_type, year))
            else:
                cursor = await connection.execute("""
                    SELECT * FROM fasts 
                    WHERE user_id = ? AND fast_type = ? AND year IS NULL
                """, (user_id, fast_type))
            
            row = await cursor.fetchone()
            if not row:
                return None
            
            return Fast(
                user_id=row['user_id'],
                fast_type=row['fast_type'],
                year=row['year'],
                total_missed=row['total_missed'],
                completed=row['completed']
            )
        finally:
            await connection.close()
    
    async def update_completed_fasts(self, user_id: int, fast_type: str, 
                                     amount: int, year: Optional[int] = None) -> bool:
        """Обновление количества совершенных постов"""
        connection = await db_manager.get_connection()
        try:
            if year:
                await connection.execute("""
                    UPDATE fasts 
                    SET completed = completed + ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND fast_type = ? AND year = ?
                """, (amount, user_id, fast_type, year))
            else:
                await connection.execute("""
                    UPDATE fasts 
                    SET completed = completed + ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND fast_type = ? AND year IS NULL
                """, (amount, user_id, fast_type))
            
            await connection.commit()
            return True
        finally:
            await connection.close()
    
    async def reset_user_fasts(self, user_id: int) -> bool:
        """Сброс всех постов пользователя"""
        connection = await db_manager.get_connection()
        try:
            await connection.execute("DELETE FROM fasts WHERE user_id = ?", (user_id,))
            await connection.commit()
            return True
        finally:
            await connection.close()
    
    async def get_statistics(self) -> Dict:
        """Получение общей статистики по постам"""
        connection = await db_manager.get_connection()
        try:
            # Общее количество пользователей с постами
            cursor = await connection.execute("""
                SELECT COUNT(DISTINCT user_id) as total_users FROM fasts
            """)
            total_users = (await cursor.fetchone())['total_users']
            
            # Статистика по типам постов
            cursor = await connection.execute("""
                SELECT fast_type, 
                       SUM(total_missed) as total_missed,
                       SUM(completed) as total_completed,
                       SUM(total_missed - completed) as total_remaining
                FROM fasts 
                GROUP BY fast_type
            """)
            fast_stats = await cursor.fetchall()
            
            return {
                'total_users': total_users,
                'fast_statistics': [dict(row) for row in fast_stats]
            }
        finally:
            await connection.close()