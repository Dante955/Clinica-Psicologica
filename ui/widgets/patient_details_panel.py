# ui/widgets/patient_details_panel.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt
from database.database_manager import session_scope
from database.models import Patient

class PatientDetailsPanel(QWidget):
    def __init__(self, patient_id: int, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.setWindowTitle("Detalles del Paciente")
        self.setMinimumSize(600, 800)

        self.setup_ui()
        self.load_patient_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        container = QWidget()
        scroll_area.setWidget(container)
        
        layout = QVBoxLayout(container)

        # --- Datos Demográficos ---
        demographics_group = QGroupBox("Datos Demográficos")
        demographics_layout = QFormLayout()
        self.full_name_label = QLabel()
        self.contact_info_label = QLabel()
        self.patient_type_label = QLabel()
        self.tutor_name_label = QLabel()
        self.birth_date_label = QLabel()
        self.gender_pronouns_label = QLabel()
        self.address_label = QLabel()
        self.emergency_contact_label = QLabel()
        self.referred_by_label = QLabel()
        
        demographics_layout.addRow("Nombre Completo:", self.full_name_label)
        demographics_layout.addRow("Información de Contacto:", self.contact_info_label)
        demographics_layout.addRow("Tipo de Paciente:", self.patient_type_label)
        demographics_layout.addRow("Nombre del Tutor:", self.tutor_name_label)
        demographics_layout.addRow("Fecha de Nacimiento:", self.birth_date_label)
        demographics_layout.addRow("Pronombres de Género:", self.gender_pronouns_label)
        demographics_layout.addRow("Dirección:", self.address_label)
        demographics_layout.addRow("Contacto de Emergencia:", self.emergency_contact_label)
        demographics_layout.addRow("Referido por:", self.referred_by_label)
        demographics_group.setLayout(demographics_layout)
        layout.addWidget(demographics_group)

        # --- Motivo de Consulta ---
        consultation_group = QGroupBox("Motivo de Consulta")
        consultation_layout = QFormLayout()
        self.main_reason_label = QLabel()
        self.main_reason_label.setWordWrap(True)
        self.current_symptoms_label = QLabel()
        self.current_symptoms_label.setWordWrap(True)
        self.problem_duration_label = QLabel()
        self.therapy_expectations_label = QLabel()
        self.therapy_expectations_label.setWordWrap(True)
        self.previous_attempts_label = QLabel()
        self.previous_attempts_label.setWordWrap(True)

        consultation_layout.addRow("Motivo Principal:", self.main_reason_label)
        consultation_layout.addRow("Síntomas Actuales:", self.current_symptoms_label)
        consultation_layout.addRow("Duración del Problema:", self.problem_duration_label)
        consultation_layout.addRow("Expectativas de la Terapia:", self.therapy_expectations_label)
        consultation_layout.addRow("Intentos Previos de Solución:", self.previous_attempts_label)
        consultation_group.setLayout(consultation_layout)
        layout.addWidget(consultation_group)

        # --- Historia Clínica ---
        history_group = QGroupBox("Historia Clínica")
        history_layout = QFormLayout()
        self.mental_health_history_label = QLabel()
        self.mental_health_history_label.setWordWrap(True)
        self.psychiatric_medication_label = QLabel()
        self.psychiatric_medication_label.setWordWrap(True)
        self.other_medication_label = QLabel()
        self.other_medication_label.setWordWrap(True)
        self.family_history_label = QLabel()
        self.family_history_label.setWordWrap(True)
        self.risk_assessment_label = QLabel()
        self.risk_assessment_label.setWordWrap(True)

        history_layout.addRow("Historia de Salud Mental:", self.mental_health_history_label)
        history_layout.addRow("Medicación Psiquiátrica:", self.psychiatric_medication_label)
        history_layout.addRow("Otra Medicación:", self.other_medication_label)
        history_layout.addRow("Historia Familiar:", self.family_history_label)
        history_layout.addRow("Evaluación de Riesgo:", self.risk_assessment_label)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

    def load_patient_data(self):
        with session_scope() as session:
            patient = session.get(Patient, self.patient_id)
            if not patient:
                self.full_name_label.setText("<Paciente no encontrado>")
                return

            # Demographics
            self.full_name_label.setText(patient.full_name)
            self.contact_info_label.setText(patient.contact_info or "N/A")
            self.patient_type_label.setText(patient.patient_type.capitalize() or "N/A")
            self.tutor_name_label.setText(patient.tutor_name or "N/A")
            self.birth_date_label.setText(patient.birth_date.strftime("%Y-%m-%d") if patient.birth_date else "N/A")
            self.gender_pronouns_label.setText(patient.gender_pronouns or "N/A")
            self.address_label.setText(patient.address or "N/A")
            self.emergency_contact_label.setText(patient.emergency_contact or "N/A")
            self.referred_by_label.setText(patient.referred_by or "N/A")

            # Consultation
            self.main_reason_label.setText(patient.main_reason_for_consultation or "N/A")
            self.current_symptoms_label.setText(patient.current_symptoms or "N/A")
            self.problem_duration_label.setText(patient.problem_duration or "N/A")
            self.therapy_expectations_label.setText(patient.therapy_expectations or "N/A")
            self.previous_attempts_label.setText(patient.previous_solution_attempts or "N/A")

            # History
            self.mental_health_history_label.setText(patient.previous_mental_health_history or "N/A")
            self.psychiatric_medication_label.setText(patient.psychiatric_medication or "N/A")
            self.other_medication_label.setText(patient.other_medication or "N/A")
            self.family_history_label.setText(patient.family_history or "N/A")
            self.risk_assessment_label.setText(patient.risk_assessment or "N/A")
