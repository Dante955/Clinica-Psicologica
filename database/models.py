from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Float, Enum, Numeric, func
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

# Base para nuestros modelos declarativos
Base = declarative_base()

class UserRole(enum.Enum):
    ADMIN = "ADMIN"  # Administrador técnico del sistema
    PSICOLOGO = "PSICOLOGO"  # Psicólogo que atiende pacientes
    SOPORTE = "SOPORTE"  # Soporte técnico
    ADMINISTRACION = "ADMINISTRACION"  # Personal administrativo

class ExpenseTypeEnum(enum.Enum):
    GENERAL = "general"
    SALARIO = "salario"
    LUZ = "luz"
    AGUA = "agua"
    INTERNET = "internet"
    ALQUILER = "alquiler"

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # Usar String en lugar de Enum para SQL Server
    full_name = Column(String(150), nullable=False)
    specialization = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    appointments = relationship("Appointment", back_populates="psicologo")
    patients = relationship("Patient", back_populates="psychologist")
    salaries = relationship("Salary", back_populates="user")

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    contact_info = Column(String(100))
    email = Column(String(100), nullable=False)
    
    # Columna para asignar un paciente a un psicólogo
    psychologist_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    patient_type = Column(String(20), nullable=False, default='adulto')  # 'adulto' o 'niño'
    tutor_name = Column(String(100))  # Nombre del tutor si el paciente es un niño

    # --- CAMPOS ADICIONALES PARA EL FORMULARIO DE ADMISIÓN DE ADULTOS ---
    # Módulo 1: Datos Demográficos
    birth_date = Column(DateTime)
    gender_pronouns = Column(String(100))
    address = Column(String(250))
    emergency_contact = Column(String(150))
    referred_by = Column(String(150))

    # Módulo 2: Motivo de Consulta
    main_reason_for_consultation = Column(Text)
    current_symptoms = Column(Text)
    problem_duration = Column(String(100))
    therapy_expectations = Column(Text)
    previous_solution_attempts = Column(Text)

    # Módulo 3: Historia Clínica
    previous_mental_health_history = Column(Text)
    psychiatric_medication = Column(Text)
    other_medication = Column(Text)
    family_history = Column(Text)
    risk_assessment = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relación para acceder a las citas de un paciente
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    # Relación para acceder al psicólogo asignado
    psychologist = relationship("User", back_populates="patients")


class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    psychologist_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    appointment_time = Column(DateTime, nullable=False)
    notes = Column(Text)
    status = Column(String(50), default='scheduled')  # 'scheduled', 'completed', 'cancelled', 'no_show'
    price = Column(Numeric(10, 2))
    payment_status = Column(String(50), default='pendiente')  # 'pendiente', 'pagado'
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relación para el ingreso asociado
    income = relationship("Income", uselist=False, back_populates="appointment", cascade="all, delete-orphan")

    # Relaciones para acceder al paciente y psicólogo desde la cita
    patient = relationship("Patient", back_populates="appointments")
    psicologo = relationship("User", back_populates="appointments")


class Expense(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True)
    description = Column(String(200), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    expense_date = Column(DateTime, nullable=False)
    expense_type = Column(String(50), nullable=False, default='general')  # 'general', 'salario', 'luz', 'agua', 'internet', 'alquiler'
    month = Column(Integer, nullable=False)  # Mes del gasto (1-12)
    year = Column(Integer, nullable=False)  # Año del gasto
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

class Income(Base):
    __tablename__ = 'incomes'
    id = Column(Integer, primary_key=True)
    description = Column(String(200), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    income_date = Column(DateTime, nullable=False)
    # Relación para vincular un ingreso a una cita específica
    appointment_id = Column(Integer, ForeignKey('appointments.id'), nullable=True, unique=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    appointment = relationship("Appointment", back_populates="income")


class Salary(Base):
    __tablename__ = 'salaries'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    base_amount = Column(Numeric(10, 2), nullable=False)  # Salario base
    bonuses = Column(Numeric(10, 2), default=0)  # Comisiones o bonos
    deductions = Column(Numeric(10, 2), default=0)  # Deducciones
    # Nota: total_amount se calculará en Python o como columna computada en SQL Server
    payment_date = Column(DateTime)  # Fecha en la que se realizó el pago
    period_month = Column(Integer, nullable=False)  # Mes al que corresponde el salario (1-12)
    period_year = Column(Integer, nullable=False)  # Año al que corresponde el salario
    status = Column(String(50), default='pendiente')  # 'pendiente', 'pagado', 'cancelado'
    notes = Column(Text)  # Notas adicionales
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relación con usuario
    user = relationship("User", back_populates="salaries")
    
    @property
    def total_amount(self):
        """Calcula el total del salario (base + bonos - deducciones)"""
        base = float(self.base_amount or 0)
        bonus = float(self.bonuses or 0)
        deduct = float(self.deductions or 0)
        return base + bonus - deduct



# Ejemplo de cómo inicializar la base de datos
def setup_database(engine=None):
    """
    Crea todas las tablas en la base de datos.
    
    Args:
        engine: Motor de SQLAlchemy opcional. Si no se proporciona,
                se usa el engine del database_manager.
    """
    if engine is None:
        from database.database_manager import engine as default_engine
        engine = default_engine
    
    Base.metadata.create_all(engine)
    print("Base de datos y tablas creadas.")

if __name__ == '__main__':
    setup_database()
