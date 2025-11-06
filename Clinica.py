import sys
import requests
import sqlite3
from pathlib import Path
from core.config import settings
from core import security
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QMessageBox, QStackedWidget, QFrame
)
from PySide6.QtCore import Qt, QSize

API_URL = "local"  # Cambiar a "local" para usar la DB SQLite local. Antes: "http://localhost:8000"

# Helper: Simple MenuBar look
class MenuBar(QFrame):
    def __init__(self, on_navigate, on_logout):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        buttons = [
            ("Inicio", "dashboard"),
            ("Pacientes", "pacientes"),
            ("Cerrar sesión", "logout"),  # Simula menú
        ]
        for txt, key in buttons:
            btn = QPushButton(txt)
            btn.setStyleSheet("""
            QPushButton { 
                background-color: #353a47;
                color: #e1e1e1;
                border-radius: 7px;
                padding: 7px 18px;
                font-weight:bold;
            }
            QPushButton:hover { background: #3b80e0; color: #fff; }
            """)
            if key == "logout":
                btn.clicked.connect(on_logout)
            else:
                btn.clicked.connect(lambda _, x=key: on_navigate(x))
            layout.addWidget(btn)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("QFrame { background:#23272f; }")


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
        # Aesthetic
        self.setStyleSheet("""
            QWidget {background:#23272f;}
            QLineEdit {padding:7px;border-radius:5px;margin-bottom:7px;background:#353a47;color:#e1e1e1;}
        """)
        self.setFixedWidth(330)

    def try_login(self):
        email = self.email.text()
        password = self.password.text()
        # Modo local: usa SQLite directamente
        if API_URL == "local":
            try:
                db_url = settings.database_url
                if not db_url.startswith("sqlite:///"):
                    raise RuntimeError("DATABASE_URL debe ser sqlite:///... para modo local")
                db_path = db_url.replace("sqlite:///", "")
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("SELECT id_usuario, contrasena_hash, activo FROM Usuarios WHERE email = ?", (email,))
                row = cur.fetchone()
                conn.close()
                if not row:
                    QMessageBox.warning(self, "Error", "Usuario no encontrado")
                    return
                id_usuario, hash_pw, activo = row
                if activo != 1:
                    QMessageBox.warning(self, "Error", "Usuario inactivo")
                    return
                ok = security.verify_password(hash_pw, password)
                if ok:
                    self.on_login(id_usuario)  # en modo local pasamos id_usuario como token/identificador
                else:
                    QMessageBox.warning(self, "Error", "Credenciales incorrectas")
            except Exception as e:
                QMessageBox.critical(self, "Error de BD", str(e))
            return

        # Modo remoto (HTTP)
        try:
            r = requests.post(f"{API_URL}/login", json={"email": email, "password": password}, timeout=6)
            if r.status_code == 200:
                token = r.json()['access_token']
                self.on_login(token)
            else:
                QMessageBox.warning(self, "Error", "Credenciales incorrectas")
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Error de red", f"No se pudo conectar a: {API_URL}")
        except requests.exceptions.Timeout:
            QMessageBox.critical(self, "Error de red", "Tiempo de espera agotado al intentar conectar con el backend.")
        except Exception as e:
            QMessageBox.critical(self, "Error de red", str(e))


class Dashboard(QWidget):
    def __init__(self, token):
        super().__init__()
        layout = QVBoxLayout(self)
        lbl = QLabel("Bienvenido a la Clínica")
        lbl.setStyleSheet("font-size:18px;color:#3b80e0;")
        layout.addWidget(lbl)
        self.stats = QLabel("Cargando...")  # Mostrar stats de backend
        layout.addWidget(self.stats)
        self.setStyleSheet("background:#23272f;color:#e1e1e1;")
        self.load(token)

    def load(self, token):
        # Modo local
        if API_URL == "local":
            try:
                db_path = settings.database_url.replace("sqlite:///", "")
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                # pacientes activos
                cur.execute("SELECT COUNT(*) FROM Pacientes WHERE activo = 1")
                pacientes_activos = cur.fetchone()[0] or 0
                # citas hoy (comparar fecha parte ISO)
                cur.execute("SELECT COUNT(*) FROM Citas WHERE date(fecha_hora_inicio) = date('now')")
                citas_hoy = cur.fetchone()[0] or 0
                # ingresos mes (pagos pagados)
                cur.execute("SELECT IFNULL(SUM(monto),0) FROM Pagos WHERE estado = 'Pagado' AND strftime('%Y-%m', fecha_pago) = strftime('%Y-%m','now')")
                ingresos_mes = cur.fetchone()[0] or 0.0
                conn.close()
                self.stats.setText(
                    f"Pacientes activos: {pacientes_activos}\n"
                    f"Citas hoy: {citas_hoy}\n"
                    f"Ingresos mes: {ingresos_mes}"
                )
            except Exception as e:
                self.stats.setText("Error leyendo la DB local")
            return

        # Modo remoto
        try:
            headers = {"Authorization": f"Bearer {token}"}
            r = requests.get(f"{API_URL}/dashboard", headers=headers, timeout=6)
            if r.status_code == 200:
                d = r.json()
                self.stats.setText(
                    f"Pacientes activos: {d['pacientes_activos']}<br>"
                    f"Citas hoy: {d['citas_hoy']}<br>"
                    f"Ingresos mes: {d['ingresos_mes']:,}"
                )
            else:
                self.stats.setText("No se pudieron cargar los datos")
        except Exception:
            self.stats.setText("Sin conexión al backend")


