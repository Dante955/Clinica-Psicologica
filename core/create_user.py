import getpass
import uuid
import secrets
import sys
from core.database import get_db
from core import security

def main():
    email = input("Email del usuario admin: ").strip()
    if not email:
        print("Email requerido"); sys.exit(1)
    pwd = getpass.getpass("Contraseña (no se mostrará): ")
    pwd2 = getpass.getpass("Confirmar contraseña: ")
    if pwd != pwd2:
        print("Las contraseñas no coinciden"); sys.exit(1)
    if len(pwd) < 8:
        print("La contraseña debe tener al menos 8 caracteres"); sys.exit(1)

    with get_db() as conn:
        cur = conn.cursor()
        # crear columna reversible si no existe
        cur.execute("PRAGMA table_info(Usuarios)")
        cols = [r["name"] for r in cur.fetchall()]
        if "contrasena_encriptada" not in cols:
            cur.execute("ALTER TABLE Usuarios ADD COLUMN contrasena_encriptada BLOB")
        uid = str(uuid.uuid4())
        pwd_hash = security.hash_password(pwd)
        encrypted_pwd = security.fernet.encrypt(pwd.encode("utf-8"))
        salt = secrets.token_hex(16)
        cur.execute(
            "INSERT INTO Usuarios (id_usuario, email, contrasena_hash, salt, nombre_clinica, activo, contrasena_encriptada) VALUES (?,?,?,?,?,?,?)",
            (uid, email, pwd_hash, salt, "Clínica", 1, encrypted_pwd)
        )
        conn.commit()
    print("Usuario creado:", email)

if __name__ == "__main__":
    main()