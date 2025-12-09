from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QHBoxLayout, QMessageBox, QDateEdit, QDoubleSpinBox
)
from PySide6.QtCore import QDate
from database.database_manager import session_scope
from database.models import Income
from datetime import datetime

class IncomeFormDialog(QDialog):
    def __init__(self, income_id=None, parent=None):
        super().__init__(parent)
        self.income_id = income_id
        self.is_edit_mode = self.income_id is not None

        self.setWindowTitle("Editar Ingreso" if self.is_edit_mode else "Añadir Ingreso")
        self.setMinimumWidth(400)
        self.setup_ui()

        if self.is_edit_mode:
            self.load_income_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.description_input = QLineEdit()
        self.amount_spinbox = QDoubleSpinBox()
        self.amount_spinbox.setRange(0, 9999999.99)
        self.amount_spinbox.setPrefix("C$ ")  # Moneda en Córdobas
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)

        form_layout.addRow("Descripción:", self.description_input)
        form_layout.addRow("Monto:", self.amount_spinbox)
        form_layout.addRow("Fecha:", self.date_edit)

        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_income)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)

        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

    def load_income_data(self):
        with session_scope() as session:
            income = session.get(Income, self.income_id)
            if income:
                self.description_input.setText(income.description)
                self.amount_spinbox.setValue(income.amount)
                self.date_edit.setDate(income.income_date)

    def save_income(self):
        description = self.description_input.text().strip()
        amount = self.amount_spinbox.value()
        income_date = self.date_edit.date().toPython()

        if not description or amount <= 0:
            QMessageBox.warning(self, "Datos incompletos", "La descripción y un monto mayor a cero son requeridos.")
            return

        with session_scope() as session:
            income = session.get(Income, self.income_id) if self.is_edit_mode else Income()
            income.description = description
            income.amount = amount
            income.income_date = datetime.combine(income_date, datetime.min.time())
            if not self.is_edit_mode:
                session.add(income)

        QMessageBox.information(self, "Éxito", "Ingreso guardado correctamente.")
        self.accept()