class PacientesPage(QWidget):
    def __init__(self, token):
        super().__init__()
        layout = QVBoxLayout(self)
        lbl = QLabel("Pacientes")
        lbl.setStyleSheet("font-size:19px;font-weight:700;color:#3b80e0;")
        layout.addWidget(lbl)
        self.list = QListWidget()
        layout.addWidget(self.list)
        self.setStyleSheet("""
            background:#23272f;
            color:#e1e1e1;
            QListWidget {background:#353a47;color:white;border-radius:8px;font-size:15px;}
        """)
        self.load(token)

    def load(self, token):
        # Modo local
        if API_URL == "local":
            try:
                db_path = settings.database_url.replace("sqlite:///", "")
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("SELECT id_paciente, datos_sensibles_encriptados, telefono_encriptado FROM Pacientes WHERE activo = 1")
                self.list.clear()
                for id_p, datos_blob, tel_blob in cur.fetchall():
                    datos = {}
                    try:
                        datos = security.decrypt_data(datos_blob) or {}
                    except Exception:
                        datos = {}
                    nombre = datos.get("nombre", "")
                    apellido = datos.get("apellido", "")
                    telefono = ""
                    try:
                        t = security.decrypt_data(tel_blob) or {}
                        if isinstance(t, dict):
                            telefono = t.get("telefono", "")
                        else:
                            telefono = t
                    except Exception:
                        telefono = ""
                    self.list.addItem(f"{nombre} {apellido} - {telefono}")
                conn.close()
            except Exception as e:
                self.list.clear()
                self.list.addItem("Error leyendo la DB local")
            return

        # Modo remoto
        try:
            headers = {"Authorization": f"Bearer {token}"}
            r = requests.get(f"{API_URL}/pacientes", headers=headers, timeout=6)
            self.list.clear()
            if r.status_code == 200:
                for p in r.json():
                    nom = p.get('nombre', '')
                    ape = p.get('apellido', '')
                    tel = p.get('telefono', '')
                    self.list.addItem(f"{nom} {ape} - {tel}")
            else:
                self.list.addItem("Error al cargar pacientes")
        except Exception:
            self.list.addItem("No hay conexión al servidor")

class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clínica Psicológica")
        self.resize(550, 400)
        self.setStyleSheet("background:#23272f;")
        self.token = None
        self.menu_bar = None
        self.stacked = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked)
        self.show_login()

    def show_login(self):
        if self.menu_bar:
            self.menu_bar.setParent(None)
            self.menu_bar = None
        self.stacked.addWidget(LoginPage(self.on_login))
        self.stacked.setCurrentIndex(self.stacked.count() - 1)

    def on_login(self, token):
        self.token = token
        # Show menu bar
        self.menu_bar = MenuBar(self.navigate, self.logout)
        self.layout().insertWidget(0, self.menu_bar)
        self.navigate("dashboard")

    def logout(self):
        self.token = None
        self.stacked.addWidget(LoginPage(self.on_login))
        self.stacked.setCurrentIndex(self.stacked.count()-1)
        if self.menu_bar:
            self.menu_bar.setParent(None)
            self.menu_bar = None

    def navigate(self, page):
        widget = None
        if page == "dashboard":
            widget = Dashboard(self.token)
        elif page == "pacientes":
            widget = PacientesPage(self.token)
        else:
            w = QLabel("Pronto...")
            w.setStyleSheet("color:#3b80e0;font-size:19px")
            widget = w
        self.stacked.addWidget(widget)
        self.stacked.setCurrentIndex(self.stacked.count() - 1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MainApp()
    ventana.show()
    sys.exit(app.exec())