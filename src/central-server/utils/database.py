"""
Utilidades para manejo correcto de base de datos
"""

from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from models.database import get_db

@asynccontextmanager
async def get_db_session():
    """Context manager para manejo correcto de sesiones de base de datos"""
    db = next(get_db())
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def safe_db_operation(operation_func):
    """Decorator para operaciones seguras de base de datos"""
    async def wrapper(*args, **kwargs):
        async with get_db_session() as db:
            return await operation_func(db, *args, **kwargs)
    return wrapper
