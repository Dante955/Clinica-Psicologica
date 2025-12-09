import configparser
import os
import sys
import logging
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text

# Setup minimal logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ReproScript")

def get_database_url():
    # Verify config path
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_path, 'config.ini')
    
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    
    host = config.get('database', 'mssql_host', fallback='localhost')
    port = config.get('database', 'mssql_port', fallback='1433')
    database = config.get('database', 'mssql_database', fallback='clinic_db')
    user = config.get('database', 'mssql_user', fallback='')
    password = config.get('database', 'mssql_password', fallback='')
    driver = config.get('database', 'mssql_driver', fallback='ODBC Driver 17 for SQL Server')
    trusted = config.getboolean('database', 'mssql_trusted', fallback=False)

    if host and ('\\' in host or not port):
        server_part = host
    else:
        server_part = f"{host},{port}"

    # REPRO: Using exact logic from database_manager.py (missing TrustServerCertificate)
    if trusted or not user:
        odbc_parts = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server_part};"
            f"DATABASE={database};"
            f"Trusted_Connection=Yes;"
        )
    else:
        odbc_parts = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server_part};"
            f"DATABASE={database};"
            f"UID={user};PWD={password};"
        )

    odbc_conn_str = quote_plus(odbc_parts)
    logger.info(f"Connecting to {server_part}...")
    return f"mssql+pyodbc:///?odbc_connect={odbc_conn_str}"

try:
    url = get_database_url()
    engine = create_engine(url, echo=False)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("SUCCESS: Connection worked WITHOUT TrustServerCertificate!")
except Exception as e:
    print(f"FAILURE: Connection failed as expected. Error: {e}")
