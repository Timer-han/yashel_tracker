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
                    telegram_id, username, full_name,
                    gender, birth_date, city, role, is_registered,
                    prayer_start_date, adult_date, fasting_start_date,
                    has_childbirth, childbirth_count, last_activity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.telegram_id, user.username, user.full_name,
                user.gender, user.birth_date, user.city,
                user.role, user.is_registered, user.prayer_start_date,
                user.adult_date, user.fasting_start_date,
                user.has_childbirth, user.childbirth_count,
                user.last_activity
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
            
            # Обработка даты рождения
            birth_date = None
            if row['birth_date']:
                try:
                    birth_date = datetime.datetime.strptime(row['birth_date'], "%Y-%m-%d").date()
                except:
                    birth_date = None
            
            # Обработка даты начала намазов
            prayer_start_date = None
            if row['prayer_start_date']:
                try:
                    prayer_start_date = datetime.datetime.strptime(row['prayer_start_date'], "%Y-%m-%d").date()
                except:
                    prayer_start_date = None
            
            # Обработка даты совершеннолетия
            adult_date = None
            if row['adult_date']:
                try:
                    adult_date = datetime.datetime.strptime(row['adult_date'], "%Y-%m-%d").date()
                except:
                    adult_date = None
            
            # Обработка даты начала постов
            fasting_start_date = None
            if 'fasting_start_date' in row.keys() and row['fasting_start_date']:
                try:
                    fasting_start_date = datetime.datetime.strptime(row['fasting_start_date'], "%Y-%m-%d").date()
                except:
                    fasting_start_date = None
            
            return User(
                telegram_id=row['telegram_id'],
                username=row['username'],
                full_name=row['full_name'] if 'full_name' in row.keys() else None,
                gender=row['gender'],
                birth_date=birth_date,
                city=row['city'],
                role=row['role'],
                is_registered=row['is_registered'],
                prayer_start_date=prayer_start_date,
                adult_date=adult_date,
                fasting_start_date=fasting_start_date,
                has_childbirth=row['has_childbirth'] if 'has_childbirth' in row.keys() else False,
                childbirth_count=row['childbirth_count'] if 'childbirth_count' in row.keys() else 0
            )
        finally:
            await connection.close()
    
    async def update_user(self, telegram_id: int, **kwargs) -> bool:
        """Обновление пользователя"""
        if not kwargs:
            return False
        
        # Фильтруем только существующие поля
        valid_fields = [
            'username', 'full_name', 'gender', 'birth_date', 'city',
            'role', 'is_registered', 'prayer_start_date', 'adult_date',
            'fasting_start_date', 'has_childbirth', 'childbirth_count'
        ]
        
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        if not filtered_kwargs:
            return False
            
        set_clause = ", ".join([f"{key} = ?" for key in filtered_kwargs.keys()])
        values = list(filtered_kwargs.values()) + [telegram_id]
        
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
        
        if min_age is not None and max_age is not None:
            # Для фильтрации по возрасту нужно использовать даты рождения
            from datetime import date, timedelta
            today = date.today()
            max_birth_date = today - timedelta(days=min_age * 365)
            min_birth_date = today - timedelta(days=max_age * 365)
            
            query += " AND birth_date BETWEEN ? AND ?"
            params.extend([min_birth_date.isoformat(), max_birth_date.isoformat()])
        
        connection = await db_manager.get_connection()
        try:
            cursor = await connection.execute(query, params)
            rows = await cursor.fetchall()
            
            users = []
            for row in rows:
                # Обработка дат
                birth_date = None
                if row['birth_date']:
                    try:
                        birth_date = datetime.datetime.strptime(row['birth_date'], "%Y-%m-%d").date()
                    except:
                        birth_date = None
                
                prayer_start_date = None
                if row['prayer_start_date']:
                    try:
                        prayer_start_date = datetime.datetime.strptime(row['prayer_start_date'], "%Y-%m-%d").date()
                    except:
                        prayer_start_date = None
                
                adult_date = None
                if row['adult_date']:
                    try:
                        adult_date = datetime.datetime.strptime(row['adult_date'], "%Y-%m-%d").date()
                    except:
                        adult_date = None
                
                fasting_start_date = None
                if 'fasting_start_date' in row.keys() and row['fasting_start_date']:
                    try:
                        fasting_start_date = datetime.datetime.strptime(row['fasting_start_date'], "%Y-%m-%d").date()
                    except:
                        fasting_start_date = None
                
                users.append(User(
                    telegram_id=row['telegram_id'],
                    username=row['username'],
                    full_name=row['full_name'] if 'full_name' in row.keys() else row['username'],
                    gender=row['gender'],
                    birth_date=birth_date,
                    city=row['city'],
                    role=row['role'],
                    is_registered=row['is_registered'],
                    prayer_start_date=prayer_start_date,
                    adult_date=adult_date,
                    fasting_start_date=fasting_start_date,
                    has_childbirth=row['has_childbirth'] if 'has_childbirth' in row.keys() else False,
                    childbirth_count=row['childbirth_count'] if 'childbirth_count' in row.keys() else 0
                ))
            return users
        finally:
            await connection.close()
    
    async def get_all_registered_users(self) -> List[User]:
        """Получение всех зарегистрированных пользователей"""
        return await self.get_users_by_filters()
    
    async def delete_user(self, telegram_id: int) -> bool:
        """Удаление пользователя"""
        connection = await db_manager.get_connection()
        try:
            # Удаляем связанные данные
            await connection.execute("DELETE FROM prayers WHERE user_id = ?", (telegram_id,))
            await connection.execute("DELETE FROM prayer_history WHERE user_id = ?", (telegram_id,))
            await connection.execute("DELETE FROM fasts WHERE user_id = ?", (telegram_id,))
            await connection.execute("DELETE FROM fast_history WHERE user_id = ?", (telegram_id,))
            await connection.execute("DELETE FROM hayd_info WHERE user_id = ?", (telegram_id,))
            await connection.execute("DELETE FROM nifas_info WHERE user_id = ?", (telegram_id,))
            
            # Удаляем самого пользователя
            await connection.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
            
            await connection.commit()
            return True
        except Exception as e:
            await connection.rollback()
            return False
        finally:
            await connection.close()
    
    async def get_users_count(self) -> int:
        """Получение общего количества пользователей"""
        connection = await db_manager.get_connection()
        try:
            cursor = await connection.execute(
                "SELECT COUNT(*) as count FROM users WHERE is_registered = TRUE"
            )
            row = await cursor.fetchone()
            return row['count'] if row else 0
        finally:
            await connection.close()
    
    async def get_users_by_role(self, role: str) -> List[User]:
        """Получение пользователей по роли"""
        connection = await db_manager.get_connection()
        try:
            cursor = await connection.execute(
                "SELECT * FROM users WHERE role = ?", (role,)
            )
            rows = await cursor.fetchall()
            
            users = []
            for row in rows:
                # Обработка дат
                birth_date = None
                if row['birth_date']:
                    try:
                        birth_date = datetime.datetime.strptime(row['birth_date'], "%Y-%m-%d").date()
                    except:
                        birth_date = None
                
                users.append(User(
                    telegram_id=row['telegram_id'],
                    username=row['username'],
                    full_name=row['full_name'] if 'full_name' in row.keys() else row['username'],
                    gender=row['gender'],
                    birth_date=birth_date,
                    city=row['city'],
                    role=row['role'],
                    is_registered=row['is_registered']
                ))
            return users
        finally:
            await connection.close()