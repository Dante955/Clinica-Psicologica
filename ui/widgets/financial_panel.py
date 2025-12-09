# ui/widgets/financial_panel.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDateEdit, QFormLayout, QGroupBox
)
from PySide6.QtCore import QDate, Qt

# --- MODIFICADO ---
# Se importan ambos diálogos
from .plot_widget import MplPlotWidget
from ui.dialogs.expense_form_dialog import ExpenseFormDialog
from ui.dialogs.income_form_dialog import IncomeFormDialog  # Asumimos que este diálogo existe

from core.reporting import ReportingService
from datetime import datetime

class FinancialPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.reporting_service = ReportingService()
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

        # Botón para generar el reporte
        self.generate_report_button = QPushButton("📊 Generar Reporte")
        self.generate_report_button.clicked.connect(self.update_report)

        # --- AÑADIDO: Botón para añadir ingresos ---
        self.add_income_button = QPushButton("💰 Añadir Ingreso")
        self.add_income_button.clicked.connect(self.open_income_form)

        # Botón para añadir gastos
        self.add_expense_button = QPushButton("➕ Añadir Gasto")
        self.add_expense_button.clicked.connect(self.open_expense_form)

        # Layout del formulario para las fechas
        form_layout = QFormLayout()
        form_layout.addRow("Fecha de Inicio:", self.start_date_edit)
        form_layout.addRow("Fecha de Fin:", self.end_date_edit)

        controls_layout.addLayout(form_layout)
        controls_layout.addWidget(self.generate_report_button, 0, Qt.AlignBottom)
        # --- AÑADIDO: Se agrega el botón de ingresos al layout ---
        controls_layout.addWidget(self.add_income_button, 0, Qt.AlignBottom)
        controls_layout.addWidget(self.add_expense_button, 0, Qt.AlignBottom)
        controls_layout.addStretch()

        # --- Panel de Resumen ---
        summary_group = QGroupBox("Resumen Financiero")
        summary_layout = QHBoxLayout(summary_group)
        
        self.income_label = QLabel("Ingresos: $0.00")
        self.expenses_label = QLabel("Gastos: $0.00")
        self.profit_label = QLabel("Beneficio: $0.00")

        for label in [self.income_label, self.expenses_label, self.profit_label]:
            label.setObjectName("summaryLabel")
            summary_layout.addWidget(label)

        # --- Gráfico ---
        self.plot_widget = MplPlotWidget()

        # --- Ensamblaje Final ---
        main_layout.addWidget(controls_group)
        main_layout.addWidget(summary_group)
        main_layout.addWidget(self.plot_widget)

        # Generar el reporte inicial
        self.update_report()

    # --- AÑADIDO: Método para abrir el formulario de ingresos ---
    def open_income_form(self):
        """Abre el formulario para añadir ingresos."""
        dialog = IncomeFormDialog(parent=self)
        # El método exec() es bloqueante, espera a que el diálogo se cierre
        dialog.exec()
        # Actualiza el reporte después de cualquier acción en el diálogo
        self.update_report()

    def open_expense_form(self):
        """Abre el formulario para añadir gastos."""
        dialog = ExpenseFormDialog(parent=self)
        dialog.exec()
        self.update_report()  # Recargar el reporte después de guardar o cancelar

    def update_report(self):
        """Obtiene los datos y actualiza el panel."""
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().addDays(1).toPython()

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.min.time())

        # 1. Obtener resumen financiero
        summary = self.reporting_service.get_financial_summary(start_dt, end_dt)
        
        income = summary.get("income", 0)
        expenses = summary.get("expenses", 0)
        profit = income - expenses # Cálculo explícito para asegurar consistencia

        self.income_label.setText(f"Ingresos: C${income:,.2f}") # Cambiado a córdobas
        self.expenses_label.setText(f"Gastos: C${expenses:,.2f}")
        self.profit_label.setText(f"Beneficio: C${profit:,.2f}")

        # 2. Actualizar el gráfico
        self.plot_financial_summary(income, expenses, profit)

    def plot_financial_summary(self, income, expenses, profit):
        """Dibuja un gráfico de barras con el resumen."""
        self.plot_widget.figure.clear()
        ax = self.plot_widget.figure.add_subplot(111)

        categories = ["Ingresos", "Gastos", "Beneficio"]
        values = [income, expenses, profit]
        colors = ['#A3BE8C', '#BF616A', '#5E81AC']

        bars = ax.bar(categories, values, color=colors) 

        ax.set_ylabel("Monto (C$)")
        ax.set_title("Resumen Financiero (Córdobas)")
        ax.grid(axis='y', linestyle='--', alpha=0.7)

        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2.0, yval, f'C${yval:,.2f}',
                    va='bottom' if yval >= 0 else 'top', ha='center')

        self.plot_widget.canvas.draw()

    def refresh_data(self):
        """Método público para refrescar los reportes."""
        self.update_report()