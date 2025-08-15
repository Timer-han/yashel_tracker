from typing import List, Optional
from datetime import date
from ..connection import db_manager
from ..models.hayd import HaydInfo
from ..models.nifas import NifasInfo

class FemalePeriodsRepository:
    """Репозиторий для работы с женскими периодами"""
    
    async def save_hayd_info(self, hayd_info: HaydInfo) -> bool:
        """Сохранение информации о хайд"""
        connection = await db_manager.get_connection()
        try:
            # Проверяем существующую запись
            cursor = await connection.execute("""
                SELECT id FROM hayd_info 
                WHERE user_id = ? AND period_number = ?
            """, (hayd_info.user_id, hayd_info.period_number))
            existing = await cursor.fetchone()
            
            if existing:
                await connection.execute("""
                    UPDATE hayd_info 
                    SET average_duration = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND period_number = ?
                """, (hayd_info.average_duration, hayd_info.user_id, hayd_info.period_number))
            else:
                await connection.execute("""
                    INSERT INTO hayd_info (user_id, average_duration, period_number)
                    VALUES (?, ?, ?)
                """, (hayd_info.user_id, hayd_info.average_duration, hayd_info.period_number))
            
            await connection.commit()
            return True
        finally:
            await connection.close()
    
    async def get_hayd_info(self, user_id: int, period_number: int = 0) -> Optional[HaydInfo]:
        """Получение информации о хайд для периода"""
        connection = await db_manager.get_connection()
        try:
            cursor = await connection.execute("""
                SELECT * FROM hayd_info 
                WHERE user_id = ? AND period_number = ?
            """, (user_id, period_number))
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            return HaydInfo(
                user_id=row['user_id'],
                average_duration=row['average_duration'],
                period_number=row['period_number']
            )
        finally:
            await connection.close()
    
    async def get_all_hayd_info(self, user_id: int) -> List[HaydInfo]:
        """Получение всей информации о хайд пользователя"""
        connection = await db_manager.get_connection()
        try:
            cursor = await connection.execute("""
                SELECT * FROM hayd_info 
                WHERE user_id = ? 
                ORDER BY period_number
            """, (user_id,))
            rows = await cursor.fetchall()
            
            return [
                HaydInfo(
                    user_id=row['user_id'],
                    average_duration=row['average_duration'],
                    period_number=row['period_number']
                )
                for row in rows
            ]
        finally:
            await connection.close()
    
    async def save_nifas_info(self, nifas_info: NifasInfo) -> bool:
        """Сохранение информации о нифас"""
        connection = await db_manager.get_connection()
        try:
            # Проверяем существующую запись
            cursor = await connection.execute("""
                SELECT id FROM nifas_info 
                WHERE user_id = ? AND childbirth_number = ?
            """, (nifas_info.user_id, nifas_info.childbirth_number))
            existing = await cursor.fetchone()
            
            if existing:
                await connection.execute("""
                    UPDATE nifas_info 
                    SET childbirth_date = ?, nifas_duration = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND childbirth_number = ?
                """, (
                    nifas_info.childbirth_date, 
                    nifas_info.nifas_duration,
                    nifas_info.user_id, 
                    nifas_info.childbirth_number
                ))
            else:
                await connection.execute("""
                    INSERT INTO nifas_info (user_id, childbirth_number, childbirth_date, nifas_duration)
                    VALUES (?, ?, ?, ?)
                """, (
                    nifas_info.user_id, 
                    nifas_info.childbirth_number,
                    nifas_info.childbirth_date, 
                    nifas_info.nifas_duration
                ))
            
            await connection.commit()
            return True
        finally:
            await connection.close()
    
    async def get_nifas_info(self, user_id: int, childbirth_number: int) -> Optional[NifasInfo]:
        """Получение информации о конкретном нифас"""
        connection = await db_manager.get_connection()
        try:
            cursor = await connection.execute("""
                SELECT * FROM nifas_info 
                WHERE user_id = ? AND childbirth_number = ?
            """, (user_id, childbirth_number))
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            return NifasInfo(
                user_id=row['user_id'],
                childbirth_number=row['childbirth_number'],
                childbirth_date=date.fromisoformat(row['childbirth_date']),
                nifas_duration=row['nifas_duration']
            )
        finally:
            await connection.close()
    
    async def get_all_nifas_info(self, user_id: int) -> List[NifasInfo]:
        """Получение всей информации о нифас пользователя"""
        connection = await db_manager.get_connection()
        try:
            cursor = await connection.execute("""
                SELECT * FROM nifas_info 
                WHERE user_id = ? 
                ORDER BY childbirth_number
            """, (user_id,))
            rows = await cursor.fetchall()
            
            return [
                NifasInfo(
                    user_id=row['user_id'],
                    childbirth_number=row['childbirth_number'],
                    childbirth_date=date.fromisoformat(row['childbirth_date']),
                    nifas_duration=row['nifas_duration']
                )
                for row in rows
            ]
        finally:
            await connection.close()
    
    async def delete_all_periods_info(self, user_id: int) -> bool:
        """Удаление всей информации о периодах пользователя"""
        connection = await db_manager.get_connection()
        try:
            await connection.execute("DELETE FROM hayd_info WHERE user_id = ?", (user_id,))
            await connection.execute("DELETE FROM nifas_info WHERE user_id = ?", (user_id,))
            await connection.commit()
            return True
        finally:
            await connection.close()