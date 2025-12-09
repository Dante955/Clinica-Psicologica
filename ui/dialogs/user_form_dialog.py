from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, 
    QPushButton, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt

from database.models import User, UserRole
from database.database_manager import session_scope
from core.authentication import AuthService
from werkzeug.security import generate_password_hash

class UserFormDialog(QDialog):
    def __init__(self, user_id=None, current_user=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.current_user = current_user
        self.is_edit_mode = self.user_id is not None

        self.setWindowTitle("Editar Usuario" if self.is_edit_mode else "Añadir Usuario")
        self.setMinimumWidth(400)

        self.setup_ui()

        if self.is_edit_mode:
            self.load_user_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- Campos del formulario ---
        self.username_input = QLineEdit()
        self.full_name_input = QLineEdit()  # Campo de nombre completo
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setEchoMode(QLineEdit.Password)
        self.role_combo = QComboBox()
        
        # Llenar el ComboBox con los roles del enum
        # Solo ADMIN y SOPORTE pueden crear usuarios ADMIN
        for role in UserRole:
            # Filtrar el rol ADMIN si el usuario actual no es ADMIN o SOPORTE
            if role == UserRole.ADMIN:
                if self.current_user and self.current_user.role not in [UserRole.ADMIN.value, UserRole.SOPORTE.value]:
                    continue  # Saltar el rol ADMIN
            self.role_combo.addItem(role.value.capitalize(), role.value)

        form_layout.addRow("Nombre de Usuario:", self.username_input)
        form_layout.addRow("Nombre Completo:", self.full_name_input)
        
        password_label = "Contraseña (dejar en blanco para no cambiar):" if self.is_edit_mode else "Contraseña:"
        form_layout.addRow(password_label, self.password_input)
        form_layout.addRow("Confirmar Contraseña:", self.password_confirm_input)
        form_layout.addRow("Rol:", self.role_combo)

        # --- Botones de Acción ---
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_user)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)

        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
    
    def load_user_data(self):
        """Carga los datos del usuario en el formulario para edición."""
        with session_scope() as session:
            user = session.query(User).filter_by(id=self.user_id).first()
            if user:
                self.username_input.setText(user.username)
                self.full_name_input.setText(user.full_name or "")
                # Encontrar el índice del rol en el ComboBox
                index = self.role_combo.findData(user.role)
                if index != -1:
                    self.role_combo.setCurrentIndex(index)

    def save_user(self):
        """Guarda el usuario (nuevo o editado) en la base de datos."""
        username = self.username_input.text().strip()
        full_name = self.full_name_input.text().strip()
        password = self.password_input.text()
        password_confirm = self.password_confirm_input.text()
        role_value = self.role_combo.currentData()

        if not username:
            QMessageBox.warning(self, "Campo Requerido", "El nombre de usuario no puede estar vacío.")
            return

        if not full_name:
            QMessageBox.warning(self, "Campo Requerido", "El nombre completo no puede estar vacío.")
            return

        if password != password_confirm:
            QMessageBox.warning(self, "Error de Contraseña", "Las contraseñas no coinciden.")
            return

        if not self.is_edit_mode or password:
            if len(password) < 8:
                QMessageBox.warning(self, "Contraseña Débil", "La contraseña debe tener al menos 8 caracteres.")
                return

        if not self.is_edit_mode and not password:
            QMessageBox.warning(self, "Campo Requerido", "La contraseña es obligatoria para nuevos usuarios.")
            return

        try:
            with session_scope() as session:
                if self.is_edit_mode:
                    # --- Modo Edición ---
                    user_to_update = session.query(User).filter_by(id=self.user_id).first()
                    if user_to_update:
                        user_to_update.username = username
                        user_to_update.full_name = full_name
                        user_to_update.role = role_value
                        if password: # Solo actualiza la contraseña si se proporcionó una nueva
                            user_to_update.hashed_password = generate_password_hash(password)
                else:
                    # --- Modo Creación ---
                    # Verificar si el usuario ya existe
                    if session.query(User).filter_by(username=username).first():
                        QMessageBox.warning(self, "Error", f"El nombre de usuario '{username}' ya existe.")
                        return
                    
                    hashed_password = generate_password_hash(password)
                    
                    new_user = User(
                        username=username,
                        hashed_password=hashed_password,
                        role=role_value,
                        full_name=full_name
                    )
                    session.add(new_user)
            
            QMessageBox.information(self, "Éxito", "Usuario guardado correctamente.")
            self.accept() # Cierra el diálogo con éxito

        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", f"Ocurrió un error al guardar:\n{e}")
            self.reject()