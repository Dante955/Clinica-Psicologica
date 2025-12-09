-- Script de creación de base de datos SQL Server (T-SQL)
-- Sistema de Gestión de Consultorio Psicológico

-- ============================================
-- 1. CREAR BASE DE DATOS
-- ============================================

USE master;
GO

IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'clinic_db')
BEGIN
    CREATE DATABASE clinic_db;
END
GO

USE clinic_db;
GO

-- ============================================
-- 2. CREAR TABLAS
-- ============================================

-- Tabla de usuarios
-- Nota: Los ENUMs se manejan aquí con CHECK CONSTRAINTS
IF OBJECT_ID('dbo.users', 'U') IS NOT NULL DROP TABLE dbo.users;
GO

CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(100) UNIQUE NOT NULL,
    hashed_password NVARCHAR(255) NOT NULL,
    role NVARCHAR(50) NOT NULL,
    full_name NVARCHAR(150) NOT NULL,
    specialization NVARCHAR(150),
    created_at DATETIME2 DEFAULT SYSDATETIME(),
    updated_at DATETIME2 DEFAULT SYSDATETIME(),

    CONSTRAINT chk_user_role CHECK (role IN ('ADMIN', 'PSICOLOGO', 'SOPORTE', 'ADMINISTRACION'))
);
GO

-- Tabla de pacientes
IF OBJECT_ID('dbo.patients', 'U') IS NOT NULL DROP TABLE dbo.patients;
GO

