from typing import Optional, List
import datetime
from ..connection import db_manager
from ..models.user import User
import json

class UserRepository:
    """Репозиторий для работы с пользователями"""
    
    async def create_user(self, user: User) -> Optional[int]:
        """Создание пользователя"""
        connection = await db_manager.get_connection()
        try:
            # Сначала проверим, какие столбцы существуют в таблице
            cursor = await connection.execute("PRAGMA table_info(users)")
            columns_info = await cursor.fetchall()
            existing_columns = {col['name'] for col in columns_info}
            
            # Базовые поля, которые должны быть всегда
            base_fields = [
                'telegram_id', 'username', 'birth_date', 'city', 'role', 
                'is_registered', 'prayer_start_date', 'adult_date', 'last_activity'
            ]
            base_values = [
                user.telegram_id, user.username, user.birth_date, user.city,
                user.role, user.is_registered, user.prayer_start_date,
                user.adult_date, user.last_activity
            ]
            
            # Новые поля (могут отсутствовать в старых БД)
            if 'gender' in existing_columns:
                base_fields.append('gender')
                base_values.append(user.gender)
            
            if 'childbirth_count' in existing_columns:
                base_fields.extend(['childbirth_count', 'childbirths', 'hyde_periods', 'nifas_lengths'])
                base_values.extend([
                    user.childbirth_count,
                    user.childbirths_to_json(),
                    user.hyde_periods_to_json(),
                    user.nifas_lengths_to_json()
                ])
            
            # Создаем динамический запрос
            placeholders = ', '.join(['?' for _ in base_fields])
            fields_str = ', '.join(base_fields)
            
            cursor = await connection.execute(f"""
                INSERT INTO users ({fields_str}) VALUES ({placeholders})
            """, base_values)
            
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
            
            # Обрабатываем birth_date
            birth_date = None
            if row['birth_date']:
                try:
                    birth_date = datetime.datetime.strptime(row['birth_date'], "%Y-%m-%d").date()
                except:
                    pass
            
            # Безопасное получение полей с проверкой на существование
            def safe_get(field_name, default_value):
                try:
                    return row[field_name] if field_name in row.keys() else default_value
                except (KeyError, IndexError):
                    return default_value
            
            return User(
                telegram_id=row['telegram_id'],
                username=row['username'],
                gender=safe_get('gender', None),
                childbirth_count=safe_get('childbirth_count', 0),
                childbirths=User.from_json_childbirths(safe_get('childbirths', '[]')),
                hyde_periods=User.from_json_periods(safe_get('hyde_periods', '[]')),
                nifas_lengths=User.from_json_periods(safe_get('nifas_lengths', '[]')),
                birth_date=birth_date,
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
                # Безопасное получение полей
                def safe_get(field_name, default_value):
                    try:
                        return row[field_name] if field_name in row.keys() else default_value
                    except (KeyError, IndexError):
                        return default_value
                
                # Обрабатываем birth_date
                birth_date = None
                if row['birth_date']:
                    try:
                        birth_date = datetime.datetime.strptime(row['birth_date'], "%Y-%m-%d").date()
                    except:
                        pass
                
                users.append(User(
                    telegram_id=row['telegram_id'],
                    username=row['username'],
                    gender=safe_get('gender', None),
                    childbirth_count=safe_get('childbirth_count', 0),
                    childbirths=User.from_json_childbirths(safe_get('childbirths', '[]')),
                    hyde_periods=User.from_json_periods(safe_get('hyde_periods', '[]')),
                    nifas_lengths=User.from_json_periods(safe_get('nifas_lengths', '[]')),
                    birth_date=birth_date,
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