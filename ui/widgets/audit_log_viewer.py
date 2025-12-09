# ui/widgets/audit_log_viewer.py
import os
import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QMessageBox, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

LOG_FILE_PATH = os.path.join("logs", "clinic_audit.log")

class AuditLogViewer(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.setup_ui()
        self.load_log_file()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Layout para el título y el botón de refrescar
        top_layout = QHBoxLayout()
        title = QLabel("Auditoría de Inicio de Sesión")
        title.setObjectName("panelTitle")
        
        self.refresh_button = QPushButton("🔄 Refrescar")
        self.refresh_button.clicked.connect(self.load_log_file)
        self.refresh_button.setFixedWidth(120)

        top_layout.addWidget(title)
        top_layout.addStretch()
        top_layout.addWidget(self.refresh_button)

        layout.addLayout(top_layout)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFontFamily("Courier") # Fuente monoespaciada para mejor legibilidad
        
        layout.addWidget(self.log_display)

    def load_log_file(self):
        """Carga o recarga el contenido del archivo de log."""
        logging.info(f"El usuario '{self.current_user.username}' está viendo el registro de auditoría.")
        try:
            # Abrir con manejo de errores de codificación explícito.
            # 'errors="replace"' sustituirá los caracteres problemáticos por ''.
            with open(LOG_FILE_PATH, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                self.log_display.setPlainText(content)
                self.log_display.verticalScrollBar().setValue(self.log_display.verticalScrollBar().maximum())
        except UnicodeDecodeError as ude:
            # Este bloque es un fallback por si 'errors="replace"' no fuera suficiente.
            # Intenta con una codificación común en Windows.
            logging.warning(f"UnicodeDecodeError al leer el archivo de auditoría con UTF-8. Intentando con 'latin-1'. Error: {ude}", exc_info=True)
            try:
                with open(LOG_FILE_PATH, 'r', encoding='latin-1') as f:
                    content = f.read()
                    self.log_display.setPlainText(f"--- ADVERTENCIA: El archivo de log contiene caracteres no UTF-8. Mostrando con 'latin-1'. ---\n\n{content}")
                    self.log_display.verticalScrollBar().setValue(self.log_display.verticalScrollBar().maximum())
            except Exception as e_fallback:
                error_message = f"No se pudo cargar el archivo de auditoría ni con UTF-8 ni con latin-1: {e_fallback}"
                self.log_display.setPlainText(error_message)
                logging.error(error_message, exc_info=True)
        except FileNotFoundError:
            self.log_display.setPlainText("El archivo de auditoría ('logs/clinic_audit.log') no se ha creado todavía.")
        except Exception as e:
            error_message = f"No se pudo cargar el archivo de auditoría: {e}"
            self.log_display.setPlainText(error_message)
            logging.error(error_message, exc_info=True)