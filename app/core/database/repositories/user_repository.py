from typing import Optional, List
import datetime
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
                    telegram_id, username, gender, birth_date, city, role, 
                    is_registered, prayer_start_date, adult_date, last_activity,
                    fasting_missed_days, fasting_completed_days,
                    hayd_average_days, childbirth_count, childbirth_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.telegram_id, user.username, user.gender, 
                user.birth_date.isoformat() if user.birth_date else None,
                user.city, user.role, user.is_registered, 
                user.prayer_start_date.isoformat() if user.prayer_start_date else None,
                user.adult_date.isoformat() if user.adult_date else None,
                user.last_activity,
                user.fasting_missed_days, user.fasting_completed_days,
                user.hayd_average_days, user.childbirth_count, user.childbirth_data
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
                gender=row['gender'],
                birth_date=datetime.datetime.strptime(row['birth_date'], "%Y-%m-%d").date() if row['birth_date'] else None,
                city=row['city'],
                role=row['role'],
                is_registered=row['is_registered'],
                prayer_start_date=datetime.datetime.strptime(row['prayer_start_date'], "%Y-%m-%d").date() if row['prayer_start_date'] else None,
                adult_date=datetime.datetime.strptime(row['adult_date'], "%Y-%m-%d").date() if row['adult_date'] else None,
                fasting_missed_days=row['fasting_missed_days'] if 'fasting_missed_days' in row and row['fasting_missed_days'] else 0,
                fasting_completed_days=row['fasting_completed_days'] if 'fasting_completed_days' in row and row['fasting_completed_days'] else 0,
                hayd_average_days=row['hayd_average_days'] if 'hayd_average_days' in row and row['hayd_average_days'] else None,
                childbirth_count=row['childbirth_count'] if 'childbirth_count' in row and row['childbirth_count'] else 0,
                childbirth_data=row['childbirth_data'] if 'childbirth_data' in row and row['childbirth_data'] else '\{\}'
            )
        finally:
            await connection.close()
    
    async def update_user(self, telegram_id: int, **kwargs) -> bool:
        """Обновление пользователя"""
        if not kwargs:
            return False
        
        # Преобразуем даты в строки для БД
        for key in ['birth_date', 'prayer_start_date', 'adult_date']:
            if key in kwargs and kwargs[key] is not None:
                if hasattr(kwargs[key], 'isoformat'):
                    kwargs[key] = kwargs[key].isoformat()
            
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
                    gender=row['gender'],
                    birth_date=datetime.datetime.strptime(row['birth_date'], "%Y-%m-%d").date() if row['birth_date'] else None,
                    city=row['city'],
                    role=row['role'],
                    is_registered=row['is_registered'],
                    prayer_start_date=datetime.datetime.strptime(row['prayer_start_date'], "%Y-%m-%d").date() if row['prayer_start_date'] else None,
                    adult_date=datetime.datetime.strptime(row['adult_date'], "%Y-%m-%d").date() if row['adult_date'] else None,
                    fasting_missed_days=row['fasting_missed_days'] if 'fasting_missed_days' in row and row['fasting_missed_days'] else 0,
                    fasting_completed_days=row['fasting_completed_days'] if 'fasting_completed_days' in row and row['fasting_completed_days'] else 0,
                    hayd_average_days=row['hayd_average_days'] if 'hayd_average_days' in row and row['hayd_average_days'] else None,
                    childbirth_count=row['childbirth_count'] if 'childbirth_count' in row and row['childbirth_count'] else 0,
                    childbirth_data=row['childbirth_data'] if 'childbirth_data' in row and row['childbirth_data'] else '\{\}'
                ))
            return users
        finally:
            await connection.close()
    
    async def get_all_registered_users(self) -> List[User]:
        """Получение всех зарегистрированных пользователей"""
        return await self.get_users_by_filters()