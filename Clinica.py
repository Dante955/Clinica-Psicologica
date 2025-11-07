import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from core.initializer import ensure_env_exists, ensure_initial_user_gui

if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        # crear .env si no existe (antes de importar UI/config/security)
        created_env = ensure_env_exists(None)
    except Exception as e:
        QMessageBox.critical(None, "Error inicializando configuración", str(e))
        sys.exit(1)

    # Si acabamos de crear .env, intentar crear la BD y lanzar el diálogo de creación de usuario
    if created_env:
        try:
            # ahora que .env existe, cargamos settings y podemos inicializar la BD
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

        # abrir diálogo para crear el usuario inicial (si hace falta)
        try:
            ensure_initial_user_gui(None)
        except Exception as e:
            QMessageBox.critical(None, "Error creando usuario inicial", str(e))
            # no salimos; permitimos que la app arranque para depuración

    else:
        # Si .env ya existía, seguimos con la comprobación normal de BD (no forzamos diálogo)
        try:
            from core.config import settings
            db_path = Path(settings.database_url.replace("sqlite:///", ""))
            if not db_path.exists():
                try:
                    from core.database import init_db
                    init_db()
                except Exception:
                    QMessageBox.warning(None, "BD no creada",
                                         "No se ha podido crear la base de datos automáticamente.\n"
                                         "Ejecuta manualmente: python core/init_db.py")
        except Exception as e:
            QMessageBox.warning(None, "Aviso configuración", f"No se pudo verificar la BD: {e}")

    # ahora podemos cargar la UI principal (que cargará core.config/core.security correctamente)
    from ui.main_window import MainApp

    ventana = MainApp()
    ventana.show()
    sys.exit(app.exec())