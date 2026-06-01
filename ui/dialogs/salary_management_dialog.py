from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QSpinBox, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt
from database.database_manager import session_scope
from database.models import User, UserRole, Salary
from datetime import datetime
import logging


class SalaryManagementDialog(QDialog):
    def __init__(self, parent=None, is_admin=False):
        super().__init__(parent)
        self.is_admin = is_admin
        self.setup_ui()
        self.load_employees()
        
    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle("Gestión de Salarios de Empleados")
        self.setGeometry(100, 100, 700, 400)
        
        layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel("Salarios de Empleados (Monto Base)")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title_label)
        
        # Tabla de empleados
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Usuario", "Nombre Completo", "Salario Base (C$)", "Acción"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 100)
        
        layout.addWidget(self.table)
        
        # Información
        info_label = QLabel("Solo administradores pueden editar salarios.")
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(info_label)
        
        # Botones
        button_layout = QHBoxLayout()
        
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def load_employees(self):
        """Carga los empleados con sus salarios."""
        with session_scope() as session:
            # Obtener todos los usuarios (excepto admin)
            employees = session.query(User).filter(
                User.role.in_([UserRole.PSICOLOGO.value, UserRole.SOPORTE.value, UserRole.ADMINISTRACION.value])
            ).all()
            
            self.table.setRowCount(len(employees))
            
            for row, employee in enumerate(employees):
                # Usuario
                user_item = QTableWidgetItem(employee.username)
                user_item.setFlags(user_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 0, user_item)
                
                # Nombre completo
                name_item = QTableWidgetItem(employee.full_name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 1, name_item)
                
                # Obtener salario base actual
                salary = session.query(Salary).filter(
                    Salary.user_id == employee.id,
                    Salary.status == 'pendiente'
                ).order_by(Salary.payment_date.desc()).first()
                
                salary_base = float(salary.base_amount) if salary else 0.0
                
                # Spinbox para el salario (editable solo para admin)
                spinbox = QSpinBox()
                spinbox.setMaximum(1000000)
                spinbox.setValue(int(salary_base))
                spinbox.setEnabled(self.is_admin)
                spinbox.valueChanged.connect(lambda value, emp_id=employee.id: self.on_salary_changed(emp_id, value))
                self.table.setCellWidget(row, 2, spinbox)
                
                # Botón para guardar (solo si es admin)
                save_button = QPushButton("Guardar")
                save_button.setEnabled(self.is_admin)
                save_button.clicked.connect(lambda checked, emp_id=employee.id, row_idx=row: self.save_salary(emp_id, row_idx))
                self.table.setCellWidget(row, 3, save_button)
    
    def on_salary_changed(self, employee_id, new_salary):
        """Se ejecuta cuando cambia el valor del salario."""
        # Aquí solo actualizamos el spinbox, no guardamos aún
        pass
    
    def save_salary(self, employee_id, row):
        """Guarda el salario del empleado."""
        if not self.is_admin:
            QMessageBox.warning(self, "Permisos", "Solo administradores pueden editar salarios.")
            return
        
        spinbox = self.table.cellWidget(row, 2)
        new_salary = spinbox.value()
        
        try:
            with session_scope() as session:
                employee = session.query(User).filter(User.id == employee_id).first()
                if not employee:
                    QMessageBox.critical(self, "Error", "Empleado no encontrado.")
                    return
                
                # Crear un nuevo registro de salario
                salary = Salary(
                    user_id=employee_id,
                    base_amount=new_salary,
                    bonuses=0,
                    deductions=0,
                    payment_date=datetime.now(),
                    period_month=datetime.now().month,
                    period_year=datetime.now().year,
                    status='pendiente'
                )
                session.add(salary)
                session.commit()
                
                logging.info(f"Salario actualizado para {employee.username}: C${new_salary}")
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Salario guardado para {employee.full_name}: C${new_salary:.2f}"
                )
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", f"No se pudo guardar el salario:\n{e}")
            logging.error(f"Error al guardar salario: {e}")
