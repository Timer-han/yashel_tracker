from typing import List, Optional
from ..connection import db_manager
from ..models.admin import Admin

class AdminRepository:
    """Репозиторий для работы с администраторами"""
    
    async def add_admin(self, admin: Admin) -> bool:
        """Добавление администратора"""
        async with await db_manager.get_connection() as db:
            try:
                await db.execute("""
                    INSERT INTO admins (telegram_id, role, added_by, is_active)
                    VALUES (?, ?, ?, ?)
                """, (admin.telegram_id, admin.role, admin.added_by, admin.is_active))
                await db.commit()
                return True
            except Exception:
                return False
    
    async def get_admin(self, telegram_id: int) -> Optional[Admin]:
        """Получение администратора по telegram_id"""
        async with await db_manager.get_connection() as db:
            cursor = await db.execute("""
                SELECT * FROM admins WHERE telegram_id = ? AND is_active = TRUE
            """, (telegram_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            
            return Admin(
                telegram_id=row['telegram_id'],
                role=row['role'],
                added_by=row['added_by'],
                is_active=row['is_active']
            )
    
    async def remove_admin(self, telegram_id: int) -> bool:
        """Удаление администратора"""
        async with await db_manager.get_connection() as db:
            await db.execute("""
                UPDATE admins SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
            """, (telegram_id,))
            await db.commit()
            return True
    
    async def get_all_admins(self) -> List[Admin]:
        """Получение всех активных администраторов"""
        async with await db_manager.get_connection() as db:
            cursor = await db.execute("""
                SELECT * FROM admins WHERE is_active = TRUE ORDER BY created_at
            """)
            rows = await cursor.fetchall()
            
            admins = []
            for row in rows:
                admins.append(Admin(
                    telegram_id=row['telegram_id'],
                    role=row['role'],
                    added_by=row['added_by'],
                    is_active=row['is_active']
                ))
            return admins
