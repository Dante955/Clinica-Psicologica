import sys
import os
import logging
import socket
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import sys
import os
import logging
import socket
import configparser

# --- 1. Funciones de Utilidad (Config & Logging) ---
# Deben definirse ANTES de importar los módulos del núcleo,
# porque esos módulos inicializan la BB.DD. al importarse.

def get_base_path():
    """Retorna la ruta base donde se ejecuta la aplicación (o el exe)."""
    if getattr(sys, 'frozen', False):
         # Si es un .exe, la ruta es la del ejecutable
        return os.path.dirname(sys.executable)
    # Si es script, la ruta es la actual (o la del script principal)
    return os.path.abspath(".")

def resource_path(relative_path):
    """ Obtiene la ruta absoluta al recurso, funciona para desarrollo y para PyInstaller. """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    else:
        # No estamos empaquetados, la ruta es relativa al script principal
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def setup_logging_early():
    """Configura el logging antes de cargar nada más."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Buscar config.ini junto al ejecutable o en la raíz
    config_path = os.path.join(get_base_path(), 'config.ini')
    
    log_level = logging.INFO
    if os.path.exists(config_path):
        try:
            config = configparser.ConfigParser()
            config.read(config_path, encoding='utf-8')
            level_str = config.get('logging', 'level', fallback='INFO').upper()
            log_level = getattr(logging, level_str, logging.INFO)
        except Exception:
            pass # Usar default si falla

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "clinic_audit.log"), encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True # Forzar reconfiguración si ya existía
    )
    logging.info("="*50)
    logging.info(f"Iniciando aplicación. Config path: {config_path}")

# --- 2. CONFIGURAR LOGGING AHORA ---
setup_logging_early()

# --- 3. Importaciones de Módulos Locales ---
# (Ahora el logging ya está listo para capturar lo que pase aquí)
from core.authentication import AuthService
from database.models import UserRole

# --- 4. Importaciones de GUI ---
import matplotlib
matplotlib.use('QtAgg')

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyleFactory
# Las ventanas se importan dentro de Application para evitar ciclos o cargas prematuras
from core.backup_manager import create_automatic_backup

class Application:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.set_app_icon()
        # setup_logging YA SE HIZO
        
        # Crear respaldo automático de la base de datos
        logging.info("Creando respaldo automático de la base de datos...")
        create_automatic_backup()
        
        self.auth_service = AuthService()
        self.main_win = None

        # --- IMPORTACIONES MOVIDAS AQUÍ ---
        # Importamos los componentes de la UI DESPUÉS de crear QApplication
        from ui.login_window import LoginWindow
        from ui.main_window import MainWindow 
        self.MainWindow = MainWindow # Guardamos la clase para usarla después

        # Establecer un tema base para un look más moderno
        self.app.setStyle(QStyleFactory.create('Fusion'))

        # Aplicar la hoja de estilos global
        self.set_app_stylesheet()

        # Iniciar la ventana de login
        self.login_win = LoginWindow(self.auth_service)
        self.login_win.login_successful.connect(self.on_login_success)

    def run(self):
        """Muestra la ventana de login y ejecuta la aplicación."""
        logging.info("Mostrando ventana de login.")
        self.show_login_window()
        sys.exit(self.app.exec())

    def on_login_success(self, auth_service: AuthService):
        """Slot que se ejecuta cuando el login es exitoso."""
        user = auth_service.current_user
        role_enum = auth_service.get_current_user_role()  # Esto ahora devuelve un enum
        role = role_enum.value if role_enum else "UNKNOWN"
        hostname = socket.gethostname()
        logging.info(f"Inicio de sesión exitoso para el usuario '{user.username}' con rol '{role}' desde el equipo '{hostname}'.")

        # --- AÑADIDO: Enviar recordatorios de citas ---
        # Solo el admin o el personal de soporte se encargan de esto al iniciar sesión
        if auth_service.get_current_user_role() in [UserRole.ADMIN, UserRole.SOPORTE]:
            logging.info(f"El rol '{role}' permite el envío de notificaciones. Iniciando tarea.")
            from core.notification_service import NotificationService
            try:
                notification_service = NotificationService(config_path=resource_path('config.ini'))
                # Solo intentamos enviar si la configuración de email existe
                if notification_service.is_configured():
                    notification_service.send_appointment_reminders()
                    logging.info("Proceso de envío de recordatorios de citas finalizado.")
                else:
                    logging.warning("El servicio de notificaciones no está configurado en 'config.ini'. Se omite el envío de correos.")
            except Exception as e:
                logging.error(f"Ocurrió un error durante el envío de recordatorios: {e}", exc_info=True)
        
        self.main_win = self.MainWindow(auth_service)
        self.main_win.logout_requested.connect(self.handle_logout) # Conectar la señal
        self.main_win.showMaximized() # Mostrar la ventana maximizada
        self.login_win.close()

    def handle_logout(self):
        """Cierra la ventana principal y muestra la de login."""
        if self.auth_service.current_user:
            logging.info(f"Cerrando sesión para el usuario '{self.auth_service.current_user.username}'.")

        self.main_win.close()
        self.main_win = None # Liberar la referencia
        self.auth_service.logout()
        self.show_login_window()

    def show_login_window(self):
        """Muestra la ventana de login."""
        self.login_win.center()
        self.login_win.show()
    
    def set_app_stylesheet(self):
        """Carga y aplica la hoja de estilos QSS desde un archivo."""
        try:
            with open(resource_path('styles.qss'), 'r') as f:
                style = f.read()
                self.app.setStyleSheet(style)
        except FileNotFoundError:
            logging.warning("No se encontró el archivo 'styles.qss'. La aplicación se ejecutará sin estilos personalizados.")
        except Exception as e:
            logging.error(f"Error al cargar la hoja de estilos: {e}", exc_info=True)

    def set_app_icon(self):
        """Establece el icono de la aplicación."""
        icon_path = resource_path('assets/icon.png')
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            self.app.setWindowIcon(app_icon)
            logging.info("Icono de la aplicación cargado correctamente.")
        else:
            logging.warning(f"No se encontró el archivo de icono en '{icon_path}'.")

def initialize_database():
    """Crea la BD y usuarios por defecto si no existen."""
    # Importaciones necesarias solo para esta función
    # Nota: AuthService y UserRole ya están importados arriba si se necesitan, pero aquí se reimportaban
    from core.authentication import AuthService, UserRole 
    from database.models import setup_database, User
    from database.database_manager import session_scope

    setup_database()
    auth = AuthService() # Usar una sola instancia
    with session_scope() as session:
        # Crear usuario admin si no existe
        if not session.query(User).filter_by(username="admin").first():
            logging.info("No se encontró usuario 'admin'. Creando usuario por defecto.")
            auth.create_user(
                username="admin",
                password="admin123",
                role=UserRole.ADMIN,
                full_name="Administrador del Sistema"
            )
        
        # Crear usuario psicólogo si no existe
        if not session.query(User).filter_by(username="psico1").first():
            logging.info("No se encontró usuario 'psico1'. Creando usuario por defecto.")
            auth.create_user(
                username="psico1",
                password="psico123",
                role=UserRole.PSICOLOGO,
                full_name="Dr. Armando Casas",
                specialization="Terapia Cognitivo-Conductual"
            )
        
        # Crear usuario soporte si no existe
        if not session.query(User).filter_by(username="steve").first():
            logging.info("No se encontró usuario 'steve'. Creando usuario por defecto.")
            auth.create_user(
                username="steve",
                password="1234",
                role=UserRole.SOPORTE,
                full_name="Steven Rafael Blanco Macias"
            )

if __name__ == "__main__":
    # Logging ya configurado al inicio del script.
    
    # 1. Asegúrate de que la base de datos y los usuarios existan
    initialize_database()

    # 2. Inicia la aplicación
    app_instance = Application()
    app_instance.run()