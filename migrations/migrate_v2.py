import asyncio
import aiosqlite
import json
from datetime import datetime
import logging
import shutil
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def backup_database(db_path: str):
    """Создание резервной копии базы данных"""
    if not os.path.exists(db_path):
        logger.info(f"База данных {db_path} не существует, создание новой...")
        return None
        
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    logger.info(f"Создана резервная копия: {backup_path}")
    return backup_path

async def check_table_structure(connection: aiosqlite.Connection):
    """Проверка текущей структуры таблицы users"""
    try:
        cursor = await connection.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        logger.info(f"Текущие столбцы в таблице users: {column_names}")
        return column_names
    except Exception as e:
        logger.error(f"Ошибка при проверке структуры таблицы: {e}")
        return []

async def migrate_database(db_path: str):
    """Основная функция миграции"""
    
    # Создаем резервную копию
    backup_path = await backup_database(db_path)
    
    connection = await aiosqlite.connect(db_path)
    connection.row_factory = aiosqlite.Row
    
    try:
        # Проверяем текущую структуру
        current_columns = await check_table_structure(connection)
        
        # Определяем, нужна ли миграция
        unwanted_columns = ['first_name', 'last_name', 'full_name']
        needed_columns = ['fasting_missed_days', 'fasting_completed_days', 'hayd_average_days', 'childbirth_count', 'childbirth_data']
        
        needs_migration = (
            any(col in current_columns for col in unwanted_columns) or
            not all(col in current_columns for col in needed_columns)
        )
        
        if not needs_migration:
            logger.info("Миграция не требуется. База данных уже в актуальном состоянии.")
            await connection.close()
            return
        
        logger.info("Начинаем миграцию базы данных...")
        
        # Начинаем транзакцию
        await connection.execute("BEGIN TRANSACTION")
        
        # 1. Создаем новую таблицу users с правильной структурой
        logger.info("Создание новой таблицы users...")
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
        
        # 2. Копируем данные из старой таблицы
        logger.info("Копирование данных...")
        
        # Определяем общие поля
        common_fields = [
            'id', 'telegram_id', 'username', 'gender', 'birth_date', 'city', 
            'role', 'is_registered', 'prayer_start_date', 'adult_date', 
            'last_activity', 'created_at', 'updated_at'
        ]
        
        # Фильтруем только существующие поля
        existing_fields = [field for field in common_fields if field in current_columns]
        fields_str = ', '.join(existing_fields)
        
        await connection.execute(f"""
            INSERT INTO users_new ({fields_str}, fasting_missed_days, fasting_completed_days, hayd_average_days, childbirth_count, childbirth_data)
            SELECT {fields_str}, 0, 0, NULL, 0, NULL
            FROM users
        """)
        
        # 3. Обновляем данные для женщин (устанавливаем adult_date если его нет)
        logger.info("Обновление данных для пользователей...")
        
        cursor = await connection.execute("""
            SELECT telegram_id, gender, birth_date, adult_date
            FROM users_new WHERE is_registered = TRUE
        """)
        users = await cursor.fetchall()
        
        for user in users:
            if user['birth_date'] and not user['adult_date']:
                # Определяем возраст совершеннолетия в зависимости от пола
                adult_age = 9 if user['gender'] == 'female' else 12
                
                birth_date = datetime.strptime(user['birth_date'], "%Y-%m-%d").date()
                adult_date = birth_date.replace(year=birth_date.year + adult_age)
                
                await connection.execute("""
                    UPDATE users_new SET adult_date = ? WHERE telegram_id = ?
                """, (adult_date.isoformat(), user['telegram_id']))
        
        # 4. Удаляем старую таблицу и переименовываем новую
        await connection.execute("DROP TABLE users")
        await connection.execute("ALTER TABLE users_new RENAME TO users")
        
        # 5. Восстанавливаем индексы
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)
        """)
        
        # 6. Создаем недостающие таблицы если их нет
        logger.info("Проверка и создание остальных таблиц...")
        
        # Таблица намазов
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS prayers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                prayer_type TEXT NOT NULL,
                total_missed INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                UNIQUE(user_id, prayer_type)
            )
        """)
        
        # Таблица истории намазов
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS prayer_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                prayer_type TEXT NOT NULL,
                action TEXT NOT NULL,
                amount INTEGER NOT NULL,
                previous_value INTEGER NOT NULL,
                new_value INTEGER NOT NULL,
                comment TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        """)
        
        # Таблица администраторов
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                role TEXT NOT NULL,
                added_by INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Создаем индексы
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_prayers_user_id ON prayers(user_id)
        """)
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_prayer_history_user_id ON prayer_history(user_id)
        """)
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_admins_telegram_id ON admins(telegram_id)
        """)
        
        await connection.commit()
        logger.info("Миграция успешно завершена!")
        
        # Проверяем результат
        new_columns = await check_table_structure(connection)
        logger.info(f"Новая структура таблицы users: {new_columns}")
        
    except Exception as e:
        await connection.rollback()
        logger.error(f"Ошибка миграции: {e}")
        if backup_path:
            logger.info(f"Восстанавливаем из резервной копии: {backup_path}")
            shutil.copy2(backup_path, db_path)
        raise
    finally:
        await connection.close()

async def main():
    """Главная функция"""
    db_path = "data/yashel_tracker.db"  # Укажите путь к вашей БД
    
    # Создаем директорию data если её нет
    os.makedirs("data", exist_ok=True)
    
    await migrate_database(db_path)
    logger.info("Процесс миграции завершен!")

if __name__ == "__main__":
    asyncio.run(main())