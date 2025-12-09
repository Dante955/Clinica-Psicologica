"""
Database Migration Utility

Provides functionality to migrate data from SQLite to PostgreSQL
and manage database connections.
"""

import logging
import configparser
import os
from typing import Dict, List, Tuple, Callable, Optional
from urllib.parse import quote_plus
from sqlalchemy import create_engine, inspect, MetaData, Table
from sqlalchemy.orm import sessionmaker
from database.models import Base, User, Patient, Appointment, Expense, Income, Salary


class DatabaseMigrator:
    """Handles database migration and connection testing."""
    
    def __init__(self, config_path: str = 'config.ini'):
        """
        Initialize the migrator.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
    
    
    def test_mssql_connection(
        self,
        host: str,
        port: str,
        database: str,
        user: str = '',
        password: str = '',
        driver: str = 'ODBC Driver 17 for SQL Server',
        trusted: bool = False
    ) -> Tuple[bool, str]:
        """
        Test SQL Server (MSSQL) connection using pyodbc.
        Supports Windows Authentication (trusted) and SQL Authentication.
        Returns (success, message).
        """
        try:
            import pyodbc
        except ImportError:
            return False, "❌ Error: pyodbc no está instalado\n\nInstala con: pip install pyodbc"

        # Construir connection string ODBC
        # Soportar instancias nombradas: si el host contiene '\\' (ej. 'localhost\\SQLEXPRESS')
        # o si no se proporciona puerto, no añadimos ",port" a SERVER.
        if host and ('\\' in host or not port):
            server_part = host
        else:
            server_part = f"{host},{port}"

        if trusted or not user:
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={server_part};"
                f"DATABASE={database};"
                f"Trusted_Connection=Yes;"
                f"TrustServerCertificate=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={server_part};"
                f"DATABASE={database};"
                f"UID={user};PWD={password};"
                f"TrustServerCertificate=yes;"
            )

        try:
            conn = pyodbc.connect(conn_str, timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT 1")
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row and row[0] == 1:
                return True, f"✅ Conexión exitosa a SQL Server {host}:{port}/{database}"
            return False, "❌ Conexión establecida pero la prueba SELECT falló"
        except Exception as e:
            return False, f"❌ Error de conexión a SQL Server:\n\n{str(e)}"


    
    def get_database_statistics(self) -> Dict[str, any]:
        """
        Get statistics about the current database.
        
        Returns:
            Dictionary with database statistics
        """
        try:
            from database.database_manager import engine, session_scope
            
            stats = {
                'db_type': 'SQLite' if engine.url.drivername == 'sqlite' else 'MSSQL',
                'url': str(engine.url).replace(engine.url.password or '', '****'),
                'tables': {}
            }
            
            # Get table counts
            with session_scope() as session:
                stats['tables']['Usuarios'] = session.query(User).count()
                stats['tables']['Pacientes'] = session.query(Patient).count()
                stats['tables']['Citas'] = session.query(Appointment).count()
                stats['tables']['Gastos'] = session.query(Expense).count()
                stats['tables']['Ingresos'] = session.query(Income).count()
            
            # Get database size (SQLite only)
            if stats['db_type'] == 'SQLite':
                db_path = str(engine.url).replace('sqlite:///', '')
                if os.path.exists(db_path):
                    size_bytes = os.path.getsize(db_path)
                    stats['size_mb'] = size_bytes / (1024 * 1024)
                    stats['size_bytes'] = size_bytes
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error al obtener estadísticas: {e}")
            return {'error': str(e)}
    
    def export_sqlite_data(self) -> Dict[str, List]:
        """
        Export all data from SQLite database.
        
        Returns:
            Dictionary with table names as keys and lists of records as values
        """
        from database.database_manager import session_scope
        
        data = {}
        
        try:
            with session_scope() as session:
                # Export users
                users = session.query(User).all()
                data['users'] = [
                    {
                        'id': u.id,
                        'username': u.username,
                        'hashed_password': u.hashed_password,
                        'role': u.role,
                        'full_name': u.full_name,
                        'specialization': u.specialization
                    }
                    for u in users
                ]
                
                # Export patients
                patients = session.query(Patient).all()
                data['patients'] = [
                    {
                        'id': p.id,
                        'full_name': p.full_name,
                        'contact_info': p.contact_info,
                        'email': p.email,
                        'psychologist_id': p.psychologist_id,
                        'patient_type': p.patient_type,
                        'tutor_name': p.tutor_name,
                        'birth_date': p.birth_date,
                        'gender_pronouns': p.gender_pronouns,
                        'address': p.address,
                        'emergency_contact': p.emergency_contact,
                        'referred_by': p.referred_by,
                        'main_reason_for_consultation': p.main_reason_for_consultation,
                        'current_symptoms': p.current_symptoms,
                        'problem_duration': p.problem_duration,
                        'therapy_expectations': p.therapy_expectations,
                        'previous_solution_attempts': p.previous_solution_attempts,
                        'previous_mental_health_history': p.previous_mental_health_history,
                        'psychiatric_medication': p.psychiatric_medication,
                        'other_medication': p.other_medication,
                        'family_history': p.family_history,
                        'risk_assessment': p.risk_assessment
                    }
                    for p in patients
                ]
                
                # Export appointments
                appointments = session.query(Appointment).all()
                data['appointments'] = [
                    {
                        'id': a.id,
                        'patient_id': a.patient_id,
                        'psychologist_id': a.psychologist_id,
                        'appointment_time': a.appointment_time,
                        'notes': a.notes,
                        'status': a.status,
                        'price': a.price,
                        'payment_status': a.payment_status
                    }
                    for a in appointments
                ]
                
                # Export expenses
                expenses = session.query(Expense).all()
                data['expenses'] = [
                    {
                        'id': e.id,
                        'description': e.description,
                        'amount': e.amount,
                        'expense_date': e.expense_date,
                        'expense_type': e.expense_type,
                        'month': e.month,
                        'year': e.year
                    }
                    for e in expenses
                ]
                
                # Export incomes
                incomes = session.query(Income).all()
                data['incomes'] = [
                    {
                        'id': i.id,
                        'description': i.description,
                        'amount': i.amount,
                        'income_date': i.income_date,
                        'appointment_id': i.appointment_id
                    }
                    for i in incomes
                ]
                
            self.logger.info(f"Datos exportados: {len(data['users'])} usuarios, "
                           f"{len(data['patients'])} pacientes, "
                           f"{len(data['appointments'])} citas")
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error al exportar datos: {e}", exc_info=True)
            raise
    
    def import_data_to_mssql(
        self,
        data: Dict[str, List],
        host: str,
        port: str,
        database: str,
        user: str = '',
        password: str = '',
        driver: str = 'ODBC Driver 17 for SQL Server',
        trusted: bool = False,
        progress_callback: Callable[[str, int, int], None] = None
    ) -> Tuple[bool, str]:
        """
        Importa datos a SQL Server desde un diccionario exportado.
        
        Args:
            data: Diccionario con datos exportados de SQLite
            host: Host del servidor SQL Server
            port: Puerto del servidor
            database: Nombre de la base de datos
            user: Usuario (opcional si trusted=True)
            password: Contraseña (opcional si trusted=True)
            driver: Driver ODBC
            trusted: Usar autenticación de Windows
            progress_callback: Función opcional para reportar progreso (tabla, actual, total)
            
        Returns:
            Tuple (éxito, mensaje)
        """
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        from urllib.parse import quote_plus
        
        try:
            # Construir connection string
            if host and ('\\' in host or not port):
                server_part = host
            else:
                server_part = f"{host},{port}"

            if trusted or not user:
                odbc_parts = (
                    f"DRIVER={{{driver}}};"
                    f"SERVER={server_part};"
                    f"DATABASE={database};"
                    f"Trusted_Connection=Yes;"
                    f"TrustServerCertificate=yes;"
                )
            else:
                odbc_parts = (
                    f"DRIVER={{{driver}}};"
                    f"SERVER={server_part};"
                    f"DATABASE={database};"
                    f"UID={user};PWD={password};"
                    f"TrustServerCertificate=yes;"
                )

            odbc_conn_str = quote_plus(odbc_parts)
            mssql_url = f"mssql+pyodbc:///?odbc_connect={odbc_conn_str}"
            
            # Crear engine y sesión
            engine = create_engine(mssql_url, echo=False)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            self.logger.info("Iniciando importación de datos a SQL Server...")
            
            # Importar en orden para mantener integridad referencial
            tables_order = ['users', 'patients', 'appointments', 'incomes', 'expenses']
            
            for table_name in tables_order:
                if table_name not in data or not data[table_name]:
                    continue
                
                records = data[table_name]
                total = len(records)
                
                self.logger.info(f"Importando {total} registros a tabla '{table_name}'...")
                
                if progress_callback:
                    progress_callback(table_name, 0, total)
                
                # Habilitar IDENTITY_INSERT para preservar IDs
                session.execute(text(f"SET IDENTITY_INSERT {table_name} ON"))
                
                try:
                    for idx, record in enumerate(records):
                        # Convertir enums a strings si es necesario
                        if table_name == 'users' and 'role' in record:
                            role_value = record['role']
                            if hasattr(role_value, 'value'):
                                record['role'] = role_value.value
                            elif hasattr(role_value, 'name'):
                                record['role'] = role_value.name
                        
                        # Construir INSERT statement
                        columns = ', '.join(record.keys())
                        placeholders = ', '.join([f":{key}" for key in record.keys()])
                        insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                        
                        session.execute(text(insert_sql), record)
                        
                        if progress_callback and (idx + 1) % 10 == 0:
                            progress_callback(table_name, idx + 1, total)
                    
                    session.commit()
                    
                    if progress_callback:
                        progress_callback(table_name, total, total)
                    
                except Exception as e:
                    session.rollback()
                    self.logger.error(f"Error importando tabla '{table_name}': {e}")
                    raise
                finally:
                    # Deshabilitar IDENTITY_INSERT
                    session.execute(text(f"SET IDENTITY_INSERT {table_name} OFF"))
                    session.commit()
            
            session.close()
            
            message = (
                f"✅ Migración completada exitosamente\n\n"
                f"Registros importados:\n"
                f"  - Usuarios: {len(data.get('users', []))}\n"
                f"  - Pacientes: {len(data.get('patients', []))}\n"
                f"  - Citas: {len(data.get('appointments', []))}\n"
                f"  - Ingresos: {len(data.get('incomes', []))}\n"
                f"  - Gastos: {len(data.get('expenses', []))}\n"
            )
            
            self.logger.info(message)
            return True, message
            
        except Exception as e:
            error_msg = f"❌ Error durante la migración:\n\n{str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    

    def update_config_to_mssql(
        self,
        host: str,
        port: str,
        database: str,
        user: str = '',
        password: str = '',
        driver: str = 'ODBC Driver 17 for SQL Server',
        trusted: bool = False
    ):
        """
        Update config.ini to use MSSQL (SQL Server).
        """
        config = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            config.read(self.config_path, encoding='utf-8')
        if not config.has_section('database'):
            config.add_section('database')

        config.set('database', 'db_type', 'mssql')
        config.set('database', 'mssql_host', host)
        config.set('database', 'mssql_port', port)
        config.set('database', 'mssql_database', database)
        config.set('database', 'mssql_user', user)
        config.set('database', 'mssql_password', password)
        config.set('database', 'mssql_driver', driver)
        config.set('database', 'mssql_trusted', 'true' if trusted else 'false')

        with open(self.config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        self.logger.info("Configuración actualizada a SQL Server (MSSQL)")

    def save_mssql_config(
        self,
        host: str,
        port: str,
        database: str,
        user: str = '',
        password: str = '',
        driver: str = 'ODBC Driver 17 for SQL Server',
        trusted: bool = False
    ):
        """
        Save MSSQL configuration without switching to it.
        """
        config = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            config.read(self.config_path, encoding='utf-8')
        if not config.has_section('database'):
            config.add_section('database')

        config.set('database', 'mssql_host', host)
        config.set('database', 'mssql_port', port)
        config.set('database', 'mssql_database', database)
        config.set('database', 'mssql_user', user)
        config.set('database', 'mssql_password', password)
        config.set('database', 'mssql_driver', driver)
        config.set('database', 'mssql_trusted', 'true' if trusted else 'false')

        with open(self.config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        self.logger.info("Configuración de MSSQL guardada")

    def load_mssql_config(self) -> Dict[str, str]:
        """Load MSSQL configuration from config.ini."""
        config = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            config.read(self.config_path, encoding='utf-8')

        return {
            'host': config.get('database', 'mssql_host', fallback='localhost'),
            'port': config.get('database', 'mssql_port', fallback='1433'),
            'database': config.get('database', 'mssql_database', fallback='clinic_db'),
            'user': config.get('database', 'mssql_user', fallback=''),
            'password': config.get('database', 'mssql_password', fallback=''),
            'driver': config.get('database', 'mssql_driver', fallback='ODBC Driver 17 for SQL Server'),
            'trusted': config.getboolean('database', 'mssql_trusted', fallback=False)
        }
