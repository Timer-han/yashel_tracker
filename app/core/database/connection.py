import aiosqlite
import logging
from typing import Optional
from ..config import config

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Менеджер подключения к базе данных"""
    
    def __init__(self):
        self.db_path = config.DATABASE_URL.replace("sqlite:///", "")
    
    async def get_connection(self) -> aiosqlite.Connection:
        """Получение нового подключения к БД"""
        connection = await aiosqlite.connect(self.db_path)
        connection.row_factory = aiosqlite.Row
        return connection
    
    async def initialize_database(self):
        """Инициализация базы данных"""
        connection = await self.get_connection()
        try:
            # Создание таблицы пользователей
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    full_name TEXT,
                    gender TEXT,
                    birth_date DATE,
                    city TEXT,
                    role TEXT DEFAULT 'user',
                    is_registered BOOLEAN DEFAULT FALSE,
                    prayer_start_date DATE,
                    adult_date DATE,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Создание таблицы намазов
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS prayers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    prayer_type TEXT NOT NULL,
                    total_missed INTEGER DEFAULT 0,
                    completed INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, prayer_type)
                )
            """)
            
            # Создание таблицы истории намазов
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
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Создание таблицы администраторов
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

            # Создание таблицы для хайд
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

            # Создание таблицы для нифас
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

            # Создание таблицы для постов
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

            # Создание таблицы истории постов
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
            
            await connection.commit()
            logger.info("База данных инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise
        finally:
            await connection.close()

# Создание глобального экземпляра
db_manager = DatabaseConnection()