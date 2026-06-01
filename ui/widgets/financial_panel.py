from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDateEdit, QFormLayout, QGroupBox, QMessageBox, QFileDialog, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import QDate, Qt

# Se eliminó la importación del widget del gráfico (evitando el ImportError)
from ui.dialogs.expense_form_dialog import ExpenseFormDialog
from ui.dialogs.income_form_dialog import IncomeFormDialog
from ui.dialogs.export_report_dialog import ExportReportDialog
from ui.dialogs.salary_management_dialog import SalaryManagementDialog

from core.reporting import ReportingService
from database.database_manager import session_scope
from database.models import User, Salary
import os

class FinancialPanel(QWidget):
    def __init__(self, auth_service=None, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.reporting_service = ReportingService()
        self.is_admin = False
        
        # Verificar si el usuario actual es admin
        if auth_service and hasattr(auth_service, 'get_current_user_role'):
            from database.models import UserRole
            role = auth_service.get_current_user_role()
            self.is_admin = (role == UserRole.ADMIN)
        
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Panel de Controles ---
        controls_group = QGroupBox("Filtros y Acciones")
        controls_layout = QHBoxLayout(controls_group)

        # Widgets de fecha
        self.start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_edit.setCalendarPopup(True)
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)

        # Botones
        self.generate_report_button = QPushButton("📊 Generar Reporte")
        self.generate_report_button.clicked.connect(self.update_report)

        self.add_income_button = QPushButton("💰 Añadir Ingreso")
        self.add_income_button.clicked.connect(self.open_income_form)

        self.add_expense_button = QPushButton("➕ Añadir Gasto")
        self.add_expense_button.clicked.connect(self.open_expense_form)

        self.export_excel_button = QPushButton("📥 Exportar Excel")
        self.export_excel_button.clicked.connect(self.export_financial_report_to_excel)

        self.manage_salaries_button = QPushButton("💼 Gestionar Salarios")
        self.manage_salaries_button.clicked.connect(self.open_salary_management)
        self.manage_salaries_button.setEnabled(self.is_admin)

        # Layout del formulario para las fechas
        form_layout = QFormLayout()
        form_layout.addRow("Fecha de Inicio:", self.start_date_edit)
        form_layout.addRow("Fecha de Fin:", self.end_date_edit)

        controls_layout.addLayout(form_layout)
        
        # Uso de Qt.AlignmentFlag para compatibilidad con PySide6
        align_bottom = Qt.AlignmentFlag.AlignBottom
        controls_layout.addWidget(self.generate_report_button, 0, align_bottom)
        controls_layout.addWidget(self.add_income_button, 0, align_bottom)
        controls_layout.addWidget(self.add_expense_button, 0, align_bottom)
        controls_layout.addWidget(self.export_excel_button, 0, align_bottom)
        controls_layout.addWidget(self.manage_salaries_button, 0, align_bottom)
        controls_layout.addStretch()

        # --- Panel de Resumen ---
        summary_group = QGroupBox("Resumen Financiero")
        summary_layout = QHBoxLayout(summary_group)
        
        self.income_label = QLabel("Ingresos: C$0.00")
        self.expenses_label = QLabel("Gastos: C$0.00")
        self.profit_label = QLabel("Beneficio: C$0.00")

        for label in [self.income_label, self.expenses_label, self.profit_label]:
            label.setObjectName("summaryLabel")
            summary_layout.addWidget(label)

        # --- Panel de Empleados y Salarios ---
        employees_group = QGroupBox("Salarios de Empleados")
        employees_layout = QVBoxLayout(employees_group)

        self.employees_table = QTableWidget()
        self.employees_table.setColumnCount(3)
        self.employees_table.setHorizontalHeaderLabels(["Usuario", "Nombre Completo", "Salario Base (C$)"])
        self.employees_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.employees_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.employees_table.setColumnWidth(2, 150)
        self.employees_table.setMaximumHeight(200)

        employees_layout.addWidget(self.employees_table)

        # --- Ensamblaje Final ---
        main_layout.addWidget(controls_group)
        main_layout.addWidget(summary_group)
        main_layout.addWidget(employees_group)
        # Se añade un espacio elástico final para empujar el contenido hacia arriba de forma ordenada
        main_layout.addStretch()

        # Generar el reporte inicial y cargar empleados
        self.update_report()
        self.load_employees_salaries()

    def open_income_form(self):
        """Abre el formulario para añadir ingresos."""
        try:
            dialog = IncomeFormDialog(parent=self)
            dialog.exec()
            self.update_report()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el formulario de ingresos: {e}")

    def open_expense_form(self):
        """Abre el formulario para añadir gastos."""
        try:
            dialog = ExpenseFormDialog(parent=self)
            dialog.exec()
            self.update_report()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el formulario de gastos: {e}")

    def update_report(self):
        """Obtiene los datos y actualiza el panel."""
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().addDays(1).toPython()

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.min.time())

        try:
            summary = self.reporting_service.get_financial_summary(start_dt, end_dt)
            income = summary.get("income", 0)
            expenses = summary.get("expenses", 0)
            profit = income - expenses

            self.income_label.setText(f"Ingresos: C${income:,.2f}")
            self.expenses_label.setText(f"Gastos: C${expenses:,.2f}")
            self.profit_label.setText(f"Beneficio: C${profit:,.2f}")

        except Exception as e:
            QMessageBox.warning(
                self, 
                "Error al cargar datos", 
                f"Ocurrió un inconveniente al obtener el resumen financiero:\n{e}"
            )

    def refresh_data(self):
        """Método público para refrescar los reportes."""
        self.update_report()
        self.load_employees_salaries()

    def export_financial_report_to_excel(self):
        """Exporta el reporte financiero a un archivo Excel."""
        try:
            start_date = self.start_date_edit.date().toPython()
            end_date = self.end_date_edit.date().addDays(1).toPython()

            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.min.time())

            # Abrir el diálogo para seleccionar categorías
            dialog = ExportReportDialog(start_dt, end_dt, parent=self)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error al exportar",
                f"No se pudo exportar el reporte:\n{e}"
            )

    def load_employees_salaries(self):
        """Carga la tabla de salarios de empleados."""
        try:
            with session_scope() as session:
                # Obtener todos los usuarios (excepto admin)
                from database.models import UserRole
                employees = session.query(User).filter(
                    User.role.in_([UserRole.PSICOLOGO.value, UserRole.SOPORTE.value, UserRole.ADMINISTRACION.value])
                ).all()

                self.employees_table.setRowCount(len(employees))

                for row, employee in enumerate(employees):
                    # Usuario
                    user_item = QTableWidgetItem(employee.username)
                    user_item.setFlags(user_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.employees_table.setItem(row, 0, user_item)

                    # Nombre completo
                    name_item = QTableWidgetItem(employee.full_name)
                    name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.employees_table.setItem(row, 1, name_item)

                    # Obtener salario base actual
                    salary = session.query(Salary).filter(
                        Salary.user_id == employee.id
                    ).order_by(Salary.period_year.desc(), Salary.period_month.desc()).first()

                    salary_base = float(salary.base_amount) if salary else 0.0

                    # Monto del salario
                    salary_item = QTableWidgetItem(f"C${salary_base:,.2f}")
                    salary_item.setFlags(salary_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.employees_table.setItem(row, 2, salary_item)

        except Exception as e:
            import logging
            logging.error(f"Error al cargar salarios de empleados: {e}")

    def open_salary_management(self):
        """Abre el diálogo de gestión de salarios."""
        try:
            dialog = SalaryManagementDialog(parent=self, is_admin=self.is_admin)
            if dialog.exec():
                # Recargar la tabla de salarios después de hacer cambios
                self.load_employees_salaries()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir el diálogo de gestión de salarios:\n{e}"
            )