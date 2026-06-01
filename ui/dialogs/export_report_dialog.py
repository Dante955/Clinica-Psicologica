from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox,
    QGroupBox, QLabel, QMessageBox
)
from PySide6.QtCore import Qt
from datetime import datetime
from core.reporting import ReportingService
from PySide6.QtWidgets import QFileDialog


class ExportReportDialog(QDialog):
    def __init__(self, start_date: datetime, end_date: datetime, parent=None):
        super().__init__(parent)
        self.start_date = start_date
        self.end_date = end_date
        self.reporting_service = ReportingService()
        self.selected_categories = []
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle("Exportar Reporte Financiero")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel("Selecciona las categorías de gastos a incluir:")
        layout.addWidget(title_label)
        
        # Grupo de checkboxes
        categories_group = QGroupBox("Categorías de Gastos")
        categories_layout = QVBoxLayout(categories_group)
        
        self.categories = {
            "Salario": "salario",
            "Luz": "luz",
            "Agua": "agua",
            "Internet": "internet",
            "Alquiler": "alquiler",
            "General": "general"
        }
        
        self.checkboxes = {}
        for display_name, category_value in self.categories.items():
            checkbox = QCheckBox(display_name)
            checkbox.setChecked(True)
            self.checkboxes[category_value] = checkbox
            categories_layout.addWidget(checkbox)
        
        layout.addWidget(categories_group)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        
        select_all_button = QPushButton("Seleccionar Todo")
        select_all_button.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_button)
        
        deselect_all_button = QPushButton("Deseleccionar Todo")
        deselect_all_button.clicked.connect(self.deselect_all)
        button_layout.addWidget(deselect_all_button)
        
        layout.addLayout(button_layout)
        
        # Botones de diálogo
        dialog_button_layout = QHBoxLayout()
        
        export_button = QPushButton("Exportar")
        export_button.clicked.connect(self.export_report)
        dialog_button_layout.addWidget(export_button)
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        dialog_button_layout.addWidget(cancel_button)
        
        layout.addLayout(dialog_button_layout)
    
    def select_all(self):
        """Selecciona todas las categorías."""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)
    
    def deselect_all(self):
        """Deselecciona todas las categorías."""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)
    
    def export_report(self):
        """Exporta el reporte con las categorías seleccionadas."""
        # Obtener categorías seleccionadas
        selected_categories = [
            category for category, checkbox in self.checkboxes.items()
            if checkbox.isChecked()
        ]
        
        if not selected_categories:
            QMessageBox.warning(
                self,
                "Advertencia",
                "Debes seleccionar al menos una categoría."
            )
            return
        
        # Preguntar dónde guardar el archivo
        file_dialog = QFileDialog()
        default_filename = f"Reporte_Financiero_{self.start_date.strftime('%d-%m-%Y')}_a_{self.end_date.strftime('%d-%m-%Y')}.xlsx"
        file_path, _ = file_dialog.getSaveFileName(
            self,
            "Guardar reporte financiero",
            default_filename,
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if not file_path:
            return  # Usuario canceló
        
        # Asegurar que tenga extensión .xlsx
        if not file_path.endswith('.xlsx'):
            file_path += '.xlsx'
        
        try:
            # Exportar el reporte
            self.reporting_service.export_financial_report_to_excel(
                self.start_date,
                self.end_date,
                file_path,
                selected_categories
            )
            
            QMessageBox.information(
                self,
                "Éxito",
                f"Reporte exportado correctamente a:\n{file_path}"
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error al exportar",
                f"No se pudo exportar el reporte:\n{e}"
            )
