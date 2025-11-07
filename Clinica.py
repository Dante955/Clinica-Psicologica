import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from core.initializer import ensure_env_exists, ensure_initial_user_gui
import sqlite3, os

db = "clinica.db"
if not os.path.exists(db):
    print("No existe", db); sys.exit(1)
con = sqlite3.connect(db)
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tablas:", [r[0] for r in cur.fetchall()])
try:
    cur.execute("SELECT COUNT(*) FROM Usuarios")
    print("Usuarios:", cur.fetchone()[0])
except Exception as e:
    print("La tabla Usuarios no existe o error:", e)
con.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        # crear .env si no existe (antes de importar UI/config/security)
        created_env = ensure_env_exists(None)
    except Exception as e:
        QMessageBox.critical(None, "Error inicializando configuración", str(e))
        sys.exit(1)

    # intentar crear la BD si no existe
    try:
        from core.config import settings
        db_path = Path(settings.database_url.replace("sqlite:///", ""))
        if not db_path.exists():
            try:
                from core.database import init_db
                init_db()
            except Exception as e:
                QMessageBox.warning(None, "BD no creada",
                                     f"No se ha podido crear la base de datos automáticamente:\n{e}\n"
                                     "Ejecuta manualmente: python core/init_db.py")
    except Exception as e:
        QMessageBox.warning(None, "Aviso configuración", f"No se pudo verificar la BD: {e}")

    # lanzar diálogo de creación de usuario si hace falta (se intentará crear la BD si falta)
    try:
        ensure_initial_user_gui(None)
    except Exception as e:
        QMessageBox.critical(None, "Error creando usuario inicial", str(e))
        # no salimos; permitimos que la app arranque para depuración

    # ahora cargamos la UI principal
    from ui.main_window import MainApp

    ventana = MainApp()
    ventana.show()
    sys.exit(app.exec())