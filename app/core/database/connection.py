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
            # Создание таблицы пользователей (исправленная структура)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
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
                    childbirth_data TEXT DEFAULT NULL,
                    daily_notifications_enabled INTEGER DEFAULT 1
                )
            """)
            
            # Добавляем поле daily_notifications_enabled если его нет (для существующих БД)
            try:
                await connection.execute("""
                    ALTER TABLE users ADD COLUMN daily_notifications_enabled INTEGER DEFAULT 1
                """)
                logger.info("Добавлено поле daily_notifications_enabled в таблицу users")
            except:
                # Поле уже существует
                pass
            
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
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id),
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
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
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
            
            # Создание индексов
            await connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)
            """)
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
            logger.info("База данных инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise
        finally:
            await connection.close()

# Создание глобального экземпляра
db_manager = DatabaseConnection()