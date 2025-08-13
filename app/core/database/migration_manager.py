import aiosqlite
import logging
import os
from typing import List
from ..config import config

logger = logging.getLogger(__name__)

class MigrationManager:
    """Менеджер миграций базы данных"""
    
    def __init__(self):
        self.migrations_dir = "migrations"
        self.db_path = config.DATABASE_URL.replace("sqlite:///", "")
    
    async def get_connection(self) -> aiosqlite.Connection:
        """Получение подключения к БД"""
        connection = await aiosqlite.connect(self.db_path)
        connection.row_factory = aiosqlite.Row
        return connection
    
    async def create_migrations_table(self):
        """Создание таблицы миграций"""
        connection = await self.get_connection()
        try:
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE NOT NULL,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await connection.commit()
        finally:
            await connection.close()
    
    async def get_applied_migrations(self) -> List[str]:
        """Получение списка примененных миграций"""
        connection = await self.get_connection()
        try:
            cursor = await connection.execute("SELECT filename FROM migrations ORDER BY id")
            rows = await cursor.fetchall()
            return [row['filename'] for row in rows]
        except:
            return []
        finally:
            await connection.close()
    
    async def apply_migration(self, filename: str):
        """Применение одной миграции"""
        filepath = os.path.join(self.migrations_dir, filename)
        
        if not os.path.exists(filepath):
            logger.error(f"Файл миграции не найден: {filepath}")
            return False
        
        connection = await self.get_connection()
        try:
            # Читаем содержимое файла миграции
            with open(filepath, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            # Разбиваем на отдельные команды
            commands = [cmd.strip() for cmd in migration_sql.split(';') if cmd.strip()]
            
            # Выполняем каждую команду отдельно
            for command in commands:
                try:
                    await connection.execute(command)
                except Exception as e:
                    # Игнорируем ошибки типа "column already exists" или "table already exists"
                    error_msg = str(e).lower()
                    if any(phrase in error_msg for phrase in [
                        "already exists", "duplicate column", "duplicate table",
                        "no such column", "table users_old already exists"
                    ]):
                        logger.warning(f"Пропускаем ожидаемую ошибку: {e}")
                        continue
                    else:
                        raise e
            
            # Записываем в таблицу миграций
            await connection.execute(
                "INSERT OR IGNORE INTO migrations (filename) VALUES (?)", 
                (filename,)
            )
            
            await connection.commit()
            logger.info(f"Миграция применена: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка применения миграции {filename}: {e}")
            await connection.rollback()
            return False
        finally:
            await connection.close()
    
    async def run_migrations(self):
        """Запуск всех неприменённых миграций"""
        await self.create_migrations_table()
        
        if not os.path.exists(self.migrations_dir):
            logger.info("Директория миграций не найдена")
            return
        
        # Получаем список всех файлов миграций
        migration_files = [f for f in os.listdir(self.migrations_dir) if f.endswith('.sql')]
        migration_files.sort()
        
        # Получаем примененные миграции
        applied = await self.get_applied_migrations()
        
        # Применяем новые миграции
        for filename in migration_files:
            if filename not in applied:
                logger.info(f"Применяем миграцию: {filename}")
                success = await self.apply_migration(filename)
                if not success:
                    logger.error(f"Не удалось применить миграцию: {filename}")
                    break
        
        logger.info("Миграции завершены")

# Создание глобального экземпляра
migration_manager = MigrationManager()