CREATE TABLE patients (
    id INT IDENTITY(1,1) PRIMARY KEY,
    full_name NVARCHAR(100) NOT NULL,
    contact_info NVARCHAR(100),
    email NVARCHAR(100) NOT NULL,
    psychologist_id INT,
    patient_type NVARCHAR(20) NOT NULL DEFAULT 'adulto',
    tutor_name NVARCHAR(100),
    
    -- Módulo 1: Datos Demográficos
    birth_date DATETIME2,
    gender_pronouns NVARCHAR(100),
    address NVARCHAR(250),
    emergency_contact NVARCHAR(150),
    referred_by NVARCHAR(150),
    
    -- Módulo 2: Motivo de Consulta
    main_reason_for_consultation NVARCHAR(MAX),
    current_symptoms NVARCHAR(MAX),
    problem_duration NVARCHAR(100),
    therapy_expectations NVARCHAR(MAX),
    previous_solution_attempts NVARCHAR(MAX),
    
    -- Módulo 3: Historia Clínica
    previous_mental_health_history NVARCHAR(MAX),
    psychiatric_medication NVARCHAR(MAX),
    other_medication NVARCHAR(MAX),
    family_history NVARCHAR(MAX),
    risk_assessment NVARCHAR(MAX),
    
    created_at DATETIME2 DEFAULT SYSDATETIME(),
    updated_at DATETIME2 DEFAULT SYSDATETIME(),
    
    CONSTRAINT FK_patients_users FOREIGN KEY (psychologist_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_patient_type CHECK (patient_type IN ('adulto', 'niño'))
);
GO

-- Tabla de citas
IF OBJECT_ID('dbo.appointments', 'U') IS NOT NULL DROP TABLE dbo.appointments;
GO

CREATE TABLE appointments (
    id INT IDENTITY(1,1) PRIMARY KEY,
    patient_id INT NOT NULL,
    psychologist_id INT NOT NULL,
    appointment_time DATETIME2 NOT NULL,
    notes NVARCHAR(MAX),
    status NVARCHAR(50) DEFAULT 'scheduled',
    price DECIMAL(10, 2),
    payment_status NVARCHAR(50) DEFAULT 'pendiente',
    created_at DATETIME2 DEFAULT SYSDATETIME(),
    updated_at DATETIME2 DEFAULT SYSDATETIME(),
    
    CONSTRAINT FK_appointments_patients FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    CONSTRAINT FK_appointments_users FOREIGN KEY (psychologist_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_status CHECK (status IN ('scheduled', 'completed', 'cancelled', 'no_show')),
    CONSTRAINT chk_payment_status CHECK (payment_status IN ('pendiente', 'pagado'))
);
GO

-- Tabla de gastos
IF OBJECT_ID('dbo.expenses', 'U') IS NOT NULL DROP TABLE dbo.expenses;
GO

CREATE TABLE expenses (
    id INT IDENTITY(1,1) PRIMARY KEY,
    description NVARCHAR(200) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    expense_date DATETIME2 NOT NULL,
    expense_type NVARCHAR(50) NOT NULL DEFAULT 'general',
    month INT NOT NULL,
    year INT NOT NULL,
    created_at DATETIME2 DEFAULT SYSDATETIME(),
    updated_at DATETIME2 DEFAULT SYSDATETIME(),
    
    CONSTRAINT chk_month CHECK (month BETWEEN 1 AND 12),
    CONSTRAINT chk_year CHECK (year >= 2000),
    CONSTRAINT chk_amount CHECK (amount >= 0),
    CONSTRAINT chk_expense_type CHECK (expense_type IN ('general', 'salario', 'luz', 'agua', 'internet', 'alquiler'))
);
GO

-- Tabla de ingresos
IF OBJECT_ID('dbo.incomes', 'U') IS NOT NULL DROP TABLE dbo.incomes;
GO

CREATE TABLE incomes (
    id INT IDENTITY(1,1) PRIMARY KEY,
    description NVARCHAR(200) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    income_date DATETIME2 NOT NULL,
    appointment_id INT UNIQUE,
    created_at DATETIME2 DEFAULT SYSDATETIME(),
    updated_at DATETIME2 DEFAULT SYSDATETIME(),
    
    CONSTRAINT FK_incomes_appointments FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE SET NULL,
    CONSTRAINT chk_income_amount CHECK (amount >= 0)
);
GO

-- ============================================
-- TABLA DE SALARIOS (NÓMINA)
-- ============================================

IF OBJECT_ID('dbo.salaries', 'U') IS NOT NULL DROP TABLE dbo.salaries;
GO

CREATE TABLE salaries (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,                  -- Relación con la tabla users (quién recibe el pago)
    base_amount DECIMAL(10, 2) NOT NULL,   -- Salario base
    bonuses DECIMAL(10, 2) DEFAULT 0,      -- Comisiones o bonos (ej. por número de pacientes)
    deductions DECIMAL(10, 2) DEFAULT 0,   -- Deducciones (impuestos, adelantos, etc.)
    
    -- Columna calculada: El total se calcula automáticamente
    total_amount AS (base_amount + bonuses - deductions) PERSISTED,
    
    payment_date DATETIME2,                -- Fecha en la que se realizó el pago
    period_month INT NOT NULL,             -- Mes al que corresponde el salario
    period_year INT NOT NULL,              -- Año al que corresponde el salario
    
    status NVARCHAR(50) DEFAULT 'pendiente', -- Estado del pago
    notes NVARCHAR(MAX),                   -- Notas adicionales (ej. detalle de bonos)
    
    created_at DATETIME2 DEFAULT SYSDATETIME(),
    updated_at DATETIME2 DEFAULT SYSDATETIME(),

    -- Restricciones (Foreign Keys y Checks)
    CONSTRAINT FK_salaries_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION,
    CONSTRAINT chk_salary_month CHECK (period_month BETWEEN 1 AND 12),
    CONSTRAINT chk_salary_year CHECK (period_year >= 2000),
    CONSTRAINT chk_salary_status CHECK (status IN ('pendiente', 'pagado', 'cancelado')),
    CONSTRAINT chk_salary_positive CHECK (base_amount >= 0 AND bonuses >= 0 AND deductions >= 0)
);
GO

-- ============================================
-- ÍNDICES PARA LA TABLA SALARIOS
-- ============================================

-- Índice para buscar salarios por usuario
CREATE INDEX idx_salaries_user ON salaries(user_id);

-- Índice para reportes por periodo (mes/año)
CREATE INDEX idx_salaries_period ON salaries(period_month, period_year);

-- Índice para filtrar por estado (pendientes vs pagados)
CREATE INDEX idx_salaries_status ON salaries(status);
GO

-- ============================================
-- TRIGGER DE ACTUALIZACIÓN (UPDATED_AT)
-- ============================================

CREATE TRIGGER trg_salaries_updated_at
ON salaries
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT UPDATE(updated_at)
    BEGIN
        UPDATE salaries
        SET updated_at = SYSDATETIME()
        FROM salaries s
        INNER JOIN inserted i ON s.id = i.id;
    END
END
GO

-- ============================================
-- DESCRIPCIÓN DE LA TABLA
-- ============================================
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Registro de nómina y pagos a empleados/psicólogos', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'salaries';
GO
-- ============================================
-- 3. CREAR ÍNDICES
-- ============================================

CREATE INDEX idx_patients_psychologist ON patients(psychologist_id);
CREATE INDEX idx_patients_email ON patients(email);
CREATE INDEX idx_patients_full_name ON patients(full_name);
GO

CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_psychologist ON appointments(psychologist_id);
CREATE INDEX idx_appointments_time ON appointments(appointment_time);
CREATE INDEX idx_appointments_status ON appointments(status);
GO

CREATE INDEX idx_expenses_date ON expenses(expense_date);
CREATE INDEX idx_expenses_month_year ON expenses(month, year);
CREATE INDEX idx_expenses_type ON expenses(expense_type);
GO

CREATE INDEX idx_incomes_date ON incomes(income_date);
CREATE INDEX idx_incomes_appointment ON incomes(appointment_id);
GO

-- ============================================
-- 4. TRIGGERS PARA UPDATED_AT
-- ============================================
-- En SQL Server no existe "BEFORE UPDATE" para modificar NEW.
-- Se usa AFTER UPDATE y se actualiza la tabla uniendo con la tabla virtual "inserted".

-- Trigger para users
CREATE TRIGGER trg_users_updated_at
ON users
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT UPDATE(updated_at) -- Evitar recursividad
    BEGIN
        UPDATE users
        SET updated_at = SYSDATETIME()
        FROM users u
        INNER JOIN inserted i ON u.id = i.id;
    END
END
GO

-- Trigger para patients
CREATE TRIGGER trg_patients_updated_at
ON patients
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT UPDATE(updated_at)
    BEGIN
        UPDATE patients
        SET updated_at = SYSDATETIME()
        FROM patients p
        INNER JOIN inserted i ON p.id = i.id;
    END
END
GO

-- Trigger para appointments
CREATE TRIGGER trg_appointments_updated_at
ON appointments
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT UPDATE(updated_at)
    BEGIN
        UPDATE appointments
        SET updated_at = SYSDATETIME()
        FROM appointments a
        INNER JOIN inserted i ON a.id = i.id;
    END
END
GO

-- Trigger para expenses
CREATE TRIGGER trg_expenses_updated_at
ON expenses
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT UPDATE(updated_at)
    BEGIN
        UPDATE expenses
        SET updated_at = SYSDATETIME()
        FROM expenses e
        INNER JOIN inserted i ON e.id = i.id;
    END
END
GO

-- Trigger para incomes
CREATE TRIGGER trg_incomes_updated_at
ON incomes
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT UPDATE(updated_at)
    BEGIN
        UPDATE incomes
        SET updated_at = SYSDATETIME()
        FROM incomes Inc
        INNER JOIN inserted i ON Inc.id = i.id;
    END
END
GO

-- ============================================
-- 5. INSERTAR DATOS INICIALES
-- ============================================

-- Insertar admin si no existe
IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin')
BEGIN
    INSERT INTO users (username, hashed_password, role, full_name, specialization)
    VALUES (
        'admin',
        'scrypt:32768:8:1$YourHashedPasswordHere', 
        'ADMIN',
        'Administrador del Sistema',
        NULL
    );
END
GO

-- ============================================
-- 6. DESCRIPCIONES (Extended Properties)
-- ============================================
-- En SQL Server los comentarios en tablas se agregan como propiedades extendidas

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Usuarios del sistema (psicólogos, administradores, soporte)', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'users';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Pacientes del consultorio', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'patients';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Citas programadas entre pacientes y psicólogos', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'appointments';
GO