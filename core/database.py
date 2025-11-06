import sqlite3
import uuid
from contextlib import contextmanager
from core.config import settings

@contextmanager
def get_db():
    """Context manager para conexiones SQLite"""
    conn = sqlite3.connect(settings.database_url.replace("sqlite:///", ""))
    conn.row_factory = sqlite3.Row  # Acceso por nombre de columna
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Inicializa la base de datos si no existe"""
    with open("clinica.sql", "r") as f:
        script = f.read()
    
    with get_db() as conn:
        conn.executescript(script)
    
    print("✅ Base de datos inicializada")