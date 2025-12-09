import sys
from PySide6.QtCore import Signal
from PySide6.QtGui import QScreen
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, 
    QPushButton, QLabel, QMessageBox
)
from core.authentication import AuthService
from database.models import UserRole # Necesario para el bloque __main__

class LoginWindow(QWidget):
    # Señal que se emitirá cuando el login sea exitoso. Pasará el objeto auth_service.
    login_successful = Signal(AuthService)

    def __init__(self, auth_service: AuthService):
        super().__init__()
        self.auth_service = auth_service
        self.setWindowTitle("Inicio de Sesión")
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        # Establecer un tamaño fijo para la ventana
        self.setFixedSize(340, 420)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30) # Añadir márgenes
        layout.setSpacing(15) # Espaciado entre widgets

        self.title_label = QLabel("Bienvenido")
        self.title_label.setObjectName("titleLabel") # ID para el estilo

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Usuario")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)

        login_button = QPushButton("Ingresar")
        login_button.setObjectName("loginButton") # ID para el estilo
        login_button.clicked.connect(self.handle_login)
        
        # Añadir widgets al layout
        layout.addWidget(self.title_label)
        layout.addStretch() # Espacio flexible
        layout.addWidget(QLabel("Usuario:"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Contraseña:"))
        layout.addWidget(self.password_input)
        layout.addStretch() # Espacio flexible
        layout.addWidget(login_button)

        self.setLayout(layout)

    def apply_styles(self):
        """
        Aplica la hoja de estilos (QSS) para una apariencia moderna.
        """
        stylesheet = """
            QWidget {
                background-color: #2E3440;
                color: #ECEFF4;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            #titleLabel {
                font-size: 28px;
                font-weight: bold;
                color: #88C0D0;
                qproperty-alignment: 'AlignCenter';
            }
            QLabel {
                color: #D8DEE9;
            }
            QLineEdit {
                background-color: #4C566A;
                border: 1px solid #4C566A;
                border-radius: 5px;
                padding: 10px;
                color: #ECEFF4;
            }
            QLineEdit:focus {
                border: 1px solid #88C0D0;
            }
            #loginButton {
                background-color: #5E81AC;
                border: none;
                border-radius: 5px;
                padding: 12px;
                font-weight: bold;
                color: #ECEFF4;
            }
            #loginButton:hover {
                background-color: #81A1C1;
            }
            #loginButton:pressed {
                background-color: #88C0D0;
            }
        """
        self.setStyleSheet(stylesheet)

    def center(self):
        """
        Centra la ventana en la pantalla principal.
        """
        pantalla = QScreen.availableGeometry(QApplication.primaryScreen())
        geometria = self.frameGeometry()
        geometria.moveCenter(pantalla.center())
        self.move(geometria.topLeft())

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if self.auth_service.login(username, password):
            # Limpiar los campos de entrada
            self.username_input.clear()
            self.password_input.clear()
            # Emitimos la señal con el servicio de autenticación que contiene el usuario logueado
            self.login_successful.emit(self.auth_service)
            self.close() # Cierra la ventana de login
        else:
            QMessageBox.warning(self, "Error", "Usuario o contraseña incorrectos.")

# Ejemplo de cómo ejecutarlo
if __name__ == '__main__':
    # Esto es solo para probar esta ventana de forma aislada
    app = QApplication(sys.argv)
    auth = AuthService()
    
    # Para probar, necesitarías crear un usuario primero.
    # Descomenta las siguientes líneas si es necesario:
    # from database.database_manager import session_scope
    # from database.models import User
    # with session_scope() as session:
    #     if not session.query(User).filter_by(username="admin").first():
    #         auth.create_user("admin", "admin123", UserRole.ADMIN)
    
    window = LoginWindow(auth)
    window.center() # Centra la ventana
    window.show()
    sys.exit(app.exec())