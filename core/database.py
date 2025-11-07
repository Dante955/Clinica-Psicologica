import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from core.config import settings

ROOT = Path(__file__).resolve().parents[1]
SQL_FILE = ROOT / "CLINICA PSICOLOGICA - SQLITE.txt"

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
    """Inicializa la base de datos si no existe leyendo el archivo de esquema."""
    if not SQL_FILE.exists():
        raise FileNotFoundError(f"No se encontró el fichero SQL de esquema: {SQL_FILE}")
    with open(SQL_FILE, "r", encoding="utf-8") as f:
        script = f.read()
    with get_db() as conn:
        conn.executescript(script)
    print("✅ Base de datos inicializada")