"""
Panel de Importación Masiva de Datos

Permite a usuarios con rol SOPORTE importar pacientes y citas
desde archivos Excel (.xlsx) o CSV (.csv).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QMessageBox, QFileDialog, QTextEdit, QComboBox,
    QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal
import pandas as pd
from datetime import datetime
import os

from database.database_manager import session_scope
from database.models import Patient, Appointment, User, UserRole


class ImportWorker(QThread):
    """Worker thread para importar datos sin bloquear la UI."""
    progress = Signal(int, int)  # current, total
    finished = Signal(bool, str, dict)  # success, message, stats
    
    def __init__(self, file_path, import_type, psychologist_id=None):
        super().__init__()
        self.file_path = file_path
        self.import_type = import_type
        self.psychologist_id = psychologist_id
    
    def run(self):
        """Ejecuta la importación en segundo plano."""
        try:
            # Leer archivo
            if self.file_path.endswith('.csv'):
                df = pd.read_csv(self.file_path)
            else:
                df = pd.read_excel(self.file_path)
            
            total = len(df)
            stats = {'success': 0, 'errors': 0, 'skipped': 0}
            
            if self.import_type == 'patients':
                stats = self._import_patients(df, total)
            elif self.import_type == 'appointments':
                stats = self._import_appointments(df, total)
            
            message = (
                f"Importación completada:\n"
                f"✅ Exitosos: {stats['success']}\n"
                f"⚠️ Omitidos: {stats['skipped']}\n"
                f"❌ Errores: {stats['errors']}"
            )
            
            self.finished.emit(True, message, stats)
            
        except Exception as e:
            self.finished.emit(False, f"Error durante la importación:\n{str(e)}", {})
    
    def _import_patients(self, df, total):
        """Importa pacientes desde el DataFrame."""
        stats = {'success': 0, 'errors': 0, 'skipped': 0}
        
        with session_scope() as session:
            for idx, row in df.iterrows():
                self.progress.emit(idx + 1, total)
                
                try:
                    # Validar campos requeridos
                    if pd.isna(row.get('nombre')) or pd.isna(row.get('email')):
                        stats['skipped'] += 1
                        continue
                    
                    # Verificar si el paciente ya existe
                    existing = session.query(Patient).filter_by(
                        email=str(row['email']).strip()
                    ).first()
                    
                    if existing:
                        stats['skipped'] += 1
                        continue
                    
                    # Crear nuevo paciente
                    patient = Patient(
                        full_name=str(row['nombre']).strip(),
                        email=str(row['email']).strip(),
                        contact_info=str(row.get('telefono', '')).strip() if not pd.isna(row.get('telefono')) else '',
                        patient_type=str(row.get('tipo', 'adulto')).strip().lower(),
                        psychologist_id=self.psychologist_id,
                        address=str(row.get('direccion', '')).strip() if not pd.isna(row.get('direccion')) else None,
                        emergency_contact=str(row.get('contacto_emergencia', '')).strip() if not pd.isna(row.get('contacto_emergencia')) else None
                    )
                    
                    # Fecha de nacimiento (opcional)
                    if not pd.isna(row.get('fecha_nacimiento')):
                        try:
                            patient.birth_date = pd.to_datetime(row['fecha_nacimiento'])
                        except:
                            pass
                    
                    session.add(patient)
                    stats['success'] += 1
                    
                except Exception as e:
                    stats['errors'] += 1
                    continue
        
        return stats
    
    def _import_appointments(self, df, total):
        """Importa citas desde el DataFrame."""
        stats = {'success': 0, 'errors': 0, 'skipped': 0}
        
        with session_scope() as session:
            for idx, row in df.iterrows():
                self.progress.emit(idx + 1, total)
                
                try:
                    # Validar campos requeridos
                    if pd.isna(row.get('email_paciente')) or pd.isna(row.get('fecha_hora')):
                        stats['skipped'] += 1
                        continue
                    
                    # Buscar paciente por email
                    patient = session.query(Patient).filter_by(
                        email=str(row['email_paciente']).strip()
                    ).first()
                    
                    if not patient:
                        stats['skipped'] += 1
                        continue
                    
                    # Parsear fecha y hora
                    try:
                        appointment_time = pd.to_datetime(row['fecha_hora'])
                    except:
                        stats['errors'] += 1
                        continue
                    
                    # Crear cita
                    appointment = Appointment(
                        patient_id=patient.id,
                        psychologist_id=patient.psychologist_id or self.psychologist_id,
                        appointment_time=appointment_time,
                        status=str(row.get('estado', 'programada')).strip().lower(),
                        price=float(row.get('precio', 0)) if not pd.isna(row.get('precio')) else None,
                        payment_status=str(row.get('estado_pago', 'pendiente')).strip().lower(),
                        notes=str(row.get('notas', '')).strip() if not pd.isna(row.get('notas')) else None
                    )
                    
                    session.add(appointment)
                    stats['success'] += 1
                    
                except Exception as e:
                    stats['errors'] += 1
                    continue
        
        return stats


class BulkImportPanel(QWidget):
    """Panel para importación masiva de datos."""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("📥 Importación Masiva de Datos")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #5E81AC;")
        layout.addWidget(title)
        
        # Descripción
        description = QLabel(
            "Importa múltiples pacientes o citas desde archivos Excel (.xlsx) o CSV (.csv). "
            "Descarga las plantillas para asegurar el formato correcto."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(description)
        
        # Grupo de plantillas
        templates_group = QGroupBox("📋 Plantillas")
        templates_layout = QVBoxLayout()
        
        templates_info = QLabel(
            "Descarga las plantillas con el formato correcto para importar datos:"
        )
        templates_info.setWordWrap(True)
        templates_layout.addWidget(templates_info)
        
        # Botones de plantillas
        template_buttons_layout = QHBoxLayout()
        
        patient_template_btn = QPushButton("📄 Descargar Plantilla de Pacientes")
        patient_template_btn.clicked.connect(lambda: self.download_template('patients'))
        patient_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5A6268;
            }
        """)
        template_buttons_layout.addWidget(patient_template_btn)
        
        appointment_template_btn = QPushButton("📄 Descargar Plantilla de Citas")
        appointment_template_btn.clicked.connect(lambda: self.download_template('appointments'))
        appointment_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5A6268;
            }
        """)
        template_buttons_layout.addWidget(appointment_template_btn)
        
        templates_layout.addLayout(template_buttons_layout)
        templates_group.setLayout(templates_layout)
        layout.addWidget(templates_group)
        
        # Grupo de importación
        import_group = QGroupBox("📤 Importar Datos")
        import_layout = QVBoxLayout()
        
        # Selector de tipo
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Tipo de datos:"))
        self.import_type_combo = QComboBox()
        self.import_type_combo.addItem("Pacientes", "patients")
        self.import_type_combo.addItem("Citas", "appointments")
        type_layout.addWidget(self.import_type_combo)
        type_layout.addStretch()
        import_layout.addLayout(type_layout)
        
        # Botón seleccionar archivo
        self.select_file_btn = QPushButton("📁 Seleccionar Archivo")
        self.select_file_btn.clicked.connect(self.select_file)
        self.select_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #5E81AC;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
        """)
        import_layout.addWidget(self.select_file_btn)
        
        # Label de archivo seleccionado
        self.file_label = QLabel("Ningún archivo seleccionado")
        self.file_label.setStyleSheet("color: #666; font-style: italic;")
        import_layout.addWidget(self.file_label)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        import_layout.addWidget(self.progress_bar)
        
        # Botón importar
        self.import_btn = QPushButton("▶️ Iniciar Importación")
        self.import_btn.clicked.connect(self.start_import)
        self.import_btn.setEnabled(False)
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        import_layout.addWidget(self.import_btn)
        
        import_group.setLayout(import_layout)
        layout.addWidget(import_group)
        
        # Log de resultados
        log_group = QGroupBox("📊 Registro de Importación")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setPlaceholderText("Los resultados de la importación aparecerán aquí...")
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Espaciador
        layout.addStretch()
        
        self.selected_file = None
    
    def download_template(self, template_type):
        """Descarga una plantilla de ejemplo."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Plantilla",
            f"plantilla_{template_type}.xlsx",
            "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return
        
        try:
            if template_type == 'patients':
                df = pd.DataFrame({
                    'nombre': ['Juan Pérez', 'María García'],
                    'email': ['juan@example.com', 'maria@example.com'],
                    'telefono': ['555-1234', '555-5678'],
                    'tipo': ['adulto', 'adulto'],
                    'fecha_nacimiento': ['1990-01-15', '1985-06-20'],
                    'direccion': ['Calle Principal 123', 'Avenida Central 456'],
                    'contacto_emergencia': ['Ana Pérez - 555-9999', 'Carlos García - 555-8888']
                })
            else:  # appointments
                df = pd.DataFrame({
                    'email_paciente': ['juan@example.com', 'maria@example.com'],
                    'fecha_hora': ['2024-01-15 10:00', '2024-01-15 11:00'],
                    'estado': ['programada', 'programada'],
                    'precio': [500, 500],
                    'estado_pago': ['pendiente', 'pagado'],
                    'notas': ['Primera consulta', 'Seguimiento']
                })
            
            df.to_excel(file_path, index=False)
            
            QMessageBox.information(
                self,
                "Plantilla Descargada",
                f"✅ Plantilla guardada en:\n{file_path}\n\n"
                f"Edita este archivo con tus datos y luego impórtalo."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo crear la plantilla:\n{str(e)}"
            )
    
    def select_file(self):
        """Selecciona un archivo para importar."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo",
            "",
            "Excel/CSV Files (*.xlsx *.xls *.csv)"
        )
        
        if file_path:
            self.selected_file = file_path
            self.file_label.setText(f"📄 {os.path.basename(file_path)}")
            self.file_label.setStyleSheet("color: #28A745; font-weight: bold;")
            self.import_btn.setEnabled(True)
            self.log_text.append(f"Archivo seleccionado: {os.path.basename(file_path)}")
    
    def start_import(self):
        """Inicia el proceso de importación."""
        if not self.selected_file:
            return
        
        import_type = self.import_type_combo.currentData()
        
        # Confirmar
        reply = QMessageBox.question(
            self,
            "Confirmar Importación",
            f"¿Estás seguro de importar datos desde:\n{os.path.basename(self.selected_file)}?\n\n"
            f"Tipo: {self.import_type_combo.currentText()}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Deshabilitar botones
        self.select_file_btn.setEnabled(False)
        self.import_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.log_text.append(f"\n{'='*50}")
        self.log_text.append(f"Iniciando importación de {self.import_type_combo.currentText()}...")
        self.log_text.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Crear y ejecutar worker
        self.worker = ImportWorker(self.selected_file, import_type)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.import_finished)
        self.worker.start()
    
    def update_progress(self, current, total):
        """Actualiza la barra de progreso."""
        progress = int((current / total) * 100)
        self.progress_bar.setValue(progress)
    
    def import_finished(self, success, message, stats):
        """Maneja la finalización de la importación."""
        self.progress_bar.setVisible(False)
        self.select_file_btn.setEnabled(True)
        self.import_btn.setEnabled(True)
        
        self.log_text.append(f"\n{message}")
        self.log_text.append(f"{'='*50}\n")
        
        if success:
            QMessageBox.information(self, "Importación Completada", message)
        else:
            QMessageBox.critical(self, "Error de Importación", message)
        
        # Limpiar selección
        self.selected_file = None
        self.file_label.setText("Ningún archivo seleccionado")
        self.file_label.setStyleSheet("color: #666; font-style: italic;")
        self.import_btn.setEnabled(False)
