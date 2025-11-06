#!/usr/bin/env python3
import argparse
import secrets
import sqlite3
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
SQL_FILE = ROOT / "CLINICA PSICOLOGICA - SQLITE.txt"

def generate_keys():
    from cryptography.fernet import Fernet
    master_key = Fernet.generate_key().decode()
    jwt_secret = secrets.token_urlsafe(48)
    return master_key, jwt_secret

def write_env(master_key, jwt_secret, force=False):
    content = (
        f'CLINICA_MASTER_KEY="{master_key}"\n'
        f'JWT_SECRET_KEY="{jwt_secret}"\n'
        'ALGORITHM="HS256"\n'
        'ACCESS_TOKEN_EXPIRE_MINUTES=480\n'
        'DATABASE_URL="sqlite:///./clinica.db"\n'
        'UPLOAD_DIR="./secure/uploads"\n'
        'BACKUP_DIR="./backups"\n'
    )
    ENV_FILE.write_text(content)

def db_path_from_url(url: str) -> str:
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "")
    raise RuntimeError("Solo se soporta sqlite:///... en este script")

def main():
    ap = argparse.ArgumentParser(description="Inicializa DB y crea primer usuario")
    ap.add_argument("--email", default="admin@clinica.com")
    ap.add_argument("--password", default="Admin123!", help="Cambia la contraseña después")
    ap.add_argument("--clinic", default="Mi Clínica Psicológica")
    ap.add_argument("--force", action="store_true", help="Forzar regeneración de .env")
    args = ap.parse_args()

    if not ENV_FILE.exists() or args.force:
        master_key, jwt_secret = generate_keys()
        write_env(master_key, jwt_secret, force=args.force)
        print("Creado/actualizado .env con claves generadas.")
    else:
        print(".env ya existe (use --force para regenerar).")

    # Importar settings y security ahora que .env existe
    from core.config import settings  # <- [`core.config.settings`](core/config.py)
    from core import security         # <- [`core.security.hash_password`](core/security.py)

    db_path = db_path_from_url(settings.database_url)
    conn = sqlite3.connect(db_path)
    sql = SQL_FILE.read_text(encoding="utf-8")
    conn.executescript(sql)
    print("Esquema ejecutado en:", db_path)

    uid = str(uuid.uuid4())
    pw_hash = security.hash_password(args.password)
    salt = secrets.token_hex(16)
    conn.execute(
        "INSERT OR REPLACE INTO Usuarios (id_usuario, email, contrasena_hash, salt, nombre_clinica) VALUES (?,?,?,?,?)",
        (uid, args.email, pw_hash, salt, args.clinic),
    )
    conn.commit()
    conn.close()
    print(f"Usuario creado: {args.email} (id={uid})")
    print("¡Listo! Cambia la contraseña del admin al iniciar sesión.")
    
if __name__ == "__main__":
    main()