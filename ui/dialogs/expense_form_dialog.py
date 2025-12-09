from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QHBoxLayout, QMessageBox, QDateEdit, QDoubleSpinBox, QComboBox
)
from PySide6.QtCore import QDate
from database.database_manager import session_scope
from database.models import Expense, ExpenseTypeEnum
from datetime import datetime

class ExpenseFormDialog(QDialog):
    def __init__(self, expense_id=None, parent=None):
        super().__init__(parent)
        self.expense_id = expense_id
        self.is_edit_mode = self.expense_id is not None

        self.setWindowTitle("Editar Gasto" if self.is_edit_mode else "Añadir Gasto")
        self.setMinimumWidth(400)
        self.setup_ui()

        if self.is_edit_mode:
            self.load_expense_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.description_input = QLineEdit()
        self.amount_spinbox = QDoubleSpinBox()
        self.amount_spinbox.setRange(0, 9999999.99)
        self.amount_spinbox.setPrefix("C$ ")  # Moneda en Córdobas
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.type_combo = QComboBox()
        self.type_combo.addItems([e.value for e in ExpenseTypeEnum])

        form_layout.addRow("Descripción:", self.description_input)
        form_layout.addRow("Monto:", self.amount_spinbox)
        form_layout.addRow("Fecha:", self.date_edit)
        form_layout.addRow("Tipo de Gasto:", self.type_combo)

        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_expense)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)

        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

    def load_expense_data(self):
        with session_scope() as session:
            expense = session.get(Expense, self.expense_id)
            if expense:
                self.description_input.setText(expense.description)
                self.amount_spinbox.setValue(expense.amount)
                self.date_edit.setDate(expense.expense_date)
                self.type_combo.setCurrentText(expense.expense_type)

    def save_expense(self):
        description = self.description_input.text().strip()
        amount = self.amount_spinbox.value()
        expense_date = self.date_edit.date().toPython()
        expense_type = self.type_combo.currentText()

        if not description or amount <= 0:
            QMessageBox.warning(self, "Datos incompletos", "La descripción y un monto mayor a cero son requeridos.")
            return

        try:
            with session_scope() as session:
                if self.is_edit_mode:
                    expense = session.get(Expense, self.expense_id)
                else:
                    expense = Expense()
                    session.add(expense)

                expense.description = description
                expense.amount = amount
                expense.expense_date = datetime.combine(expense_date, datetime.min.time())
                expense.expense_type = expense_type
                expense.month = expense_date.month
                expense.year = expense_date.year

            QMessageBox.information(self, "Éxito", "Gasto guardado correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", f"Ocurrió un error al guardar el gasto:\n{e}")
            self.reject()