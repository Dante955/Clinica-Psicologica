from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
                             QListWidget, QListWidgetItem, QSplitter, QCalendarWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView, QFormLayout,
                             QMessageBox, QInputDialog)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QTextCharFormat, QFont, QColor
from sqlalchemy import func, inspect

from database.database_manager import session_scope
from core.authentication import UserRole, AuthService
from core.logic import ClinicLogic # <-- Importamos la nueva clase
from database.models import User, Patient, Appointment
from ui.widgets.appointment_form_dialog import AppointmentFormDialog
from ui.dialogs.patient_form_dialog import PatientFormDialog
from ui.dialogs.email_reminder_dialog import EmailReminderDialog # Nueva importación
from ui.widgets.patient_details_panel import PatientDetailsPanel

class PsychologistPanel(QWidget):
    def __init__(self, current_user: User):
        super().__init__()
        self.current_user = current_user
        self.current_patient_id = None
        self.logic = ClinicLogic() # <-- Creamos una instancia de la lógica
        self.patient_details_window = None

        self.setup_ui()
        self.load_patients()

    def setup_ui(self):
        """Inicializa y organiza la interfaz de usuario."""
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel()

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 600])

        main_layout.addWidget(splitter)

    def _create_left_panel(self) -> QWidget:
        """Crea el panel izquierdo con la lista de pacientes."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        title = QLabel("Pacientes")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        self.patient_list = QListWidget()
        self.patient_list.itemClicked.connect(self.on_patient_selected)
        layout.addWidget(self.patient_list)

        # Layout para los botones de paciente
        button_layout = QHBoxLayout()
        add_patient_button = QPushButton("➕ Añadir Paciente")
        add_patient_button.clicked.connect(self.add_patient)
        
        edit_patient_button = QPushButton("✏️ Editar Paciente")
        edit_patient_button.clicked.connect(self.edit_patient)

        self.delete_patient_button = QPushButton("🗑️ Eliminar Paciente")
        self.delete_patient_button.clicked.connect(self.delete_patient)
        self.delete_patient_button.setEnabled(False)

        self.view_details_button = QPushButton("📄 Ver Detalles")
        self.view_details_button.clicked.connect(self.view_patient_details)
        self.view_details_button.setEnabled(False)

        button_layout.addWidget(add_patient_button)
        button_layout.addWidget(edit_patient_button)
        button_layout.addWidget(self.delete_patient_button)
        button_layout.addWidget(self.view_details_button)

        layout.addLayout(button_layout)

        return panel

    def _create_right_panel(self) -> QWidget:
        """Crea el panel derecho con los detalles y citas del paciente."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        self.patient_details_label = QLabel("Seleccione un paciente de la lista")
        self.patient_details_label.setObjectName("panelTitle")
        self.patient_details_label.setAlignment(Qt.AlignCenter)
        
        self.details_form = self._create_details_form()
        self.details_form.setVisible(False)

        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self.on_date_selected)

        self.appointments_table = self._create_appointments_table()
        
        appointment_button_layout = QHBoxLayout()
        add_appointment_button = QPushButton("🗓️ Agendar Nueva Cita")
        add_appointment_button.clicked.connect(self.add_appointment)
        self.edit_appointment_button = QPushButton("✏️ Editar Cita")
        self.edit_appointment_button.clicked.connect(self.edit_appointment)
        self.edit_appointment_button.setEnabled(False)

        # El botón de enviar recordatorio se mueve aquí
        self.send_reminder_button = QPushButton("📧 Enviar Recordatorio")
        self.send_reminder_button.clicked.connect(self.send_manual_reminder)
        self.send_reminder_button.setEnabled(False)

        self.cancel_appointment_button = QPushButton("❌ Cancelar Cita")
        self.cancel_appointment_button.clicked.connect(self.cancel_appointment)
        self.cancel_appointment_button.setEnabled(False)

        self.no_show_appointment_button = QPushButton("🚫 No Asistió")
        self.no_show_appointment_button.clicked.connect(self.mark_as_no_show)
        self.no_show_appointment_button.setEnabled(False)

        # Añadir botones al layout
        appointment_button_layout.addWidget(add_appointment_button)
        appointment_button_layout.addWidget(self.edit_appointment_button)
        appointment_button_layout.addWidget(self.send_reminder_button)
        appointment_button_layout.addWidget(self.cancel_appointment_button)
        appointment_button_layout.addWidget(self.no_show_appointment_button)


        layout.addWidget(self.patient_details_label)
        layout.addWidget(self.details_form)
        layout.addWidget(self.calendar)
        layout.addWidget(QLabel("<b>Citas del día seleccionado:</b>"))
        layout.addWidget(self.appointments_table)
        layout.addLayout(appointment_button_layout)
        
        return panel

    def _create_details_form(self) -> QWidget:
        """Crea el widget del formulario de detalles del paciente."""
        form_widget = QWidget()
        layout = QFormLayout(form_widget)
        layout.setContentsMargins(0, 10, 0, 10)
        self.patient_name_label = QLabel()
        self.patient_contact_label = QLabel()
        layout.addRow("<b>Nombre:</b>", self.patient_name_label)
        layout.addRow("<b>Contacto:</b>", self.patient_contact_label)
        return form_widget

    def _create_appointments_table(self) -> QTableWidget:
        """Crea y configura la tabla de citas."""
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["ID Cita", "Hora", "Estado"])
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.itemSelectionChanged.connect(self.on_appointment_selected)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        return table

    def load_patients(self):
        """Carga los pacientes asignados al psicólogo actual."""
        self.patient_list.clear()
        with session_scope() as session:
            # Si el usuario es Admin, ve todos los pacientes.
            # Si es Psicólogo, solo ve los suyos.
            if self.current_user.role == UserRole.ADMIN:
                patients = session.query(Patient).order_by(Patient.full_name).all()
            else: # Asumimos que es PSICOLOGO
                patients = session.query(Patient).filter_by(psychologist_id=self.current_user.id).order_by(Patient.full_name).all()

            for patient in patients:
                item = QListWidgetItem(patient.full_name)
                item.setData(Qt.UserRole, patient.id) # Guardamos el ID del paciente en el item
                self.patient_list.addItem(item)

    def on_patient_selected(self, item: QListWidgetItem):
        """Actualiza la UI cuando se selecciona un paciente."""
        self.current_patient_id = item.data(Qt.UserRole)
        self.view_details_button.setEnabled(True)
        self.delete_patient_button.setEnabled(True)
        self.edit_appointment_button.setEnabled(False)
        with session_scope() as session:
            patient = session.get(Patient, self.current_patient_id)
            if patient:
                self.patient_details_label.setText(f"Detalles de {patient.full_name}")
                self.patient_name_label.setText(patient.full_name)
                self.patient_contact_label.setText(patient.contact_info or "No especificado")
                self.details_form.setVisible(True)
                self.load_and_mark_appointments()

    def on_appointment_selected(self):
        """Habilita o deshabilita los botones de acción de citas según la selección."""
        has_selection = bool(self.appointments_table.selectedItems())
        self.edit_appointment_button.setEnabled(has_selection)
        self.delete_patient_button.setEnabled(bool(self.patient_list.currentItem()))
        self.send_reminder_button.setEnabled(has_selection)
        self.cancel_appointment_button.setEnabled(has_selection)
        self.no_show_appointment_button.setEnabled(has_selection)

    def view_patient_details(self):
        """Muestra la ventana con los detalles completos del paciente."""
        if not self.current_patient_id:
            QMessageBox.warning(self, "Paciente no seleccionado", "Por favor, seleccione un paciente.")
            return
        
        # Si ya hay una ventana de detalles abierta, la trae al frente.
        if self.patient_details_window and self.patient_details_window.isVisible():
            self.patient_details_window.activateWindow()
            return

        self.patient_details_window = PatientDetailsPanel(self.current_patient_id)
        self.patient_details_window.show()

    def load_and_mark_appointments(self):
        """Carga las citas del paciente y las resalta en el calendario."""
        if not self.current_patient_id:
            return

        # Resetea el formato de todas las fechas en el calendario
        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())

        # --- MEJORA DE ESTILO ---
        # Usa un color del tema en lugar de uno genérico
        appointment_format = QTextCharFormat()
        appointment_format.setFontWeight(QFont.Bold)
        appointment_format.setBackground(QColor("#EBCB8B")) # Color amarillo/dorado de la paleta Nord

        with session_scope() as session:
            appointments = session.query(Appointment.appointment_time).filter_by(
                patient_id=self.current_patient_id,
                psychologist_id=self.current_user.id
            ).all()

            for appt_time, in appointments:
                qdate = QDate(appt_time.year, appt_time.month, appt_time.day)
                self.calendar.setDateTextFormat(qdate, appointment_format)
        
        self.on_date_selected() # Actualiza la tabla para la fecha actual

    def on_date_selected(self):
        """Muestra en la tabla las citas de la fecha seleccionada."""
        self.appointments_table.setRowCount(0)
        if not self.current_patient_id:
            return

        selected_date = self.calendar.selectedDate().toPython()

        with session_scope() as session:
            # --- CORRECCIÓN CRÍTICA DE LA CONSULTA ---
            # Usamos func.date() de SQLAlchemy para comparar solo la parte de la fecha.
            appointments_on_date = session.query(Appointment).filter(
                Appointment.patient_id == self.current_patient_id,
                Appointment.psychologist_id == self.current_user.id,
                func.date(Appointment.appointment_time) == selected_date
            ).order_by(Appointment.appointment_time).all()

            self.appointments_table.setRowCount(len(appointments_on_date))
            for row, appt in enumerate(appointments_on_date):
                self.appointments_table.setItem(row, 0, QTableWidgetItem(str(appt.id)))
                time_str = appt.appointment_time.strftime('%H:%M')
                self.appointments_table.setItem(row, 1, QTableWidgetItem(time_str))
                status_str = appt.status or "No definido"
                self.appointments_table.setItem(row, 2, QTableWidgetItem(status_str.capitalize()))

                for col in range(3):
                    self.appointments_table.item(row, col).setTextAlignment(Qt.AlignCenter)

    def add_patient(self):
        """Pregunta el tipo de paciente y luego abre el formulario de creación."""
        items = ["Adulto", "Niño"]
        item, ok = QInputDialog.getItem(self, "Tipo de Paciente",
                                        "Seleccione el tipo de paciente a añadir:", items, 0, False)

        if ok and item:
            patient_type = 'niño' if item == "Niño" else 'adulto'
            
            # Si el usuario no es admin, se le asigna el paciente automáticamente.
            psychologist_id_to_assign = None
            if self.current_user.role != UserRole.ADMIN:
                psychologist_id_to_assign = self.current_user.id

            dialog = PatientFormDialog(patient_type=patient_type, psychologist_id=psychologist_id_to_assign, parent=self)
            if dialog.exec():
                self.load_patients()

    def edit_patient(self):
        """Abre un diálogo para editar el paciente seleccionado."""
        selected_item = self.patient_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, selecciona un paciente de la lista para editar.")
            return

        patient_id = selected_item.data(Qt.UserRole)
        dialog = PatientFormDialog(patient_id=patient_id, parent=self)
        
        if dialog.exec():
            # Guardar el ID del paciente seleccionado
            current_id = self.current_patient_id
            # Recargar la lista de pacientes
            self.load_patients()
            # Volver a seleccionar el paciente editado
            for i in range(self.patient_list.count()):
                if self.patient_list.item(i).data(Qt.UserRole) == current_id:
                    self.patient_list.setCurrentRow(i)
                    self.on_patient_selected(self.patient_list.item(i))
                    break
    
    def delete_patient(self):
        """Elimina al paciente seleccionado y todos sus datos asociados."""
        selected_item = self.patient_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, selecciona un paciente de la lista para eliminar.")
            return

        patient_id = selected_item.data(Qt.UserRole)
        patient_name = selected_item.text()

        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                     f"<b>¿Está seguro de que desea eliminar a '{patient_name}'?</b>\n\n"
                                     "Esta acción es irreversible y eliminará al paciente junto con <b>todas sus citas</b> asociadas.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            success, message = self.logic.delete_patient(patient_id)
            if success:
                QMessageBox.information(self, "Éxito", message)
                self.load_patients()
                self.clear_right_panel()
            else:
                QMessageBox.critical(self, "Error", message)

    def clear_right_panel(self):
        self.patient_details_label.setText("Seleccione un paciente de la lista")
        self.details_form.setVisible(False)
        self.appointments_table.setRowCount(0)
        self.current_patient_id = None
        self.on_appointment_selected() # Deshabilita los botones

    def add_appointment(self):
        """Abre el diálogo para añadir una nueva cita."""
        if not self.current_patient_id:
            QMessageBox.warning(self, "Paciente no seleccionado",
                                "Por favor, seleccione un paciente de la lista antes de agendar una cita.")
            return
        
        dialog = AppointmentFormDialog(patient_id=self.current_patient_id, psychologist_id=self.current_user.id, parent=self)
        if dialog.exec():
            self.load_and_mark_appointments()

    def edit_appointment(self):
        """Abre el diálogo para editar la cita seleccionada."""
        selected_items = self.appointments_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, selecciona una cita de la tabla para editar.")
            return

        appointment_id = int(self.appointments_table.item(selected_items[0].row(), 0).text())
        dialog = AppointmentFormDialog(patient_id=self.current_patient_id, psychologist_id=self.current_user.id, appointment_id=appointment_id, parent=self)
        if dialog.exec():
            self.load_and_mark_appointments()

    def cancel_appointment(self):
        """Marca la cita seleccionada como 'Cancelada'."""
        self._update_appointment_status(
            new_status='Cancelada',
            confirm_title="Confirmar Cancelación",
            confirm_text="¿Está seguro de que desea cancelar esta cita?"
        )

    def mark_as_no_show(self):
        """Marca la cita seleccionada como 'No Asistió'."""
        self._update_appointment_status(
            new_status='No Asistió',
            confirm_title="Confirmar Ausencia",
            confirm_text="¿Está seguro de que desea marcar que el paciente no asistió a esta cita?"
        )

    def _update_appointment_status(self, new_status: str, confirm_title: str, confirm_text: str):
        """Método genérico para actualizar el estado de una cita."""
        selected_items = self.appointments_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, selecciona una cita de la tabla.")
            return

        reply = QMessageBox.question(self, confirm_title, confirm_text, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            appointment_id = int(self.appointments_table.item(selected_items[0].row(), 0).text())
            with session_scope() as session:
                appointment = session.get(Appointment, appointment_id)
                if appointment:
                    appointment.status = new_status
            self.on_date_selected() # Recargar la tabla para el día actual

    def send_manual_reminder(self):
        """Abre un diálogo para enviar un recordatorio de cita manualmente."""
        selected_items = self.appointments_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, selecciona una cita para enviar un recordatorio.")
            return

        appointment_id = int(self.appointments_table.item(selected_items[0].row(), 0).text())

        # Abrir el nuevo diálogo de envío de email
        if dialog.exec():
            # Opcional: Recargar la tabla o mostrar un mensaje si es necesario
            pass

    def refresh_data(self):
        """Método público para refrescar los datos del panel."""
        self.load_patients()
        # Opcional: Si quieres que también se limpie la selección al refrescar
        # self.clear_right_panel()