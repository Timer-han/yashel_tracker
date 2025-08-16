import asyncio
import aiosqlite
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def backup_database(db_path: str):
    """Создание резервной копии базы данных"""
    import shutil
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    logger.info(f"Создана резервная копия: {backup_path}")
    return backup_path

async def migrate_database(db_path: str):
    """Основная функция миграции"""
    
    # Создаем резервную копию
    await backup_database(db_path)
    
    connection = await aiosqlite.connect(db_path)
    connection.row_factory = aiosqlite.Row
    
    try:
        # Начинаем транзакцию
        await connection.execute("BEGIN TRANSACTION")
        
        # 1. Добавляем новые поля в таблицу users
        logger.info("Добавление новых полей в таблицу users...")
        
        # Поля для постов
        await connection.execute("""
            ALTER TABLE users ADD COLUMN fasting_missed_days INTEGER DEFAULT 0
        """)
        await connection.execute("""
            ALTER TABLE users ADD COLUMN fasting_completed_days INTEGER DEFAULT 0  
        """)
        
        # Поля для хайда/нифаса (только для женщин)
        await connection.execute("""
            ALTER TABLE users ADD COLUMN hayd_average_days REAL DEFAULT NULL
        """)
        await connection.execute("""
            ALTER TABLE users ADD COLUMN childbirth_count INTEGER DEFAULT 0
        """)
        await connection.execute("""
            ALTER TABLE users ADD COLUMN childbirth_data TEXT DEFAULT NULL
        """)
        
        # 2. Удаляем ненужные поля (SQLite не поддерживает DROP COLUMN напрямую)
        logger.info("Реструктуризация таблицы users...")
        
        # Создаем новую таблицу без ненужных полей
        await connection.execute("""
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                gender TEXT,
                birth_date DATE,
                city TEXT,
                role TEXT DEFAULT 'user',
                is_registered BOOLEAN DEFAULT FALSE,
                prayer_start_date DATE,
                adult_date DATE,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                fasting_missed_days INTEGER DEFAULT 0,
                fasting_completed_days INTEGER DEFAULT 0,
                hayd_average_days REAL DEFAULT NULL,
                childbirth_count INTEGER DEFAULT 0,
                childbirth_data TEXT DEFAULT NULL
            )
        """)
        
        # Копируем данные
        await connection.execute("""
            INSERT INTO users_new (
                id, telegram_id, username, gender, birth_date, city, role,
                is_registered, prayer_start_date, adult_date, last_activity,
                created_at, updated_at, fasting_missed_days, fasting_completed_days,
                hayd_average_days, childbirth_count, childbirth_data
            )
            SELECT 
                id, telegram_id, username, gender, birth_date, city, role,
                is_registered, prayer_start_date, adult_date, last_activity,
                created_at, updated_at, 0, 0, NULL, 0, NULL
            FROM users
        """)
        
        # Удаляем старую таблицу и переименовываем новую
        await connection.execute("DROP TABLE users")
        await connection.execute("ALTER TABLE users_new RENAME TO users")
        
        # Восстанавливаем индексы
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)
        """)
        
        # 3. Пересчитываем данные для существующих пользователей
        logger.info("Пересчет данных для существующих пользователей...")
        
        cursor = await connection.execute("""
            SELECT telegram_id, gender, birth_date, prayer_start_date
            FROM users WHERE is_registered = TRUE
        """)
        users = await cursor.fetchall()
        
        for user in users:
            if user['birth_date'] and user['prayer_start_date']:
                # Определяем возраст совершеннолетия в зависимости от пола
                adult_age = 9 if user['gender'] == 'female' else 12
                
                # Обновляем adult_date если его нет
                birth_date = datetime.strptime(user['birth_date'], "%Y-%m-%d").date()
                adult_date = birth_date.replace(year=birth_date.year + adult_age)
                
                await connection.execute("""
                    UPDATE users SET adult_date = ? WHERE telegram_id = ?
                """, (adult_date.isoformat(), user['telegram_id']))
        
        await connection.commit()
        logger.info("Миграция успешно завершена!")
        
    except Exception as e:
        await connection.rollback()
        logger.error(f"Ошибка миграции: {e}")
        raise
    finally:
        await connection.close()

if __name__ == "__main__":
    db_path = "data/yashel_tracker.db"  # Укажите путь к вашей БД
    asyncio.run(migrate_database(db_path))