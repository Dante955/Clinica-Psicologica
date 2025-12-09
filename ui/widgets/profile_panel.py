from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QMessageBox, QGroupBox, QTabWidget
)
from PySide6.QtCore import Qt

from database.database_manager import session_scope
from database.models import User
from werkzeug.security import check_password_hash, generate_password_hash
from ui.widgets.email_config_panel import EmailConfigPanel


class ProfilePanel(QWidget):
    def __init__(self, current_user: User, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Crear pestañas
        tabs = QTabWidget()
        
        # Pestaña de perfil
        profile_tab = self.create_profile_tab()
        tabs.addTab(profile_tab, "👤 Mi Perfil")
        
        # Pestaña de configuración de email (solo para ADMIN y SOPORTE)
        from database.models import UserRole
        if self.current_user.role in [UserRole.ADMIN.value, UserRole.SOPORTE.value]:
            email_config_tab = EmailConfigPanel()
            tabs.addTab(email_config_tab, "📧 Configuración de Email")
        
        main_layout.addWidget(tabs)

    def create_profile_tab(self):
        """Crea la pestaña de información del perfil."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # --- Grupo de Información del Perfil ---
        info_group = QGroupBox("Información del Perfil")
        info_layout = QFormLayout(info_group)
        info_layout.setLabelAlignment(Qt.AlignRight)

        username_label = QLabel(f"<b>{self.current_user.username}</b>")
        role_label = QLabel(self.current_user.role.capitalize())  # role ya es un string
        fullname_label = QLabel(self.current_user.full_name)

        info_layout.addRow("Nombre de Usuario:", username_label)
        info_layout.addRow("Nombre Completo:", fullname_label)
        info_layout.addRow("Rol:", role_label)
        
        if self.current_user.specialization:
            specialization_label = QLabel(self.current_user.specialization)
            info_layout.addRow("Especialización:", specialization_label)

        # --- Grupo para Cambiar Contraseña ---
        password_group = QGroupBox("Cambiar Contraseña")
        password_layout = QFormLayout(password_group)
        password_layout.setLabelAlignment(Qt.AlignRight)

        self.current_password_input = QLineEdit()
        self.current_password_input.setEchoMode(QLineEdit.Password)
        
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)

        password_layout.addRow("Contraseña Actual:", self.current_password_input)
        password_layout.addRow("Nueva Contraseña:", self.new_password_input)
        password_layout.addRow("Confirmar Nueva Contraseña:", self.confirm_password_input)

        self.change_password_button = QPushButton("Cambiar Contraseña")
        self.change_password_button.clicked.connect(self.handle_change_password)

        layout.addWidget(info_group)
        layout.addWidget(password_group)
        layout.addWidget(self.change_password_button, 0, Qt.AlignRight)
        layout.addStretch()
        
        return widget

    def handle_change_password(self):
        current_pass = self.current_password_input.text()
        new_pass = self.new_password_input.text()
        confirm_pass = self.confirm_password_input.text()

        if not all([current_pass, new_pass, confirm_pass]):
            QMessageBox.warning(self, "Campos Vacíos", "Por favor, rellene todos los campos para cambiar la contraseña.")
            return

        with session_scope() as session:
            user = session.query(User).get(self.current_user.id)
            
            if not check_password_hash(user.hashed_password, current_pass):
                QMessageBox.critical(self, "Error", "La contraseña actual es incorrecta.")
                return

            if new_pass != confirm_pass:
                QMessageBox.warning(self, "Error", "La nueva contraseña y su confirmación no coinciden.")
                return
            
            if len(new_pass) < 6:
                QMessageBox.warning(self, "Contraseña Débil", "La nueva contraseña debe tener al menos 6 caracteres.")
                return

            # Si todo es correcto, actualizamos la contraseña
            user.hashed_password = generate_password_hash(new_pass)
            session.commit()

        QMessageBox.information(self, "Éxito", "¡Contraseña actualizada correctamente!")
        
        # Limpiar campos
        self.current_password_input.clear()
        self.new_password_input.clear()
        self.confirm_password_input.clear()
