import requests
import sqlite3
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QStackedWidget, QFrame, QMessageBox
from PySide6.QtCore import Qt
from core.config import settings
from core import security
from core.database import get_db
from core.initializer import ensure_initial_user_gui
from ui.login import LoginPage

API_URL = "http://localhost:8000"

def detect_use_local_db():
    try:
        requests.get(API_URL, timeout=0.8)
        return False
    except Exception:
        return True

USE_LOCAL_DB = detect_use_local_db()

class MenuBar(QFrame):
    def __init__(self, on_navigate, on_logout):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        buttons = [("Inicio", "dashboard"), ("Pacientes", "pacientes"), ("Cerrar sesión", "logout")]
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

class Dashboard(QWidget):
    def __init__(self, token):
        super().__init__()
        layout = QVBoxLayout(self)
        lbl = QLabel("Bienvenido a la Clínica")
        lbl.setStyleSheet("font-size:18px;color:#3b80e0;")
        layout.addWidget(lbl)
        self.stats = QLabel("Cargando...")
        layout.addWidget(self.stats)
        self.setStyleSheet("background:#23272f;color:#e1e1e1;")
        self.load(token)

    def load(self, token):
        if USE_LOCAL_DB:
            try:
                db_path = settings.database_url.replace("sqlite:///", "")
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM Pacientes WHERE activo = 1")
                pacientes_activos = cur.fetchone()[0] or 0
                cur.execute("SELECT COUNT(*) FROM Citas WHERE date(fecha_hora_inicio) = date('now')")
                citas_hoy = cur.fetchone()[0] or 0
                cur.execute("SELECT IFNULL(SUM(monto),0) FROM Pagos WHERE estado = 'Pagado' AND strftime('%Y-%m', fecha_pago) = strftime('%Y-%m','now')")
                ingresos_mes = cur.fetchone()[0] or 0.0
                conn.close()
                self.stats.setText(f"Pacientes activos: {pacientes_activos}\nCitas hoy: {citas_hoy}\nIngresos mes: {ingresos_mes}")
            except Exception:
                self.stats.setText("Error leyendo la DB local")
            return
        try:
            headers = {"Authorization": f"Bearer {token}"}
            r = requests.get(f"{API_URL}/dashboard", headers=headers)
            if r.status_code == 200:
                d = r.json()
                self.stats.setText(f"Pacientes activos: {d['pacientes_activos']}\nCitas hoy: {d['citas_hoy']}\nIngresos mes: {d['ingresos_mes']:,}")
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
        self.setStyleSheet("background:#23272f;color:#e1e1e1;QListWidget {background:#353a47;color:white;border-radius:8px;font-size:15px;}")
        self.load(token)

    def load(self, token):
        if USE_LOCAL_DB:
            try:
                db_path = settings.database_url.replace("sqlite:///", "")
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("SELECT id_paciente, datos_sensibles_encriptados, telefono_encriptado FROM Pacientes WHERE activo = 1")
                self.list.clear()
                for id_p, datos_blob, tel_blob in cur.fetchall():
                    datos = {}
                    try:
                        datos = security.decrypt_data(datos_blob) if datos_blob else {}
                    except Exception:
                        datos = {}
                    telefono = ""
                    try:
                        if tel_blob:
                            t = security.decrypt_data(tel_blob)
                            telefono = t.get("telefono","") if isinstance(t, dict) else t
                    except Exception:
                        telefono = ""
                    nombre = datos.get("nombre", "")
                    apellido = datos.get("apellido", "")
                    self.list.addItem(f"{nombre} {apellido} - {telefono}")
                conn.close()
            except Exception as e:
                self.list.clear()
                self.list.addItem("Error leyendo la DB local")
            return

        try:
            headers = {"Authorization": f"Bearer {token}"}
            r = requests.get(f"{API_URL}/pacientes", headers=headers)
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

        # Inicializador separado (usa diálogos para pedir contraseña)
        try:
            ensure_initial_user_gui(self)
        except Exception as e:
            QMessageBox.critical(self, "Error inicializando usuario", str(e))

        self.show_login()

    def show_login(self):
        if self.menu_bar:
            self.menu_bar.setParent(None)
            self.menu_bar = None
        self.stacked.addWidget(LoginPage(self.on_login))
        self.stacked.setCurrentIndex(self.stacked.count() - 1)

    def on_login(self, token):
        self.token = token
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