"""
Módulo de Respaldos Automáticos de Base de Datos

Crea respaldos automáticos de la base de datos SQLite al iniciar la aplicación.
Mantiene los últimos 10 respaldos y elimina los más antiguos.
"""

import os
import shutil
from datetime import datetime
import logging


def create_automatic_backup(db_path='clinic.db', backup_dir='backups', max_backups=10):
    """
    Crea un respaldo automático de la base de datos.
    
    Args:
        db_path: Ruta al archivo de base de datos
        backup_dir: Directorio donde guardar los respaldos
        max_backups: Número máximo de respaldos a mantener
    
    Returns:
        bool: True si el respaldo fue exitoso, False en caso contrario
    """
    try:
        # Verificar que existe la base de datos
        if not os.path.exists(db_path):
            logging.info("No se encontró base de datos para respaldar. Se creará una nueva.")
            return False
        
        # Crear directorio de respaldos si no existe
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generar nombre del respaldo con fecha y hora
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'clinic_auto_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copiar archivo
        shutil.copy2(db_path, backup_path)
        
        # Obtener tamaño del respaldo
        backup_size = os.path.getsize(backup_path)
        backup_size_mb = backup_size / (1024 * 1024)
        
        logging.info(f"✅ Respaldo automático creado: {backup_filename} ({backup_size_mb:.2f} MB)")
        
        # Limpiar respaldos antiguos
        cleanup_old_backups(backup_dir, max_backups)
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error al crear respaldo automático: {e}")
        return False


def cleanup_old_backups(backup_dir, max_backups):
    """
    Elimina los respaldos más antiguos si exceden el límite.
    
    Args:
        backup_dir: Directorio de respaldos
        max_backups: Número máximo de respaldos a mantener
    """
    try:
        # Obtener lista de archivos de respaldo
        backup_files = []
        for filename in os.listdir(backup_dir):
            if filename.startswith('clinic_') and filename.endswith('.db'):
                filepath = os.path.join(backup_dir, filename)
                # Obtener tiempo de modificación
                mtime = os.path.getmtime(filepath)
                backup_files.append((filepath, mtime, filename))
        
        # Ordenar por fecha (más reciente primero)
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        # Eliminar respaldos excedentes
        if len(backup_files) > max_backups:
            files_to_delete = backup_files[max_backups:]
            for filepath, _, filename in files_to_delete:
                os.remove(filepath)
                logging.info(f"🗑️  Respaldo antiguo eliminado: {filename}")
            
            logging.info(f"Manteniendo los {max_backups} respaldos más recientes")
        
    except Exception as e:
        logging.error(f"Error al limpiar respaldos antiguos: {e}")


def get_backup_info(backup_dir='backups'):
    """
    Obtiene información sobre los respaldos existentes.
    
    Returns:
        list: Lista de diccionarios con información de cada respaldo
    """
    backups = []
    
    if not os.path.exists(backup_dir):
        return backups
    
    try:
        for filename in os.listdir(backup_dir):
            if filename.startswith('clinic_') and filename.endswith('.db'):
                filepath = os.path.join(backup_dir, filename)
                size = os.path.getsize(filepath)
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                backups.append({
                    'filename': filename,
                    'path': filepath,
                    'size_mb': size / (1024 * 1024),
                    'date': mtime
                })
        
        # Ordenar por fecha (más reciente primero)
        backups.sort(key=lambda x: x['date'], reverse=True)
        
    except Exception as e:
        logging.error(f"Error al obtener información de respaldos: {e}")
    
    return backups


def restore_backup(backup_path, db_path='clinic.db'):
    """
    Restaura una base de datos desde un respaldo.
    
    Args:
        backup_path: Ruta al archivo de respaldo
        db_path: Ruta donde restaurar la base de datos
    
    Returns:
        bool: True si la restauración fue exitosa
    """
    try:
        if not os.path.exists(backup_path):
            logging.error(f"No se encontró el archivo de respaldo: {backup_path}")
            return False
        
        # Crear respaldo de la base de datos actual antes de restaurar
        if os.path.exists(db_path):
            pre_restore_backup = f"{db_path}.pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, pre_restore_backup)
            logging.info(f"Respaldo de seguridad creado: {pre_restore_backup}")
        
        # Restaurar desde el respaldo
        shutil.copy2(backup_path, db_path)
        logging.info(f"✅ Base de datos restaurada desde: {backup_path}")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error al restaurar respaldo: {e}")
        return False
