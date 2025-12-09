from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog, QLineEdit
)
from PySide6.QtCore import Qt

from database.database_manager import session_scope
from database.models import User
from ui.dialogs.user_form_dialog import UserFormDialog
from core.authentication import AuthService

class UserManagementPanel(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.auth_service = AuthService()
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Botones de Acción ---
        button_layout = QHBoxLayout()
        
        self.add_user_button = QPushButton("➕ Añadir Usuario")
        self.add_user_button.clicked.connect(self.add_user)
        
        self.edit_user_button = QPushButton("✏️ Editar Usuario")
        self.edit_user_button.clicked.connect(self.edit_user)

        self.reset_password_button = QPushButton("🔑 Restablecer Contraseña")
        self.reset_password_button.clicked.connect(self.reset_password)
        
        self.delete_user_button = QPushButton("🗑️ Eliminar Usuario")
        self.delete_user_button.clicked.connect(self.delete_user)

        button_layout.addWidget(self.add_user_button)
        button_layout.addWidget(self.edit_user_button)
        button_layout.addWidget(self.reset_password_button)
        button_layout.addWidget(self.delete_user_button)
        button_layout.addStretch()

        # --- Tabla de Usuarios ---
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(3)
        self.users_table.setHorizontalHeaderLabels(["ID", "Nombre de Usuario", "Rol"])
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers) # No editable directamente
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows) # Seleccionar filas completas
        self.users_table.setSelectionMode(QTableWidget.SingleSelection) # Solo una fila a la vez
        
        # Ajustar columnas al contenido
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.users_table)

    def load_users(self):
        """Carga o recarga los usuarios desde la BD a la tabla."""
        self.users_table.setRowCount(0) # Limpiar tabla
        with session_scope() as session:
            users = session.query(User).order_by(User.id).all()
            self.users_table.setRowCount(len(users))
            for row, user in enumerate(users):
                self.users_table.setItem(row, 0, QTableWidgetItem(str(user.id)))
                self.users_table.setItem(row, 1, QTableWidgetItem(user.username))
                self.users_table.setItem(row, 2, QTableWidgetItem(user.role))  # role ya es un string
                # Centrar el texto del ID y el Rol
                self.users_table.item(row, 0).setTextAlignment(Qt.AlignCenter)
                self.users_table.item(row, 2).setTextAlignment(Qt.AlignCenter)

    def add_user(self):
        """
        Abre un diálogo para crear un nuevo usuario y recarga la tabla si tiene éxito.
        """
        dialog = UserFormDialog(current_user=self.current_user, parent=self)
        if dialog.exec(): # exec() devuelve True si el diálogo se aceptó (ej. se guardó)
            self.load_users()

    def edit_user(self):
        """
        Abre un diálogo para editar el usuario seleccionado.
        """
        selected_row = self.users_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, selecciona un usuario de la tabla para editar.")
            return
        
        user_id = int(self.users_table.item(selected_row, 0).text())
        dialog = UserFormDialog(user_id=user_id, current_user=self.current_user, parent=self)
        if dialog.exec():
            self.load_users()

    def reset_password(self):
        """
        Restablece la contraseña del usuario seleccionado.
        """
        selected_row = self.users_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, selecciona un usuario de la tabla.")
            return

        user_id = int(self.users_table.item(selected_row, 0).text())
        username = self.users_table.item(selected_row, 1).text()

        new_password, ok = QInputDialog.getText(self, "Restablecer Contraseña", 
                                                  f"Introduce la nueva contraseña para '{username}':", 
                                                  echo=QLineEdit.Password)

        if ok and new_password:
            self.auth_service.reset_password(user_id, new_password)
            QMessageBox.information(self, "Éxito", f"La contraseña para '{username}' ha sido restablecida.")
        elif ok:
            QMessageBox.warning(self, "Contraseña Vacía", "La contraseña no puede estar vacía.")

    def delete_user(self):
        """
        Elimina el usuario seleccionado tras confirmación.
        """
        selected_row = self.users_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, selecciona un usuario de la tabla para eliminar.")
            return

        user_id = int(self.users_table.item(selected_row, 0).text())
        username = self.users_table.item(selected_row, 1).text()

        reply = QMessageBox.question(self, "Confirmar Eliminación", 
                                     f"¿Estás seguro de que quieres eliminar al usuario '{username}' (ID: {user_id})?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            with session_scope() as session:
                user_to_delete = session.query(User).filter_by(id=user_id).first()
                session.delete(user_to_delete)
            QMessageBox.information(self, "Éxito", f"Usuario '{username}' eliminado correctamente.")
            self.load_users() # Recargar la tabla

    def refresh_data(self):
        """Método público para refrescar los datos del panel."""
        self.load_users()