from typing import Optional, List
from datetime import date
from ..connection import db_manager
from ..models.user import User

class UserRepository:
    """Репозиторий для работы с пользователями"""
    
    async def create_user(self, user: User) -> Optional[int]:
        """Создание пользователя"""
        async with await db_manager.get_connection() as db:
            cursor = await db.execute("""
                INSERT INTO users (
                    telegram_id, username, first_name, last_name, full_name,
                    gender, birth_date, city, role, is_registered,
                    prayer_start_date, adult_date, last_activity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.telegram_id, user.username, user.first_name, user.last_name,
                user.full_name, user.gender, user.birth_date, user.city,
                user.role, user.is_registered, user.prayer_start_date,
                user.adult_date, user.last_activity
            ))
            await db.commit()
            return cursor.lastrowid
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получение пользователя по telegram_id"""
        async with await db_manager.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            
            return User(
                telegram_id=row['telegram_id'],
                username=row['username'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                full_name=row['full_name'],
                gender=row['gender'],
                birth_date=row['birth_date'],
                city=row['city'],
                role=row['role'],
                is_registered=row['is_registered'],
                prayer_start_date=row['prayer_start_date'],
                adult_date=row['adult_date']
            )
    
    async def update_user(self, telegram_id: int, **kwargs) -> bool:
        """Обновление пользователя"""
        if not kwargs:
            return False
            
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [telegram_id]
        
        async with await db_manager.get_connection() as db:
            await db.execute(f"""
                UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
            """, values)
            await db.commit()
            return True
    
    async def get_users_by_filters(self, gender: str = None, city: str = None, 
                                   min_age: int = None, max_age: int = None) -> List[User]:
        """Получение пользователей по фильтрам"""
        query = "SELECT * FROM users WHERE is_registered = TRUE"
        params = []
        
        if gender:
            query += " AND gender = ?"
            params.append(gender)
        
        if city:
            query += " AND city = ?"
            params.append(city)
        
        # Возраст будет рассчитываться в сервисе
        
        async with await db_manager.get_connection() as db:
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            users = []
            for row in rows:
                users.append(User(
                    telegram_id=row['telegram_id'],
                    username=row['username'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    full_name=row['full_name'],
                    gender=row['gender'],
                    birth_date=row['birth_date'],
                    city=row['city'],
                    role=row['role'],
                    is_registered=row['is_registered'],
                    prayer_start_date=row['prayer_start_date'],
                    adult_date=row['adult_date']
                ))
            return users
    
    async def get_all_registered_users(self) -> List[User]:
        """Получение всех зарегистрированных пользователей"""
        return await self.get_users_by_filters()
