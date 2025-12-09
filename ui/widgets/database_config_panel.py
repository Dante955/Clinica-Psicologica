"""
Panel de Configuración de Base de Datos

Este widget permite gestionar la configuración de la base de datos,
incluyendo SQLite y PostgreSQL, y migrar entre ellas.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QPushButton, 
    QMessageBox, QLineEdit, QProgressBar, QTextEdit, QScrollArea, QFormLayout,
    QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal
import os
import shutil
import configparser
from datetime import datetime
import logging




class DatabaseConfigPanel(QWidget):
    """Panel para gestionar la configuración de la base de datos."""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.logger = logging.getLogger(__name__)
        
        # Initialize migrator
        from database.database_migrator import DatabaseMigrator
        self.migrator = DatabaseMigrator()
        
        self.migration_worker = None
        self.setup_ui()
        self.load_current_config()
    
    def get_db_path(self):
        """Obtiene la ruta al archivo de base de datos SQLite."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        return os.path.join(project_root, 'clinic.db')
    
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("🗄️ Gestión de Base de Datos")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #5E81AC;")
        layout.addWidget(title)
        
        # Current database info
        self.create_current_db_section(layout)
        
        # Database statistics
        self.create_statistics_section(layout)
        
        # MSSQL (SQL Server) configuration
        self.create_mssql_config_section(layout)
        
        # Backup section
        self.create_backup_section(layout)
        
        # Espaciador
        layout.addStretch()
        
        scroll.setWidget(container)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def create_current_db_section(self, parent_layout):
        """Create section showing current database info."""
        group = QGroupBox("📊 Base de Datos Actual")
        layout = QVBoxLayout()
        
        self.current_db_label = QLabel("Cargando información...")
        self.current_db_label.setWordWrap(True)
        self.current_db_label.setStyleSheet("padding: 10px; background-color: #F0F0F0; border-radius: 5px;")
        layout.addWidget(self.current_db_label)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def create_statistics_section(self, parent_layout):
        """Create section showing database statistics."""
        group = QGroupBox("📈 Estadísticas de la Base de Datos")
        layout = QVBoxLayout()
        
        self.stats_label = QLabel("Cargando estadísticas...")
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("padding: 10px; font-family: monospace;")
        layout.addWidget(self.stats_label)
        
        refresh_btn = QPushButton("🔄 Actualizar Estadísticas")
        refresh_btn.clicked.connect(self.load_statistics)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #88C0D0;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #A3D4E6;
            }
        """)
        layout.addWidget(refresh_btn)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    
    def create_mssql_config_section(self, parent_layout):
        """Create MSSQL (SQL Server) configuration section."""
        group = QGroupBox("🪟 Configuración de SQL Server (MSSQL)")
        layout = QVBoxLayout()

        info = QLabel(
            "SQL Server soporta autenticación Windows (Trusted) y SQL Server (usuario/contraseña)."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; font-size: 12px; padding: 5px;")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(10)

        self.mssql_host_input = QLineEdit()
        self.mssql_host_input.setPlaceholderText("localhost")
        form.addRow("Host:", self.mssql_host_input)

        self.mssql_port_input = QLineEdit()
        self.mssql_port_input.setPlaceholderText("1433")
        form.addRow("Puerto:", self.mssql_port_input)

        self.mssql_database_input = QLineEdit()
        self.mssql_database_input.setPlaceholderText("clinic_db")
        form.addRow("Base de Datos:", self.mssql_database_input)

        self.mssql_user_input = QLineEdit()
        self.mssql_user_input.setPlaceholderText("sa (si usas SQL Auth)")
        form.addRow("Usuario:", self.mssql_user_input)

        self.mssql_password_input = QLineEdit()
        self.mssql_password_input.setEchoMode(QLineEdit.Password)
        self.mssql_password_input.setPlaceholderText("Contraseña (si aplica)")
        form.addRow("Contraseña:", self.mssql_password_input)

        self.mssql_driver_input = QLineEdit()
        self.mssql_driver_input.setPlaceholderText("ODBC Driver 17 for SQL Server")
        form.addRow("Driver ODBC:", self.mssql_driver_input)

        self.mssql_trusted_checkbox = QCheckBox("Usar Autenticación de Windows (Trusted)")
        form.addRow("", self.mssql_trusted_checkbox)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()

        test_btn = QPushButton("🔌 Probar Conexión")
        test_btn.clicked.connect(self.test_mssql_connection)
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #5E81AC;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
        """)
        btn_layout.addWidget(test_btn)

        save_btn = QPushButton("💾 Guardar Configuración")
        save_btn.clicked.connect(self.save_mssql_config)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #A3BE8C;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #B8D4A8;
            }
        """)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)
        
        # --- Botón de Migración ---
        migrate_btn = QPushButton("🚀 Migrar datos de SQLite a SQL Server")
        migrate_btn.clicked.connect(self.migrate_to_mssql)
        migrate_btn.setStyleSheet("""
            QPushButton {
                background-color: #BF616A;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #D08770;
            }
        """)
        layout.addWidget(migrate_btn)

        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    
    def create_backup_section(self, parent_layout):
        """Create backup section."""
        group = QGroupBox("💾 Respaldos")
        layout = QVBoxLayout()
        
        # Info
        info = QLabel(
            "💡 <b>Recomendación:</b> Crea respaldos regulares de tu base de datos. "
            "Los respaldos se guardan en la carpeta 'backups' del proyecto."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "background-color: #E8F4F8; "
            "border: 1px solid #B8E0F0; "
            "border-radius: 5px; "
            "padding: 10px; "
            "color: #31708F; "
            "font-size: 12px;"
        )
        layout.addWidget(info)
        
        # Backup button
        backup_btn = QPushButton("💾 Crear Respaldo Ahora")
        backup_btn.clicked.connect(self.create_backup)
        backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #5E81AC;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
        """)
        layout.addWidget(backup_btn)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def load_current_config(self):
        """Load and display current database configuration."""
        try:
            config = configparser.ConfigParser()
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.ini')
            
            if os.path.exists(config_path):
                config.read(config_path, encoding='utf-8')
            
            db_type = config.get('database', 'db_type', fallback='sqlite')
            
            if db_type == 'sqlite':
                db_path = self.get_db_path()
                info_text = (
                    f"<b>Tipo:</b> SQLite<br>"
                    f"<b>Ubicación:</b> {db_path}<br>"
                )
                
                if os.path.exists(db_path):
                    size_bytes = os.path.getsize(db_path)
                    size_mb = size_bytes / (1024 * 1024)
                    info_text += f"<b>Tamaño:</b> {size_mb:.2f} MB"
            else:
                # MSSQL
                host = config.get('database', 'mssql_host', fallback='localhost')
                port = config.get('database', 'mssql_port', fallback='1433')
                database = config.get('database', 'mssql_database', fallback='clinic_db')
                user = config.get('database', 'mssql_user', fallback='')
                
                info_text = (
                    f"<b>Tipo:</b> SQL Server (MSSQL)<br>"
                    f"<b>Host:</b> {host}:{port}<br>"
                    f"<b>Base de Datos:</b> {database}<br>"
                    f"<b>Usuario:</b> {user if user else 'Windows Authentication'}"
                )
            
            self.current_db_label.setText(info_text)

            # Load MSSQL config if present
            try:
                mssql_config = self.migrator.load_mssql_config()
                self.mssql_host_input.setText(mssql_config.get('host', ''))
                self.mssql_port_input.setText(mssql_config.get('port', ''))
                self.mssql_database_input.setText(mssql_config.get('database', ''))
                self.mssql_user_input.setText(mssql_config.get('user', ''))
                self.mssql_password_input.setText(mssql_config.get('password', ''))
                self.mssql_driver_input.setText(mssql_config.get('driver', 'ODBC Driver 17 for SQL Server'))
                self.mssql_trusted_checkbox.setChecked(bool(mssql_config.get('trusted', False)))
            except Exception:
                # It's fine if MSSQL config is missing
                pass
            
            # Don't load statistics automatically to avoid connection errors
            # User can click "Actualizar Estadísticas" button to load them
            self.stats_label.setText(
                "Haz clic en '🔄 Actualizar Estadísticas' para ver los datos de la base de datos."
            )
            
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            self.current_db_label.setText(f"Error al cargar configuración: {str(e)}")

    
    def load_statistics(self):
        """Load and display database statistics."""
        try:
            stats = self.migrator.get_database_statistics()
            
            if 'error' in stats:
                self.stats_label.setText(f"⚠️ No se pudieron cargar las estadísticas.\n\nPara SQLite: Verifica que la base de datos exista.\nPara SQL Server: Verifica que el servidor esté corriendo y las credenciales sean correctas.")
                return
            
            stats_text = f"<b>Tipo de Base de Datos:</b> {stats['db_type']}<br><br>"
            stats_text += "<b>Registros por Tabla:</b><br>"
            
            for table, count in stats.get('tables', {}).items():
                stats_text += f"  • {table}: {count}<br>"
            
            if 'size_mb' in stats:
                stats_text += f"<br><b>Tamaño Total:</b> {stats['size_mb']:.2f} MB"
            
            self.stats_label.setText(stats_text)
            
        except Exception as e:
            self.logger.error(f"Error loading statistics: {e}")
            self.stats_label.setText(
                "⚠️ No se pudieron cargar las estadísticas.\n\n"
                "Esto es normal si SQL Server no está configurado o no está corriendo.\n"
                "Las estadísticas se mostrarán cuando la base de datos esté disponible."
            )

    
    def test_mssql_connection(self):
        """Test MSSQL (SQL Server) connection from UI inputs."""
        host = self.mssql_host_input.text() or 'localhost'
        port = self.mssql_port_input.text() or '1433'
        database = self.mssql_database_input.text() or 'clinic_db'
        user = self.mssql_user_input.text() or ''
        password = self.mssql_password_input.text() or ''
        driver = self.mssql_driver_input.text() or 'ODBC Driver 17 for SQL Server'
        trusted = bool(self.mssql_trusted_checkbox.isChecked())

        success, message = self.migrator.test_mssql_connection(
            host, port, database, user, password, driver, trusted
        )

        if success:
            QMessageBox.information(self, "Conexión Exitosa", message)
        else:
            QMessageBox.critical(self, "Error de Conexión", message)
    
    def save_mssql_config(self):
        """Save MSSQL configuration from UI inputs."""
        try:
            host = self.mssql_host_input.text() or 'localhost'
            port = self.mssql_port_input.text() or '1433'
            database = self.mssql_database_input.text() or 'clinic_db'
            user = self.mssql_user_input.text() or ''
            password = self.mssql_password_input.text() or ''
            driver = self.mssql_driver_input.text() or 'ODBC Driver 17 for SQL Server'
            trusted = bool(self.mssql_trusted_checkbox.isChecked())

            self.migrator.save_mssql_config(host, port, database, user, password, driver, trusted)

            QMessageBox.information(
                self,
                "Configuración Guardada",
                "✅ La configuración de SQL Server (MSSQL) ha sido guardada.\n\n"
                "Nota: La aplicación seguirá usando la base de datos actual "
                "hasta que cambies manualmente 'db_type' en config.ini."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la configuración:\n\n{str(e)}")
    
    def migrate_to_mssql(self):
        """Execute migration from SQLite to SQL Server."""
        # 1. Validation
        host = self.mssql_host_input.text() or 'localhost'
        port = self.mssql_port_input.text() or '1433'
        database = self.mssql_database_input.text() or 'clinic_db'
        user = self.mssql_user_input.text() or ''
        password = self.mssql_password_input.text() or ''
        driver = self.mssql_driver_input.text() or 'ODBC Driver 17 for SQL Server'
        trusted = bool(self.mssql_trusted_checkbox.isChecked())

        if not trusted and not user:
             QMessageBox.warning(self, "Faltan Datos", "Si no usas autenticación de Windows, debes especificar un usuario.")
             return

        # 2. Confirmation
        reply = QMessageBox.question(
            self,
            "Confirmar Migración",
            "¿Estás seguro de que deseas migrar los datos de SQLite a SQL Server?\n\n"
            "⚠️ ESTO SOBREESCRIBIRÁ LOS DATOS EN LA BASE DE DATOS DE DESTINO.\n"
            "⚠️ La aplicación se reiniciará después de la migración.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return

        # 3. Connection Test
        success, message = self.migrator.test_mssql_connection(host, port, database, user, password, driver, trusted)
        if not success:
            QMessageBox.critical(self, "Error de Conexión", f"No se puede conectar a SQL Server:\n{message}")
            return

        # 4. Progress Dialog
        from PySide6.QtWidgets import QProgressDialog, QApplication
        
        progress = QProgressDialog("Migrando datos...", "Cancelar", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        QApplication.processEvents() # Force update

        # Callback helper
        def progress_callback(table, current, total):
            if total > 0:
                percent = int((current / total) * 100)
                progress.setLabelText(f"Importando tabla: {table} ({current}/{total})")
                progress.setValue(percent)
                QApplication.processEvents()

        try:
            # 5. Export SQLite Data
            progress.setLabelText("Exportando datos de SQLite...")
            QApplication.processEvents()
            
            data = self.migrator.export_sqlite_data()
            
            if not data:
                progress.close()
                QMessageBox.warning(self, "Sin Operación", "No hay datos para exportar o ocurrió un error al leer SQLite.")
                return

            # 6. Import to SQL Server
            progress.setLabelText("Creando estructura e importando datos...")
            QApplication.processEvents()

            success, msg = self.migrator.import_data_to_mssql(
                data=data,
                host=host, port=port, database=database, user=user, password=password,
                driver=driver, trusted=trusted,
                progress_callback=progress_callback
            )

            progress.close()

            if success:
                # 7. Update Config
                self.save_mssql_config() # Save settings
                
                # Update config.ini to use mssql
                config = configparser.ConfigParser()
                config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.ini')
                config.read(config_path)
                
                if 'database' not in config:
                    config['database'] = {}
                config['database']['db_type'] = 'mssql'
                
                with open(config_path, 'w') as f:
                    config.write(f)

                QMessageBox.information(
                    self,
                    "Migración Exitosa",
                    "✅ La migración se ha completado correctamente.\n\n"
                    "La aplicación se ha configurado para usar SQL Server.\n"
                    "Por favor, reinicia la aplicación para aplicar los cambios."
                )
            else:
                QMessageBox.critical(self, "Error en Migración", f"Ocurrió un error durante la importación:\n\n{msg}")

        except Exception as e:
            progress.close()
            self.logger.error(f"Migration error: {e}", exc_info=True)
            QMessageBox.critical(self, "Error Crítico", f"Ocurrió un error inesperado:\n\n{str(e)}")


    def create_backup(self):
        """Create database backup."""
        db_path = self.get_db_path()
        
        if not os.path.exists(db_path):
            QMessageBox.warning(
                self,
                "Base de Datos No Encontrada",
                "No se encontró el archivo de base de datos SQLite."
            )
            return
        
        try:
            # Create backup directory
            backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'clinic_backup_{timestamp}.db'
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Copy file
            shutil.copy2(db_path, backup_path)
            
            # Get size
            backup_size = os.path.getsize(backup_path)
            backup_size_mb = backup_size / (1024 * 1024)
            
            QMessageBox.information(
                self,
                "Respaldo Creado",
                f"✅ Respaldo creado exitosamente:\n\n"
                f"📁 Ubicación: {backup_path}\n"
                f"💾 Tamaño: {backup_size_mb:.2f} MB\n\n"
                f"Guarda este archivo en un lugar seguro."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error al Crear Respaldo",
                f"No se pudo crear el respaldo:\n\n{str(e)}"
            )
