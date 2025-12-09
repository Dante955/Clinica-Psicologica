"""
Panel de Configuración de Email

Este widget permite a los usuarios configurar los parámetros de email
para el envío de notificaciones y recordatorios.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QGroupBox, QMessageBox,
    QSpinBox
)
from PySide6.QtCore import Qt
import configparser
import os


class EmailConfigPanel(QWidget):
    """Panel para configurar los parámetros de email."""
    
    def __init__(self):
        super().__init__()
        self.config_path = self.get_config_path()
        self.setup_ui()
        self.load_current_config()
    
    def get_config_path(self):
        """Obtiene la ruta al archivo config.ini"""
        # Buscar config.ini en el directorio raíz del proyecto
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Subir dos niveles desde ui/widgets/ hasta la raíz
        project_root = os.path.dirname(os.path.dirname(current_dir))
        return os.path.join(project_root, 'config.ini')
    
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("⚙️ Configuración de Email")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #5E81AC;")
        layout.addWidget(title)
        
        # Descripción
        description = QLabel(
            "Configure los parámetros de email para enviar recordatorios de citas.\n"
            "La contraseña de aplicación de Google se puede obtener en: "
            "https://myaccount.google.com/apppasswords"
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(description)
        
        # Grupo de configuración SMTP
        smtp_group = QGroupBox("Configuración del Servidor SMTP")
        smtp_layout = QVBoxLayout()
        
        # Servidor SMTP
        smtp_server_layout = QHBoxLayout()
        smtp_server_layout.addWidget(QLabel("Servidor SMTP:"))
        self.smtp_server_input = QLineEdit()
        self.smtp_server_input.setPlaceholderText("smtp.gmail.com")
        smtp_server_layout.addWidget(self.smtp_server_input)
        smtp_layout.addLayout(smtp_server_layout)
        
        # Puerto
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Puerto:"))
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(587)
        self.port_input.setMaximumWidth(100)
        port_layout.addWidget(self.port_input)
        port_layout.addStretch()
        smtp_layout.addLayout(port_layout)
        
        smtp_group.setLayout(smtp_layout)
        layout.addWidget(smtp_group)
        
        # Grupo de credenciales
        credentials_group = QGroupBox("Credenciales de Email")
        credentials_layout = QVBoxLayout()
        
        # Email del remitente
        sender_layout = QHBoxLayout()
        sender_layout.addWidget(QLabel("Email:"))
        self.sender_email_input = QLineEdit()
        self.sender_email_input.setPlaceholderText("tu-email@gmail.com")
        sender_layout.addWidget(self.sender_email_input)
        credentials_layout.addLayout(sender_layout)
        
        # Contraseña de aplicación
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Contraseña de Aplicación:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("xxxx xxxx xxxx xxxx")
        password_layout.addWidget(self.password_input)
        credentials_layout.addLayout(password_layout)
        
        # Nota sobre contraseña de aplicación
        password_note = QLabel(
            "⚠️ Usa una contraseña de aplicación de Google, no tu contraseña normal.\n"
            "Para generar una: Cuenta de Google → Seguridad → Verificación en 2 pasos → Contraseñas de aplicaciones"
        )
        password_note.setWordWrap(True)
        password_note.setStyleSheet(
            "background-color: #FFF3CD; "
            "border: 1px solid #FFE69C; "
            "border-radius: 5px; "
            "padding: 10px; "
            "color: #856404; "
            "font-size: 12px;"
        )
        credentials_layout.addWidget(password_note)
        
        credentials_group.setLayout(credentials_layout)
        layout.addWidget(credentials_group)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # Botón probar conexión
        self.test_button = QPushButton("🔍 Probar Conexión")
        self.test_button.clicked.connect(self.test_connection)
        self.test_button.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5A6268;
            }
        """)
        buttons_layout.addWidget(self.test_button)
        
        # Botón guardar
        self.save_button = QPushButton("💾 Guardar Configuración")
        self.save_button.clicked.connect(self.save_config)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #5E81AC;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
        """)
        buttons_layout.addWidget(self.save_button)
        
        layout.addLayout(buttons_layout)
        
        # Espaciador al final
        layout.addStretch()
    
    def load_current_config(self):
        """Carga la configuración actual desde config.ini"""
        if not os.path.exists(self.config_path):
            return
        
        config = configparser.ConfigParser()
        config.read(self.config_path, encoding='utf-8')
        
        if config.has_section('email'):
            self.smtp_server_input.setText(
                config.get('email', 'smtp_server', fallback='smtp.gmail.com')
            )
            self.port_input.setValue(
                config.getint('email', 'port', fallback=587)
            )
            self.sender_email_input.setText(
                config.get('email', 'sender_email', fallback='')
            )
            self.password_input.setText(
                config.get('email', 'password', fallback='')
            )
    
    def save_config(self):
        """Guarda la configuración en config.ini"""
        # Validar campos
        if not self.sender_email_input.text():
            QMessageBox.warning(
                self, 
                "Campos Incompletos", 
                "Por favor, ingresa el email del remitente."
            )
            return
        
        if not self.password_input.text():
            QMessageBox.warning(
                self, 
                "Campos Incompletos", 
                "Por favor, ingresa la contraseña de aplicación de Google."
            )
            return
        
        try:
            config = configparser.ConfigParser()
            
            # Leer configuración existente
            if os.path.exists(self.config_path):
                config.read(self.config_path, encoding='utf-8')
            
            # Actualizar o crear sección [email]
            if not config.has_section('email'):
                config.add_section('email')
            
            config.set('email', 'smtp_server', self.smtp_server_input.text())
            config.set('email', 'port', str(self.port_input.value()))
            config.set('email', 'sender_email', self.sender_email_input.text())
            config.set('email', 'password', self.password_input.text())
            
            # Guardar archivo
            with open(self.config_path, 'w') as configfile:
                config.write(configfile)
            
            QMessageBox.information(
                self,
                "Configuración Guardada",
                "La configuración de email se ha guardado correctamente.\n\n"
                "Los cambios se aplicarán en el próximo envío de emails."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error al Guardar",
                f"No se pudo guardar la configuración:\n{str(e)}"
            )
    
    def test_connection(self):
        """Prueba la conexión SMTP con las credenciales proporcionadas."""
        import smtplib
        from email.mime.text import MIMEText
        
        # Validar campos
        if not self.sender_email_input.text() or not self.password_input.text():
            QMessageBox.warning(
                self,
                "Campos Incompletos",
                "Por favor, completa todos los campos antes de probar la conexión."
            )
            return
        
        try:
            # Intentar conectar al servidor SMTP
            server = smtplib.SMTP(
                self.smtp_server_input.text(), 
                self.port_input.value(),
                timeout=10
            )
            server.starttls()
            server.login(
                self.sender_email_input.text(), 
                self.password_input.text()
            )
            server.quit()
            
            QMessageBox.information(
                self,
                "Conexión Exitosa",
                "✅ La conexión al servidor SMTP fue exitosa.\n\n"
                "Las credenciales son válidas y el servidor está accesible."
            )
            
        except smtplib.SMTPAuthenticationError:
            QMessageBox.critical(
                self,
                "Error de Autenticación",
                "❌ Las credenciales son incorrectas.\n\n"
                "Verifica:\n"
                "• El email es correcto\n"
                "• Estás usando una contraseña de aplicación (no tu contraseña normal)\n"
                "• La verificación en 2 pasos está activada en tu cuenta de Google"
            )
        except smtplib.SMTPException as e:
            QMessageBox.critical(
                self,
                "Error SMTP",
                f"❌ Error al conectar con el servidor SMTP:\n\n{str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error de Conexión",
                f"❌ No se pudo conectar al servidor:\n\n{str(e)}\n\n"
                "Verifica tu conexión a Internet y que el servidor SMTP sea correcto."
            )
