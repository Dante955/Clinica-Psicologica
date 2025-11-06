import logging
from datetime import datetime
from core.database import get_db
import uuid

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("clinica_audit.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def log_acceso(id_usuario: str, tabla: str, id_registro: str, accion: str, ip: str = None):
    """Registra operación en tabla Auditoria y archivo log"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            auditoria_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO Auditoria_Acceso (id_auditoria, id_usuario, tabla_afectada, id_registro, accion, ip_address)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (auditoria_id, id_usuario, tabla, id_registro, accion, ip))
        
        logger.info(f"📝 AUDIT: {accion} en {tabla} id={id_registro} por user={id_usuario} ip={ip}")
    except Exception as e:
        logger.error(f"❌ Error en auditoría: {e}")

def log_error(mensaje: str):
    """Loguea errores críticos"""
    logger.error(f"🔥 ERROR: {mensaje}")

def log_backup(ruta: str, tamano: float, estado: str):
    """Loguea operaciones de backup"""
    logger.info(f"💾 BACKUP: {ruta} - {tamano:.2f} GB - Estado: {estado}")