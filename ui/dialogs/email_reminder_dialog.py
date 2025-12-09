import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QLabel, QPushButton,
    QHBoxLayout, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, QDateTime
from sqlalchemy.orm import joinedload

from database.database_manager import session_scope
from database.models import Appointment, Patient, User
from core.notification_service import NotificationService
from datetime import datetime

class EmailReminderDialog(QDialog):
    def __init__(self, appointment_id: int, parent=None):
        super().__init__(parent)
        self.appointment_id = appointment_id
        self.appointment = None
        # --- CAMBIO: Almacenar solo los datos necesarios, no los objetos completos ---
        self.patient_email = None
        self.patient_full_name = None
        self.notification_service = NotificationService()

        self.setWindowTitle("Enviar Recordatorio de Cita")
        self.setMinimumSize(500, 400)

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.patient_name_label = QLabel("<b>Paciente:</b> ")
        self.appointment_details_label = QLabel("<b>Cita:</b> ")
        self.patient_email_label = QLabel("<b>Email del Paciente:</b> ")

        self.subject_input = QLineEdit()
        self.body_input = QTextEdit()

        form_layout.addRow(self.patient_name_label)
        form_layout.addRow(self.appointment_details_label)
        form_layout.addRow(self.patient_email_label)
        form_layout.addRow("Asunto:", self.subject_input)
        form_layout.addRow("Cuerpo del Mensaje:", self.body_input)

        self.send_button = QPushButton("📧 Enviar Correo")
        self.send_button.clicked.connect(self.send_email)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.send_button)

        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)

    def load_data(self):
        with session_scope() as session:
            # --- CORRECCIÓN: Carga ansiosa (eager loading) de las relaciones ---
            # Usamos joinedload para cargar el paciente y el psicólogo en la misma consulta
            self.appointment = session.query(Appointment).options(
                joinedload(Appointment.patient),
                joinedload(Appointment.psicologo) # CORRECCIÓN: Usar el nombre de la relación 'psicologo'
            ).get(self.appointment_id)

            if not self.appointment:
                QMessageBox.critical(self, "Error", "Cita no encontrada.")
                self.reject()
                return

            # Ahora podemos acceder a las relaciones directamente porque ya están cargadas
            patient = self.appointment.patient
            psychologist = self.appointment.psicologo

            if not patient or not psychologist:
                QMessageBox.critical(self, "Error", "Datos de paciente o psicólogo no encontrados para la cita.")
                self.reject()
                return
            
            # --- CAMBIO: Guardar los datos en variables de instancia ---
            self.patient_full_name = patient.full_name
            self.patient_email = patient.email

            self.patient_name_label.setText(f"<b>Paciente:</b> {self.patient_full_name}")
            self.appointment_details_label.setText( # Corregido para usar el nombre de la relación correcta
                f"<b>Cita:</b> {self.appointment.appointment_time.strftime('%d/%m/%Y %H:%M')} con {psychologist.username}"
            )
            self.patient_email_label.setText(f"<b>Email del Paciente:</b> {self.patient_email or 'No disponible'}")

            # Pre-fill subject and body
            default_subject = f"Recordatorio de su cita - Clínica Mente en Equilibrio"
            default_body = (
                f"Hola {self.patient_full_name},\n\n"
                f"Le recordamos que tiene una cita programada para el "
                f"{self.appointment.appointment_time.strftime('%d de %B de %Y a las %H:%M')}.\n\n"
                f"Si necesita reagendar, por favor contáctenos.\n\n"
                f"Saludos cordiales,\nClínica Mente en Equilibrio"
            )
            self.subject_input.setText(default_subject)
            self.body_input.setPlainText(default_body)

    def send_email(self):
        if not self.notification_service.is_configured():
            QMessageBox.critical(self, "Error de Configuración", "El servicio de correo no está configurado en 'config.ini'.")
            return

        if not self.patient_email or '@' not in self.patient_email:
            QMessageBox.warning(self, "Email Inválido", f"El paciente '{self.patient_full_name}' no tiene un correo electrónico válido registrado.")
            return

        subject = self.subject_input.text().strip()
        body = self.body_input.toPlainText().strip()

        if not subject or not body:
            QMessageBox.warning(self, "Campos Vacíos", "El asunto y el cuerpo del mensaje no pueden estar vacíos.")
            return

        reply = QMessageBox.question(self, "Confirmar Envío",
                                     "¿Está seguro de que desea enviar este correo?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                # El método send_email en NotificationService espera un cuerpo HTML, así que lo envolvemos.
                html_body = f"""
                <html><body>
                <p>{body.replace('\n', '<br>')}</p>
                </body></html>
                """
                success = self.notification_service.send_email(self.patient_email, subject, html_body)
                if success:
                    QMessageBox.information(self, "Éxito", "Correo enviado correctamente.")
                    self.accept()
                else:
                    QMessageBox.critical(self, "Fallo en el Envío", "No se pudo enviar el correo. Revise la configuración o el log.")
            except Exception as e:
                QMessageBox.critical(self, "Error Inesperado", f"Ocurrió un error al intentar enviar el correo:\n{e}")