import contextlib
import configparser
import os
import sys
import logging
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# --- Configuración de la Base de Datos ---

def get_database_url():
    """
    Lee la configuración desde config.ini y retorna la URL de conexión apropiada.
    Soporta SQLite, PostgreSQL y SQL Server (MSSQL).
    """
    config = configparser.ConfigParser()
    
    # Determinar la ruta correcta de config.ini
    if getattr(sys, 'frozen', False):
        # Si ejecutamos como .exe con PyInstaller, buscamos config.ini
        # en el mismo directorio donde está el ejecutable.
        base_path = os.path.dirname(sys.executable)
    else:
        # Si corremos como script, usamos la ruta relativa a este archivo
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    config_path = os.path.join(base_path, 'config.ini')
    
    # Si no existe config.ini, usar SQLite por defecto
    if not os.path.exists(config_path):
        logging.warning(f"No se encontró config.ini en: {config_path}. Usando SQLite.")
        return "sqlite:///clinic.db"
    
    try:
        config.read(config_path, encoding='utf-8')
    except Exception as e:
        logging.error(f"Error al leer config.ini desde {config_path}: {e}")
        return "sqlite:///clinic.db"
    
    # Leer tipo de base de datos (por defecto: sqlite)
    db_type = config.get('database', 'db_type', fallback='sqlite').lower()
    
    if db_type == 'mssql':
        # Soporta dos modos:
        # - Autenticación SQL (user + password)
        # - Autenticación de Windows (trusted_connection = yes)
        host = config.get('database', 'mssql_host', fallback='localhost')
        port = config.get('database', 'mssql_port', fallback='1433')
        database = config.get('database', 'mssql_database', fallback='clinic_db')
        user = config.get('database', 'mssql_user', fallback='')
        password = config.get('database', 'mssql_password', fallback='')
        driver = config.get('database', 'mssql_driver', fallback='ODBC Driver 17 for SQL Server')
        trusted = config.getboolean('database', 'mssql_trusted', fallback=False)

        # Construir connection string ODBC y luego usar odbc_connect (más robusto)
        # Soportar instancias nombradas: si host contiene '\\' (ej. 'localhost\\SQLEXPRESS')
        # o si puerto está vacío, no añadimos ",port" a SERVER.
        if host and ('\\' in host or not port):
            server_part = host
        else:
            server_part = f"{host},{port}"

        if trusted or not user:
            # Windows Authentication / Trusted Connection
            odbc_parts = (
                f"DRIVER={{{driver}}};"
                f"SERVER={server_part};"
                f"DATABASE={database};"
                f"Trusted_Connection=Yes;"
            )
        else:
            # SQL Server Authentication
            odbc_parts = (
                f"DRIVER={{{driver}}};"
                f"SERVER={server_part};"
                f"DATABASE={database};"
                f"UID={user};PWD={password};"
            )

        # Usar odbc_connect para evitar problemas con caracteres especiales y el driver
        odbc_conn_str = quote_plus(odbc_parts)
        logging.info(f"Configurando conexión MSSQL a {server_part} (DB: {database})")
        return f"mssql+pyodbc:///?odbc_connect={odbc_conn_str}"
    else:
        # Usar SQLite por defecto
        logging.info(f"Modo de base de datos configurado: {db_type}. Usando SQLite.")
        return "sqlite:///clinic.db"

# Obtener la URL de conexión
DATABASE_URL = get_database_url()

# El 'engine' es el punto de entrada a la base de datos.
# echo=False para evitar que imprima cada comando SQL en la consola.
# Ponlo en True si necesitas depurar las consultas SQL.
if DATABASE_URL.startswith('mssql'):
    # Si es MSSQL, crear engine con el URL preparado
    logger = logging.getLogger(__name__)
    try:
        logger.info("Intentando crear engine SQL Server (MSSQL)...")
        engine = create_engine(DATABASE_URL, echo=False)
        # Probar la conexión rápidamente
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Engine MSSQL creado correctamente.")
    except Exception as e:
        logger.error(f"No se pudo conectar a MSSQL: {e}")
        logger.critical("!!! ERROR CRÍTICO DE CONEXIÓN A SQL SERVER !!!")
        logger.warning(f"La aplicación usará una base de datos SQLite LOCAL temporal ({os.path.abspath('clinic.db')}) en su lugar.")
        logger.warning("Verifique que el servidor esté activo, el firewall permita la conexión y las credenciales sean correctas.")
        engine = create_engine("sqlite:///clinic.db", echo=False)
else:
    # Configuración para SQLite
    engine = create_engine(DATABASE_URL, echo=False)

# SessionLocal es una "fábrica" que creará nuevas sesiones de base de datos
# cuando se la llame.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    """
    Función de utilidad para obtener una sesión de base de datos.
    Esto asegura que cada parte de tu código obtiene una sesión fresca.
    """
    return SessionLocal()

# (Opcional pero recomendado) Un gestor de contexto para manejar sesiones
@contextlib.contextmanager
def session_scope():
    """Proporciona un ámbito transaccional para una serie de operaciones."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
