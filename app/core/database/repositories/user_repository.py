from typing import Optional, List
import datetime
from ..connection import db_manager
from ..models.user import User
import logging
logger = logging.getLogger(__name__)

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
            
            logger.info(f"Получен пользователь: {dict(row)}")

            dict_row = dict(row)
            
            return User(
                telegram_id=row['telegram_id'],
                username=row['username'],
                gender=row['gender'],
                birth_date=datetime.datetime.strptime(row['birth_date'], "%Y-%m-%d").date() if row['birth_date'] else None,
                city=row['city'],
                role=row['role'],
                is_registered=bool(row['is_registered']),
                prayer_start_date=datetime.datetime.strptime(row['prayer_start_date'], "%Y-%m-%d").date() if row['prayer_start_date'] else None,
                adult_date=datetime.datetime.strptime(row['adult_date'], "%Y-%m-%d").date() if row['adult_date'] else None,
                fasting_missed_days=dict_row.get('fasting_missed_days', 0),
                fasting_completed_days=dict_row.get('fasting_completed_days', 0),
                hayd_average_days=dict_row.get('hayd_average_days'),
                childbirth_count=dict_row.get('childbirth_count', 0),
                childbirth_data=dict_row.get('childbirth_data')

                # fasting_missed_days=row['fasting_missed_days'] if 'fasting_missed_days' in row and row['fasting_missed_days'] else 0,
                # fasting_completed_days=row['fasting_completed_days'] if 'fasting_completed_days' in row and row['fasting_completed_days'] else 0,
                # hayd_average_days=row['hayd_average_days'] if 'hayd_average_days' in row and row['hayd_average_days'] else None,
                # childbirth_count=row['childbirth_count'] if 'childbirth_count' in row and row['childbirth_count'] else 0,
                # childbirth_data=row['childbirth_data'] if 'childbirth_data' in row and row['childbirth_data'] else None
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
        
        # Добавляем updated_at
        kwargs['updated_at'] = datetime.datetime.now().isoformat()
            
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [telegram_id]
        
        connection = await db_manager.get_connection()
        try:
            await connection.execute(f"""
                UPDATE users SET {set_clause}
                WHERE telegram_id = ?
            """, values)
            await connection.commit()
            return True
        finally:
            await connection.close()
    

                    # fasting_missed_days=dict_row.get('fasting_missed_days', 0),
                    # fasting_completed_days=dict_row.get('fasting_completed_days', 0),
                    # hayd_average_days=dict_row.get('hayd_average_days'),
                    # childbirth_count=dict_row.get('childbirth_count', 0),
                    # childbirth_data=dict_row.get('childbirth_data')
    async def get_users_by_filters(self, gender: str = None, city: str = None, 
                                   min_age: int = None, max_age: int = None) -> List[User]:
        """Получение пользователей по фильтрам"""
        import logging
        logger = logging.getLogger(__name__)
        
        query = "SELECT * FROM users WHERE is_registered = TRUE"
        params = []
        
        logger.info(f"Начальный запрос: {query}")
        
        if gender:
            query += " AND gender = ?"
            params.append(gender)
            logger.info(f"Добавлен фильтр по полу: {gender}")
        
        if city:
            query += " AND city LIKE ?"
            params.append(f"%{city}%")
            logger.info(f"Добавлен фильтр по городу: {city}")
        
        logger.info(f"Финальный запрос: {query}")
        logger.info(f"Параметры: {params}")
        
        connection = await db_manager.get_connection()
        try:
            cursor = await connection.execute(query, params)
            rows = await cursor.fetchall()
            
            logger.info(f"Найдено пользователей в БД (до фильтрации по возрасту): {len(rows)}")
            
            users = []
            for row in rows:
                try:
                    dict_row = dict(row)
                    user = User(
                        telegram_id=row['telegram_id'],
                        username=row['username'],
                        gender=row['gender'],
                        birth_date=datetime.datetime.strptime(row['birth_date'], "%Y-%m-%d").date() if row['birth_date'] else None,
                        city=row['city'],
                        role=row['role'],
                        is_registered=bool(row['is_registered']),
                        prayer_start_date=datetime.datetime.strptime(row['prayer_start_date'], "%Y-%m-%d").date() if row['prayer_start_date'] else None,
                        adult_date=datetime.datetime.strptime(row['adult_date'], "%Y-%m-%d").date() if row['adult_date'] else None,
                        fasting_missed_days=dict_row.get('fasting_missed_days', 0),
                        fasting_completed_days=dict_row.get('fasting_completed_days', 0),
                        hayd_average_days=dict_row.get('hayd_average_days'),
                        childbirth_count=dict_row.get('childbirth_count', 0),
                        childbirth_data=dict_row.get('childbirth_data')
                    )
                    
                    # Фильтрация по возрасту на уровне Python
                    if (min_age is not None or max_age is not None) and user.birth_date:
                        from ...services.calculation_service import CalculationService
                        calc_service = CalculationService()
                        age = calc_service.calculate_age(user.birth_date)
                        
                        logger.debug(f"Пользователь {user.telegram_id}: возраст {age}")
                        
                        if min_age is not None and age < min_age:
                            logger.debug(f"Пользователь {user.telegram_id} исключен: возраст {age} < {min_age}")
                            continue
                        if max_age is not None and age > max_age:
                            logger.debug(f"Пользователь {user.telegram_id} исключен: возраст {age} > {max_age}")
                            continue
                    
                    users.append(user)
                    logger.debug(f"Добавлен пользователь {user.telegram_id}: {user.gender}, {user.city}")
                    
                except Exception as e:
                    logger.error(f"Ошибка обработки пользователя {row.get('telegram_id', 'unknown')}: {e}")
                    continue
                
            logger.info(f"Итого пользователей после всех фильтров: {len(users)}")
            return users
            
        except Exception as e:
            logger.error(f"Ошибка в get_users_by_filters: {e}", exc_info=True)
            return []
        finally:
            await connection.close()

    
    async def get_all_registered_users(self) -> List[User]:
        """Получение всех зарегистрированных пользователей"""
        return await self.get_users_by_filters()
