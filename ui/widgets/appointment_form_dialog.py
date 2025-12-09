from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDateTimeEdit, QTextEdit,
    QPushButton, QHBoxLayout, QMessageBox, QComboBox, QDoubleSpinBox
)
from PySide6.QtCore import QDateTime
from database.database_manager import session_scope
from database.models import Appointment
from core.logic import ClinicLogic
from datetime import datetime

class AppointmentFormDialog(QDialog):
    def __init__(self, patient_id, psychologist_id, appointment_id=None, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.psychologist_id = psychologist_id
        self.appointment_id = appointment_id
        self.is_edit_mode = self.appointment_id is not None
        self.logic = ClinicLogic()

        self.setWindowTitle("Editar Cita" if self.is_edit_mode else "Añadir Cita")
        self.setMinimumWidth(450)

        self.setup_ui()

        if self.is_edit_mode:
            self.load_appointment_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm")

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Programada", "Completada", "Cancelada"])

        self.price_spinbox = QDoubleSpinBox()
        self.price_spinbox.setRange(0, 9999.99)
        self.price_spinbox.setPrefix("C$ ")

        self.payment_status_combo = QComboBox()
        self.payment_status_combo.addItems(["Pendiente", "Pagada"])

        self.notes_edit = QTextEdit()

        form_layout.addRow("Fecha y Hora:", self.datetime_edit)
        form_layout.addRow("Estado de la Cita:", self.status_combo)
        form_layout.addRow("Precio:", self.price_spinbox)
        form_layout.addRow("Estado del Pago:", self.payment_status_combo)
        form_layout.addRow("Notas:", self.notes_edit)

        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_appointment)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)

        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)

    def load_appointment_data(self):
        with session_scope() as session:
            appt = session.get(Appointment, self.appointment_id)
            if appt:
                self.datetime_edit.setDateTime(appt.appointment_time)
                self.status_combo.setCurrentText(appt.status or "Programada")
                self.price_spinbox.setValue(appt.price or 0.0)
                self.payment_status_combo.setCurrentText(appt.payment_status or "Pendiente")
                self.notes_edit.setText(appt.notes or "")

    def save_appointment(self):
        appointment_time = self.datetime_edit.dateTime().toPython()
        status = self.status_combo.currentText().lower()
        price = self.price_spinbox.value()
        payment_status = self.payment_status_combo.currentText().lower()
        notes = self.notes_edit.toPlainText()

        appointment_data = {
            "appointment_time": appointment_time,
            "status": status,
            "price": price,
            "payment_status": payment_status,
            "notes": notes
        }

        success, message = self.logic.save_appointment(
            patient_id=self.patient_id,
            psychologist_id=self.psychologist_id,
            appointment_data=appointment_data,
            appointment_id=self.appointment_id
        )
        if success:
            QMessageBox.information(self, "Éxito", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", message)
            self.reject()