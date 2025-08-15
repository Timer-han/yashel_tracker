#!/usr/bin/env python3
"""
Скрипт миграции существующих данных на новую структуру БД
"""

import asyncio
import aiosqlite
import logging
from datetime import date
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import config
from app.core.database.connection import db_manager
from app.core.services.enhanced_calculation_service import EnhancedCalculationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_database():
    """Основная функция миграции"""
    
    logger.info("Начало миграции базы данных...")
    
    db_path = config.DATABASE_URL.replace("sqlite:///", "")
    logger.info(db_path)
    logger.info(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    connection = await aiosqlite.connect(db_path)
    connection.row_factory = aiosqlite.Row
    
    try:
        # 1. Проверяем существование старых полей
        cursor = await connection.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        column_names = [col['name'] for col in columns]
        
        has_first_name = 'first_name' in column_names
        has_last_name = 'last_name' in column_names
        has_fasting_start_date = 'fasting_start_date' in column_names
        
        # 2. Если есть старые поля, мигрируем данные
        if has_first_name and has_last_name and not has_fasting_start_date:
            logger.info("Обнаружена старая структура БД. Начинаем миграцию...")
            
            # Сохраняем данные о пользователях
            cursor = await connection.execute("SELECT * FROM users")
            users = await cursor.fetchall()
            
            # Создаем временную таблицу с новой структурой
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS users_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    full_name TEXT,
                    gender TEXT,
                    birth_date DATE,
                    city TEXT,
                    role TEXT DEFAULT 'user',
                    is_registered BOOLEAN DEFAULT FALSE,
                    prayer_start_date DATE,
                    adult_date DATE,
                    fasting_start_date DATE,
                    has_childbirth BOOLEAN DEFAULT FALSE,
                    childbirth_count INTEGER DEFAULT 0,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Переносим данные
            for user in users:
                full_name = user['full_name']
                if not full_name or full_name == '':
                    # Формируем full_name из first_name и last_name
                    first = user['first_name'] or ''
                    last = user['last_name'] or ''
                    full_name = f"{first} {last}".strip() or None
                
                await connection.execute("""
                    INSERT INTO users_new (
                        id, telegram_id, username, full_name, gender, birth_date,
                        city, role, is_registered, prayer_start_date, adult_date,
                        last_activity, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user['id'], user['telegram_id'], user['username'],
                    full_name, user['gender'], user['birth_date'],
                    user['city'], user['role'], user['is_registered'],
                    user['prayer_start_date'], user['adult_date'],
                    user['last_activity'], user['created_at'], user['updated_at']
                ))
            
            # Удаляем старую таблицу и переименовываем новую
            await connection.execute("DROP TABLE users")
            await connection.execute("ALTER TABLE users_new RENAME TO users")
            
            logger.info(f"Мигрировано {len(users)} пользователей")
        
        # 3. Создаем новые таблицы если их нет
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS hayd_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                average_duration INTEGER NOT NULL,
                period_number INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, period_number)
            )
        """)
        
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS nifas_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                childbirth_number INTEGER NOT NULL,
                childbirth_date DATE NOT NULL,
                nifas_duration INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, childbirth_number)
            )
        """)
        
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS fasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                fast_type TEXT NOT NULL,
                year INTEGER,
                total_missed INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, fast_type, year)
            )
        """)
        
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS fast_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                fast_type TEXT NOT NULL,
                action TEXT NOT NULL,
                amount INTEGER NOT NULL,
                previous_value INTEGER NOT NULL,
                new_value INTEGER NOT NULL,
                comment TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # 4. Пересчитываем намазы для существующих пользователей с учетом пола
        logger.info("Пересчет намазов с учетом пола...")
        
        calc_service = EnhancedCalculationService()
        cursor = await connection.execute("""
            SELECT telegram_id, gender, birth_date, prayer_start_date 
            FROM users 
            WHERE is_registered = TRUE AND prayer_start_date IS NOT NULL
        """)
        users_to_recalc = await cursor.fetchall()
        
        for user in users_to_recalc:
            if user['birth_date'] and user['prayer_start_date']:
                # Получаем правильный возраст совершеннолетия по полу
                gender = user['gender'] or 'male'
                adult_age = calc_service.get_adult_age_by_gender(gender)
                
                birth_date = date.fromisoformat(user['birth_date'])
                prayer_start_date = date.fromisoformat(user['prayer_start_date'])
                adult_date = birth_date.replace(year=birth_date.year + adult_age)
                
                # Пересчитываем намазы
                prayers_data = calc_service.calculate_prayers_between_dates(adult_date, prayer_start_date)
                
                # Обновляем данные намазов
                for prayer_type, count in prayers_data.items():
                    if count > 0:
                        # Проверяем существующие данные
                        cursor = await connection.execute("""
                            SELECT * FROM prayers 
                            WHERE user_id = ? AND prayer_type = ?
                        """, (user['telegram_id'], prayer_type))
                        existing = await cursor.fetchone()
                        
                        if existing:
                            # Обновляем только total_missed, сохраняя completed
                            await connection.execute("""
                                UPDATE prayers 
                                SET total_missed = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE user_id = ? AND prayer_type = ?
                            """, (count, user['telegram_id'], prayer_type))
                        else:
                            # Создаем новую запись
                            await connection.execute("""
                                INSERT INTO prayers (user_id, prayer_type, total_missed, completed)
                                VALUES (?, ?, ?, 0)
                            """, (user['telegram_id'], prayer_type, count))
                
                logger.info(f"Пересчитаны намазы для пользователя {user['telegram_id']}")
        
        # 5. Создаем индексы
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_hayd_info_user_id ON hayd_info(user_id)")
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_nifas_info_user_id ON nifas_info(user_id)")
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_fasts_user_id ON fasts(user_id)")
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_fast_history_user_id ON fast_history(user_id)")
        
        await connection.commit()
        logger.info("Миграция завершена успешно!")
        
    except Exception as e:
        logger.error(f"Ошибка при миграции: {e}")
        await connection.rollback()
        raise
    finally:
        await connection.close()

async def main():
    """Точка входа"""
    try:
        await migrate_database()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())