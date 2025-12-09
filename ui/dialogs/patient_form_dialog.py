from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QLabel, QPushButton,
    QHBoxLayout, QMessageBox, QDateEdit, QComboBox, QTextEdit,
    QCheckBox, QGroupBox, QScrollArea, QWidget
)
from PySide6.QtCore import QDate
from database.database_manager import session_scope
from database.models import Patient
import json

class PatientFormDialog(QDialog):
    def __init__(self, patient_id=None, patient_type='adulto', psychologist_id=None, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        # Si estamos editando, el tipo de paciente se cargará desde la BD
        self.patient_type = patient_type if patient_id is None else None
        self.psychologist_id = psychologist_id
        self.is_edit_mode = self.patient_id is not None

        # Primero cargamos los datos si es necesario, para determinar el tipo
        if self.is_edit_mode:
            self.load_patient_data_for_setup()

        # Ahora que self.patient_type está definido, configuramos el UI
        self.setup_ui()

        # Finalmente, poblamos el formulario con los datos
        if self.is_edit_mode:
            self.populate_form_data()

        self.setMinimumWidth(600)

    def load_patient_data_for_setup(self):
        """Carga solo los datos básicos necesarios para construir el UI correcto."""
        with session_scope() as session:
            patient = session.query(Patient).get(self.patient_id)
            if not patient:
                QMessageBox.critical(self, "Error", "No se encontró el paciente.")
                self.reject()
                return
            self.patient = patient
            self.patient_type = patient.patient_type

    def setup_ui(self):
        """Configura la interfaz de usuario principal."""
        main_layout = QVBoxLayout(self)

        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_patient)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        if self.is_edit_mode:
            self.setWindowTitle(f"Editar Paciente ({self.patient_type.capitalize()})")
        else:
            self.setWindowTitle(f"Añadir Paciente ({self.patient_type.capitalize()})")

        # Seleccionar el formulario correcto basado en el tipo de paciente
        if self.patient_type == 'adulto':
            self.setup_adult_form(main_layout)
        else:  # 'niño'
            self.setup_child_form(main_layout)

        main_layout.addLayout(button_layout)

    def setup_child_form(self, main_layout):
        """Configura el formulario simple para pacientes niños."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)

        # --- Parte I: Datos de Identificación (El Paciente) ---
        group1 = QGroupBox("Parte I: Datos de Identificación del Paciente")
        layout1 = QVBoxLayout(group1)
        
        # Datos del niño/a
        child_data_group = QGroupBox("Datos del Niño/a")
        child_data_layout = QFormLayout(child_data_group)
        self.full_name_input = QLineEdit()
        self.birth_date_input = QDateEdit(calendarPopup=True)
        self.birth_date_input.setDate(QDate.currentDate().addYears(-10))
        self.birth_place_input = QLineEdit()
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Ej: 7 años y 2 meses")
        self.school_grade_input = QLineEdit()
        self.school_name_input = QLineEdit()
        self.referred_by_input = QLineEdit()
        child_data_layout.addRow("Nombre completo:", self.full_name_input)
        child_data_layout.addRow("Fecha y lugar de nacimiento:", self.birth_date_input)
        child_data_layout.addRow("Lugar de nacimiento:", self.birth_place_input)
        child_data_layout.addRow("Edad (años y meses):", self.age_input)
        child_data_layout.addRow("Grado escolar e institución:", self.school_grade_input)
        child_data_layout.addRow("Nombre de la institución:", self.school_name_input)
        child_data_layout.addRow("Quién remite:", self.referred_by_input)
        layout1.addWidget(child_data_group)

        # Datos de los Progenitores
        tutor_data_group = QGroupBox("Datos de los Progenitores o Cuidadores")
        tutor_data_layout = QFormLayout(tutor_data_group)
        self.tutor_name_input = QLineEdit()
        self.tutor_age_input = QLineEdit()
        self.tutor_occupation_input = QLineEdit()
        self.tutor_education_input = QLineEdit()
        self.parents_marital_status_input = QComboBox()
        self.parents_marital_status_input.addItems(["", "Casados", "Divorciados", "Separados", "Unión Libre", "Viudo/a", "Otro"])
        self.contact_info_input = QLineEdit()
        self.tutor_email_input = QLineEdit() # Nuevo campo para email
        tutor_data_layout.addRow("Nombres, edad, ocupación, escolaridad:", self.tutor_name_input)
        tutor_data_layout.addRow("Edad del cuidador:", self.tutor_age_input)
        tutor_data_layout.addRow("Ocupación:", self.tutor_occupation_input)
        tutor_data_layout.addRow("Nivel de escolaridad:", self.tutor_education_input)
        tutor_data_layout.addRow("Estado civil:", self.parents_marital_status_input)
        tutor_data_layout.addRow("Email del cuidador:", self.tutor_email_input)
        tutor_data_layout.addRow("Información de contacto (dirección, teléfono):", self.contact_info_input)
        layout1.addWidget(tutor_data_group)

        # Composición Familiar
        family_data_group = QGroupBox("Composición Familiar (Genograma)")
        family_data_layout = QFormLayout(family_data_group)
        self.family_composition_input = QTextEdit()
        self.family_composition_input.setPlaceholderText("Nombres y edades de hermanos y otras personas que vivan en el hogar. Describa la dinámica familiar.")
        family_data_layout.addRow("Miembros y dinámica:", self.family_composition_input)
        layout1.addWidget(family_data_group)
        form_layout.addWidget(group1)

        # --- Parte II: Motivo de Consulta ---
        group2 = QGroupBox("Parte II: Motivo de Consulta y Problema Actual")
        layout2 = QFormLayout(group2)
        self.main_reason_input = QTextEdit()
        self.problem_history_input = QTextEdit()
        self.problem_history_input.setPlaceholderText("Fecha de inicio, factores desencadenantes, intentos previos de solución.")
        layout2.addRow("Motivo de Consulta (Textual):", self.main_reason_input)
        layout2.addRow("Historia del Problema Actual:", self.problem_history_input)
        form_layout.addWidget(group2)

        # --- Parte III: Antecedentes Personales ---
        group3 = QGroupBox("Parte III: Antecedentes Personales (Psicoanálisis Personal)")
        layout3 = QFormLayout(group3)
        self.personal_history_input = QTextEdit()
        self.personal_history_input.setPlaceholderText("Periodo prenatal, parto, desarrollo psicomotor y del lenguaje, control de esfínteres, hábitos (sueño, alimentación), juegos y relaciones sociales.")
        layout3.addRow("Historia del desarrollo:", self.personal_history_input)
        form_layout.addWidget(group3)

        # --- Parte IV, V, VI, VII ---
        group4 = QGroupBox("Partes IV, V, VI y VII: Antecedentes, Observación y Plan")
        layout4 = QFormLayout(group4)
        self.school_history_input = QTextEdit()
        self.health_history_input = QTextEdit()
        self.interview_observation_input = QTextEdit()
        self.diagnostic_plan_input = QTextEdit()
        layout4.addRow("Antecedentes Escolares:", self.school_history_input)
        layout4.addRow("Antecedentes de Salud (Médicos y Familiares):", self.health_history_input)
        layout4.addRow("Observación de la Conducta en Entrevista:", self.interview_observation_input)
        layout4.addRow("Impresión Diagnóstica y Plan de Tratamiento:", self.diagnostic_plan_input)
        form_layout.addWidget(group4)

        # --- Consentimiento ---
        group5 = QGroupBox("Consentimiento del Tutor Legal")
        layout5 = QVBoxLayout(group5)
        self.treatment_consent_check = QCheckBox("Doy mi consentimiento para el tratamiento psicológico del menor y acepto las políticas de la clínica.")
        layout5.addWidget(self.treatment_consent_check)
        form_layout.addWidget(group5)

        scroll_area.setWidget(form_widget)
        main_layout.addWidget(scroll_area)

    def setup_adult_form(self, main_layout):
        """Configura el formulario detallado para pacientes adultos."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)

        # --- Módulo 1: Datos Administrativos y Demográficos ---
        group1 = QGroupBox("Módulo 1: Datos Administrativos y Demográficos")
        layout1 = QFormLayout(group1)
        self.full_name_input = QLineEdit()
        self.birth_date_input = QDateEdit(calendarPopup=True)
        self.birth_date_input.setDate(QDate.currentDate().addYears(-30))
        
        # MEJORA: QComboBox para Género
        self.gender_input = QComboBox()
        self.gender_input.addItems(["", "Hombre", "Mujer"])

        self.address_input = QLineEdit()
        self.contact_info_input = QLineEdit()
        self.email_input = QLineEdit() # Nuevo campo para email
        self.emergency_contact_input = QLineEdit()
        self.referred_by_input = QLineEdit()
        layout1.addRow("Nombre Completo:", self.full_name_input)
        layout1.addRow("Fecha de Nacimiento:", self.birth_date_input)
        layout1.addRow("Género:", self.gender_input)
        layout1.addRow("Dirección:", self.address_input)
        layout1.addRow("Teléfono:", self.contact_info_input)
        layout1.addRow("Email:", self.email_input)
        layout1.addRow("Contacto de Emergencia (Nombre y Teléfono):", self.emergency_contact_input)
        layout1.addRow("Referido Por:", self.referred_by_input)
        form_layout.addWidget(group1)

        # --- Módulo 2: Motivo de Consulta y Expectativas ---
        group2 = QGroupBox("Módulo 2: Motivo de Consulta y Expectativas")
        layout2 = QFormLayout(group2)
        self.main_reason_input = QTextEdit()
        self.symptoms_layout = QVBoxLayout()
        self.symptom_checkboxes = {
            "ansiedad": QCheckBox("Ansiedad"), "tristeza": QCheckBox("Tristeza"),
            "problemas_sueno": QCheckBox("Problemas de sueño"), "ataques_panico": QCheckBox("Ataques de pánico"),
            "estres": QCheckBox("Estrés"), "problemas_pareja": QCheckBox("Problemas de pareja")
        }
        for cb in self.symptom_checkboxes.values(): self.symptoms_layout.addWidget(cb)
        self.problem_duration_input = QComboBox()
        self.problem_duration_input.addItems(["", "Unos días", "Unas semanas", "Unos meses", "Más de un año"])
        self.therapy_expectations_input = QTextEdit()
        self.previous_attempts_input = QTextEdit()
        layout2.addRow("Motivo Principal de Consulta:", self.main_reason_input)
        layout2.addRow("Síntomas Actuales:", self.symptoms_layout)
        layout2.addRow("Duración del Problema:", self.problem_duration_input)
        layout2.addRow("Expectativas de la Terapia:", self.therapy_expectations_input)
        layout2.addRow("Intentos de Solución Anteriores:", self.previous_attempts_input)
        form_layout.addWidget(group2)

        # --- Módulo 3: Historia Clínica y de Salud Mental ---
        group3 = QGroupBox("Módulo 3: Historia Clínica y de Salud Mental")
        layout3 = QFormLayout(group3)
        self.prev_history_input = QTextEdit()
        self.psych_meds_input = QTextEdit()
        self.other_meds_input = QTextEdit()
        self.family_history_input = QTextEdit()
        self.risk_assessment_input = QTextEdit()
        layout3.addRow("¿Terapia o psiquiatría previa? (Cuándo, con quién, por qué):", self.prev_history_input)
        layout3.addRow("¿Medicamentos psiquiátricos actuales? (Nombre, dosis):", self.psych_meds_input)
        layout3.addRow("¿Otros medicamentos relevantes?:", self.other_meds_input)
        layout3.addRow("Antecedentes familiares de salud mental:", self.family_history_input)
        layout3.addRow("Notas sobre riesgo (ideación, adicciones, etc.):", self.risk_assessment_input)
        form_layout.addWidget(group3)

        # --- Módulo 5: Consentimiento ---
        group5 = QGroupBox("Módulo 5: Consentimiento Informado")
        layout5 = QVBoxLayout(group5)
        self.privacy_consent_check = QCheckBox("He leído y acepto la política de privacidad y confidencialidad.")
        self.treatment_consent_check = QCheckBox("Doy mi consentimiento para iniciar el tratamiento terapéutico.")
        layout5.addWidget(self.privacy_consent_check)
        layout5.addWidget(self.treatment_consent_check)
        form_layout.addWidget(group5)

        scroll_area.setWidget(form_widget)
        main_layout.addWidget(scroll_area)
        
        # Placeholder para compatibilidad con el formulario de niño
        self.tutor_name_input = QLineEdit()
        self.tutor_email_input = QLineEdit()

    def populate_form_data(self):
        """Rellena el formulario con los datos del paciente cargado."""
        if not hasattr(self, 'patient'): return

        self.full_name_input.setText(self.patient.full_name)
        self.email_input.setText(self.patient.email or "")
        self.contact_info_input.setText(self.patient.contact_info or "")

        if self.patient_type == 'niño':
            self.tutor_name_input.setText(self.patient.tutor_name or "")
            self.contact_info_input.setText(self.patient.contact_info or "")
            if self.patient.additional_data:
                try:
                    data = json.loads(self.patient.additional_data)
                    # Parte I
                    self.birth_date_input.setDate(QDate.fromString(data.get("birth_date", ""), "yyyy-MM-dd"))
                    self.birth_place_input.setText(data.get("birth_place", ""))
                    self.age_input.setText(data.get("age", ""))
                    self.school_grade_input.setText(data.get("school_grade", ""))
                    self.school_name_input.setText(data.get("school_name", ""))
                    self.referred_by_input.setText(data.get("referred_by", ""))
                    self.tutor_age_input.setText(data.get("tutor_age", ""))
                    self.tutor_occupation_input.setText(data.get("tutor_occupation", ""))
                    self.tutor_education_input.setText(data.get("tutor_education", ""))
                    self.parents_marital_status_input.setCurrentText(data.get("parents_marital_status", ""))
                    self.tutor_email_input.setText(self.patient.email or "") # Poblar email del tutor
                    self.family_composition_input.setPlainText(data.get("family_composition", ""))
                    # Parte II
                    self.main_reason_input.setPlainText(data.get("main_reason", ""))
                    self.problem_history_input.setPlainText(data.get("problem_history", ""))
                    # Parte III, IV, V, VI, VII
                    self.personal_history_input.setPlainText(data.get("personal_history", ""))
                    self.school_history_input.setPlainText(data.get("school_history", ""))
                    self.health_history_input.setPlainText(data.get("health_history", ""))
                    self.interview_observation_input.setPlainText(data.get("interview_observation", ""))
                    self.diagnostic_plan_input.setPlainText(data.get("diagnostic_plan", ""))
                    self.treatment_consent_check.setChecked(data.get("consent_given", False))

                except (json.JSONDecodeError, TypeError):
                    QMessageBox.warning(self, "Advertencia", "No se pudieron cargar los datos adicionales del niño. Podrían estar corruptos.")

        else: # Adulto
            # Deserializar JSON y poblar el formulario
            if self.patient.additional_data:
                try:
                    data = json.loads(self.patient.additional_data)
                    self.birth_date_input.setDate(QDate.fromString(data.get("birth_date", ""), "yyyy-MM-dd"))
                    self.gender_input.setCurrentText(data.get("gender", ""))
                    self.address_input.setText(data.get("address", ""))
                    self.emergency_contact_input.setText(data.get("emergency_contact", ""))
                    self.referred_by_input.setText(data.get("referred_by", ""))
                    self.main_reason_input.setPlainText(data.get("main_reason", ""))
                    
                    checked_symptoms = data.get("symptoms", [])
                    for key, checkbox in self.symptom_checkboxes.items():
                        checkbox.setChecked(key in checked_symptoms)
                    
                    self.problem_duration_input.setCurrentText(data.get("problem_duration", ""))
                    self.therapy_expectations_input.setPlainText(data.get("therapy_expectations", ""))
                    self.previous_attempts_input.setPlainText(data.get("previous_attempts", ""))
                    self.prev_history_input.setPlainText(data.get("prev_history", ""))
                    self.psych_meds_input.setPlainText(data.get("psych_meds", ""))
                    self.other_meds_input.setPlainText(data.get("other_meds", ""))
                    self.family_history_input.setPlainText(data.get("family_history", ""))
                    self.risk_assessment_input.setPlainText(data.get("risk_assessment", ""))
                    
                    consent = data.get("consent", {})
                    self.privacy_consent_check.setChecked(consent.get("privacy", False))
                    self.treatment_consent_check.setChecked(consent.get("treatment", False))

                except (json.JSONDecodeError, TypeError):
                    QMessageBox.warning(self, "Advertencia", "No se pudieron cargar los datos adicionales. Podrían estar corruptos.")
                    
    def collect_child_data(self):
        """Recopila todos los datos del formulario de niño en un diccionario."""
        data = {
            "birth_date": self.birth_date_input.date().toString("yyyy-MM-dd"),
            "birth_place": self.birth_place_input.text(),
            "age": self.age_input.text(),
            "school_grade": self.school_grade_input.text(),
            "school_name": self.school_name_input.text(),
            "referred_by": self.referred_by_input.text(),
            "tutor_age": self.tutor_age_input.text(),
            "tutor_occupation": self.tutor_occupation_input.text(),
            "tutor_education": self.tutor_education_input.text(),
            "parents_marital_status": self.parents_marital_status_input.currentText(),
            "family_composition": self.family_composition_input.toPlainText(),
            "main_reason": self.main_reason_input.toPlainText(),
            "problem_history": self.problem_history_input.toPlainText(),
            "personal_history": self.personal_history_input.toPlainText(),
            "school_history": self.school_history_input.toPlainText(),
            "health_history": self.health_history_input.toPlainText(),
            "interview_observation": self.interview_observation_input.toPlainText(),
            "diagnostic_plan": self.diagnostic_plan_input.toPlainText(),
            "consent_given": self.treatment_consent_check.isChecked()
        }
        return data

    def collect_adult_data(self):
        """Recopila todos los datos del formulario de adulto en un diccionario."""
        checked_symptoms = [key for key, checkbox in self.symptom_checkboxes.items() if checkbox.isChecked()]
        
        data = {
            "birth_date": self.birth_date_input.date().toString("yyyy-MM-dd"),
            "gender": self.gender_input.currentText(),
            "address": self.address_input.text(),
            "emergency_contact": self.emergency_contact_input.text(),
            "referred_by": self.referred_by_input.text(),
            "main_reason": self.main_reason_input.toPlainText(),
            "symptoms": checked_symptoms,
            "problem_duration": self.problem_duration_input.currentText(),
            "therapy_expectations": self.therapy_expectations_input.toPlainText(),
            "previous_attempts": self.previous_attempts_input.toPlainText(),
            "prev_history": self.prev_history_input.toPlainText(),
            "psych_meds": self.psych_meds_input.toPlainText(),
            "other_meds": self.other_meds_input.toPlainText(),
            "family_history": self.family_history_input.toPlainText(),
            "risk_assessment": self.risk_assessment_input.toPlainText(),
            "consent": {
                "privacy": self.privacy_consent_check.isChecked(),
                "treatment": self.treatment_consent_check.isChecked()
            }
        }
        return data

    def save_patient(self):
        full_name = self.full_name_input.text().strip()
        if not full_name:
            QMessageBox.warning(self, "Campo Requerido", "El nombre del paciente es obligatorio.")
            return

        tutor_name = None
        additional_data_json = None
        
        # --- VALIDACIÓN DE EMAIL OBLIGATORIO ---
        email = self.email_input.text().strip() if self.patient_type == 'adulto' else self.tutor_email_input.text().strip()
        if not email or '@' not in email:
            QMessageBox.warning(self, "Email Inválido", "El campo de email es obligatorio y debe ser una dirección válida.")
            return

        # El campo contact_info ahora es solo para el teléfono
        contact_info = self.contact_info_input.text().strip()
        
        if self.patient_type == 'niño':
            tutor_name = self.tutor_name_input.text().strip()
            if not tutor_name:
                QMessageBox.warning(self, "Campo Requerido", "El nombre del informante es obligatorio.")
                return
            if not self.treatment_consent_check.isChecked():
                QMessageBox.warning(self, "Consentimiento Requerido", "El consentimiento del tutor es obligatorio.")
                return
        else: # Adulto
            if not self.privacy_consent_check.isChecked() or not self.treatment_consent_check.isChecked():
                QMessageBox.warning(self, "Consentimiento Requerido", "Se debe aceptar la política de privacidad y el consentimiento para el tratamiento.")
                return

        if self.patient_type == 'niño':
            additional_data = self.collect_child_data()
            additional_data_json = json.dumps(additional_data, indent=4)
        else: # Adulto
            additional_data = self.collect_adult_data()
            additional_data_json = json.dumps(additional_data, indent=4)

        try:
            with session_scope() as session:
                patient_to_save = None
                if self.is_edit_mode:
                    patient_to_save = session.query(Patient).get(self.patient_id)
                
                if not patient_to_save: # Nuevo paciente
                    patient_to_save = Patient(patient_type=self.patient_type)
                    patient_to_save.psychologist_id = self.psychologist_id # Asignar psicólogo
                    session.add(patient_to_save)

                # Actualizar campos comunes y específicos
                patient_to_save.full_name = full_name
                patient_to_save.contact_info = contact_info
                patient_to_save.email = email
                patient_to_save.tutor_name = tutor_name
                
                # Asumiendo que tu modelo Patient tiene un campo `additional_data` de tipo TEXT
                if self.patient_type == 'adulto':
                    patient_to_save.additional_data = additional_data_json
                patient_to_save.additional_data = additional_data_json

            QMessageBox.information(self, "Éxito", "Paciente guardado correctamente.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", f"Ocurrió un error al guardar:\n{e}")
            self.reject()