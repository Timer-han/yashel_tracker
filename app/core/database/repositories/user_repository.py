from typing import Optional, List
from datetime import date
from ..connection import db_manager
from ..models.user import User

class UserRepository:
    """Репозиторий для работы с пользователями"""
    
    async def create_user(self, user: User) -> Optional[int]:
        """Создание пользователя"""
        connection = await db_manager.get_connection()
        try:
            cursor = await connection.execute("""
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
            await connection.commit()
            return cursor.lastrowid
        finally:
            await connection.close()
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получение пользователя по telegram_id"""
        connection = await db_manager.get_connection()
        try:
            cursor = await connection.execute(
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
        finally:
            await connection.close()
    
    async def update_user(self, telegram_id: int, **kwargs) -> bool:
        """Обновление пользователя"""
        if not kwargs:
            return False
            
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [telegram_id]
        
        connection = await db_manager.get_connection()
        try:
            await connection.execute(f"""
                UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
            """, values)
            await connection.commit()
            return True
        finally:
            await connection.close()
    
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
        
        connection = await db_manager.get_connection()
        try:
            cursor = await connection.execute(query, params)
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
        finally:
            await connection.close()
    
    async def get_all_registered_users(self) -> List[User]:
        """Получение всех зарегистрированных пользователей"""
        return await self.get_users_by_filters()