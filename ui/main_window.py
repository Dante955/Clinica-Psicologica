from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal
from core.authentication import AuthService, UserRole

# Usamos importaciones absolutas desde la raíz del proyecto
from ui.widgets.user_management_panel import UserManagementPanel
from ui.widgets.psychologist_panel import PsychologistPanel
from ui.widgets.financial_panel import FinancialPanel
from ui.widgets.profile_panel import ProfilePanel
from ui.widgets.audit_log_viewer import AuditLogViewer
from ui.widgets.database_config_panel import DatabaseConfigPanel
from ui.widgets.email_config_panel import EmailConfigPanel

class MainWindow(QMainWindow):
    # Señal para notificar que el usuario quiere cerrar sesión
    logout_requested = Signal()

    def __init__(self, auth_service: AuthService):
        super().__init__()
        self.auth_service = auth_service
        self.current_user = auth_service.current_user

        self.setWindowTitle(f"Clínica Psicológica - Bienvenido {self.current_user.username}")
        self.setMinimumSize(800, 600)

        # Widget central y layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # --- Layout para el botón de Cerrar Sesión ---
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addStretch() # Empuja el botón hacia la derecha

        self.logout_button = QPushButton("🔒 Cerrar Sesión")
        self.logout_button.clicked.connect(self.handle_logout)
        self.logout_button.setFixedWidth(150) # Ancho fijo para el botón
        
        # --- NUEVO: Botón de Actualizar Datos ---
        self.refresh_button = QPushButton("🔄 Actualizar Datos")
        self.refresh_button.clicked.connect(self.handle_refresh)
        self.refresh_button.setFixedWidth(150)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #5E81AC;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
        """)

        top_bar_layout.addWidget(self.refresh_button)
        top_bar_layout.addWidget(self.logout_button)

        self.layout.addLayout(top_bar_layout)
        
        # --- Contenedor de pestañas ---
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.setup_ui_for_role()

    def handle_refresh(self):
        """Actualiza los datos de todas las pestañas."""
        import logging
        logging.info("Iniciando actualización global de datos...")
        
        # Recorrer todas las pestañas
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            # Verificar si el widget tiene el método refresh_data
            if hasattr(widget, 'refresh_data'):
                try:
                    widget.refresh_data()
                    logging.info(f"Pestaña '{self.tabs.tabText(i)}' actualizada.")
                except Exception as e:
                    logging.error(f"Error al actualizar pestaña '{self.tabs.tabText(i)}': {e}")
            else:
                logging.debug(f"Pestaña '{self.tabs.tabText(i)}' no tiene método refresh_data.")
        
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Datos Actualizados", "La información se ha recargado correctamente.")



    def handle_logout(self):
        """Emite la señal para cerrar la sesión."""
        self.logout_requested.emit()

    def setup_ui_for_role(self):
        """
        Añade las pestañas correspondientes según el rol del usuario.
        """
        role = self.auth_service.get_current_user_role()
        
        import logging
        logging.info(f"Configurando UI para rol: {role}")

        # Pestañas para roles con acceso a la gestión de pacientes
        if role in [UserRole.ADMIN, UserRole.PSICOLOGO]:
            logging.info("Agregando panel de Pacientes y Citas")
            psychologist_widget = PsychologistPanel(self.current_user)
            self.tabs.addTab(psychologist_widget, "Pacientes y Citas")

        # Pestañas para Admin y Soporte
        if role in [UserRole.ADMIN, UserRole.SOPORTE]:
            logging.info("Agregando panel de Gestión de Usuarios")
            user_management_widget = UserManagementPanel(current_user=self.current_user)
            self.tabs.addTab(user_management_widget, "Gestión de Usuarios")

        # Pestañas exclusivas para Admin
        if role == UserRole.ADMIN:
            logging.info("Agregando panel de Reportes Financieros")
            financial_widget = FinancialPanel()
            self.tabs.addTab(financial_widget, "Reportes Financieros")

        # Pestañas exclusivas para Soporte
        if role == UserRole.SOPORTE:
            logging.info("Usuario SOPORTE detectado, agregando pestañas especiales...")
            
            try:
                logging.info("Creando panel de Auditoría...")
                audit_widget = AuditLogViewer(self.current_user)
                self.tabs.addTab(audit_widget, "Auditoría")
                logging.info("✓ Panel de Auditoría agregado")
            except Exception as e:
                logging.error(f"✗ Error al crear panel de Auditoría: {e}", exc_info=True)
            
            try:
                logging.info("Creando panel de Base de Datos...")
                db_config_widget = DatabaseConfigPanel(self.current_user)
                self.tabs.addTab(db_config_widget, "⚙️ Base de Datos")
                logging.info("✓ Panel de Base de Datos agregado")
            except Exception as e:
                logging.error(f"✗ Error al crear panel de Base de Datos: {e}", exc_info=True)
            
            try:
                logging.info("Creando panel de Email...")
                email_config_widget = EmailConfigPanel()
                self.tabs.addTab(email_config_widget, "📧 Email")
                logging.info("✓ Panel de Email agregado")
            except Exception as e:
                logging.error(f"✗ Error al crear panel de Email: {e}", exc_info=True)

        # Puedes añadir una pestaña de "Mi Perfil" para todos
        logging.info("Agregando panel de Mi Perfil")
        profile_widget = ProfilePanel(self.current_user)
        self.tabs.addTab(profile_widget, "Mi Perfil")
        
        logging.info(f"Total de pestañas agregadas: {self.tabs.count()}")