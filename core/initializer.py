from pathlib import Path
import os
import secrets
from cryptography.fernet import Fernet
from PySide6.QtWidgets import QInputDialog, QMessageBox, QLineEdit

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"

def ensure_env_exists(parent=None):
    """
    Crea .env con claves si no existe.
    No muestra ni imprime las claves; informa sólo que se creó.
    """
    if ENV_FILE.exists():
        return False

    master_key = Fernet.generate_key().decode()
    jwt_secret = secrets.token_urlsafe(48)

    content = (
        f'CLINICA_MASTER_KEY="{master_key}"\n'
        f'JWT_SECRET_KEY="{jwt_secret}"\n'
        'ALGORITHM="HS256"\n'
        'ACCESS_TOKEN_EXPIRE_MINUTES=480\n'
        'DATABASE_URL="sqlite:///./clinica.db"\n'
        'UPLOAD_DIR="./secure/uploads"\n'
        'BACKUP_DIR="./backups"\n'
    )

    ENV_FILE.write_text(content, encoding="utf-8")
    try:
        os.chmod(ENV_FILE, 0o600)
    except Exception:
        pass

    QMessageBox.information(parent, "Configuración creada",
                            ".env creado con claves de cifrado y configuración por defecto.\n\n"
                            "No se muestran las claves por seguridad.")
    return True


def ensure_initial_user_gui(parent=None):
    """
    Si la tabla Usuarios está vacía, pide email+contraseña por diálogo y crea el admin.
    Usa get_db y security importados de forma perezosa (se cargan tras existir .env).
    """
    # importaciones perezosas para que core.config lea .env ya creado
    from core.database import get_db
    from core import security
    import uuid
    import secrets as _secrets

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM Usuarios")
        row = cur.fetchone()
        cnt = row["cnt"] if row and "cnt" in row.keys() else (row[0] if row else 0)
        if cnt and cnt > 0:
            return False

        email, ok = QInputDialog.getText(parent, "Email admin", "Email para el usuario administrador:", QLineEdit.Normal)
        if not ok or not email:
            raise RuntimeError("Se requiere un email para crear el usuario inicial.")

        # pedir contraseña y confirmación
        while True:
            pwd, ok = QInputDialog.getText(parent, "Contraseña admin", "Introduce la contraseña del usuario administrador:", QLineEdit.Password)
            if not ok:
                raise RuntimeError("Creación de usuario inicial cancelada por el usuario.")
            if len(pwd) < 8:
                QMessageBox.warning(parent, "Contraseña demasiado corta", "La contraseña debe tener al menos 8 caracteres.")
                continue
            pwd2, ok2 = QInputDialog.getText(parent, "Confirmar contraseña", "Confirma la contraseña:", QLineEdit.Password)
            if not ok2:
                raise RuntimeError("Creación de usuario inicial cancelada por el usuario.")
            if pwd != pwd2:
                QMessageBox.warning(parent, "No coinciden", "Las contraseñas no coinciden. Intenta de nuevo.")
                continue
            break

        # crear columna reversible si no existe
        cur.execute("PRAGMA table_info(Usuarios)")
        cols = [r["name"] for r in cur.fetchall()]
        if "contrasena_encriptada" not in cols:
            cur.execute("ALTER TABLE Usuarios ADD COLUMN contrasena_encriptada BLOB")

        uid = str(uuid.uuid4())
        pwd_hash = security.hash_password(pwd)
        try:
            encrypted_pwd = security.fernet.encrypt(pwd.encode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"No se pudo cifrar la contraseña: {e}")
        salt = _secrets.token_hex(16)

        cur.execute(
            "INSERT INTO Usuarios (id_usuario, email, contrasena_hash, salt, nombre_clinica, activo, contrasena_encriptada) VALUES (?,?,?,?,?,?,?)",
            (uid, email, pwd_hash, salt, "Clínica Inicial", 1, encrypted_pwd)
        )
        conn.commit()

    QMessageBox.information(parent, "Usuario creado",
                            f"Se ha creado el usuario administrador con email:\n\n{email}\n\n"
                            "La contraseña fue guardada de forma segura (no se muestra).")
    return True