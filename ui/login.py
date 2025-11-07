from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt
from core import security
from core.config import settings
from core.database import get_db

class LoginPage(QWidget):
    def __init__(self, on_login):
        super().__init__()
        layout = QVBoxLayout(self)
        lbl_title = QLabel("Clínica Psicológica")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("font-size:23px;font-weight:700;color:#3b80e0;")
        layout.addWidget(lbl_title)
        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        layout.addWidget(self.email)
        self.password = QLineEdit()
        self.password.setPlaceholderText("Contraseña")
        self.password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password)
        btn_login = QPushButton("Ingresar")
        btn_login.setStyleSheet("background:#3b80e0;color:white;font-weight:600;border-radius:7px;padding:9px;")
        btn_login.clicked.connect(self.try_login)
        layout.addWidget(btn_login)
        self.on_login = on_login
        self.setStyleSheet("""
            QWidget {background:#23272f;}
            QLineEdit {padding:7px;border-radius:5px;margin-bottom:7px;background:#353a47;color:#e1e1e1;}
        """)
        self.setFixedWidth(330)

    def try_login(self):
        email = self.email.text().strip()
        password = self.password.text()
        if not email or not password:
            QMessageBox.warning(self, "Error", "Introduce email y contraseña")
            return

        # Modo local usando get_db (SQLite)
        db_url = settings.database_url
        if not db_url.startswith("sqlite:///"):
            QMessageBox.critical(self, "Error", "DATABASE_URL no apunta a SQLite")
            return
        try:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id_usuario, contrasena_hash, activo FROM Usuarios WHERE email = ?", (email,))
                row = cur.fetchone()
                if not row:
                    QMessageBox.warning(self, "Error", "Usuario no encontrado")
                    return
                id_usuario = row["id_usuario"]
                hash_pw = row["contrasena_hash"]
                activo = row["activo"]
                if activo != 1:
                    QMessageBox.warning(self, "Error", "Usuario inactivo")
                    return
                ok = security.verify_password(hash_pw, password)
                if ok == "NEED_REHASH":
                    new_hash = security.hash_password(password)
                    cur.execute("UPDATE Usuarios SET contrasena_hash = ? WHERE id_usuario = ?", (new_hash, id_usuario))
                    conn.commit()
                    ok = True
                if ok:
                    self.on_login(id_usuario)
                else:
                    QMessageBox.warning(self, "Error", "Credenciales incorrectas")
        except Exception as e:
            QMessageBox.critical(self, "Error de BD", str(e))