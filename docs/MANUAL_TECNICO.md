# Manual Técnico - Clínica Psicológica

## 1. Visión General del Sistema

La aplicación **Clínica Psicológica** es un sistema de escritorio desarrollado en **Python** utilizando **PySide6** (Qt) para la interfaz gráfica. Su objetivo es gestionar pacientes, citas, usuarios y reportes financieros.

Estilos y temas: Utiliza una paleta de colores moderna (Nord Theme) y hojas de estilo QSS personalizadas.

## 2. Pila Tecnológica

- **Lenguaje**: Python 3.10+
- **Interfaz Gráfica**: PySide6 (Qt for Python).
- **ORM**: SQLAlchemy.
- **Base de Datos**: Soporte híbrido para **SQLite** (local/dev) y **Microsoft SQL Server** (producción/red).
- **Driver SQL**: `pyodbc` con "ODBC Driver 17 for SQL Server".
- **Gráficos**: Matplotlib para reportes financieros.
- **Empaquetado**: PyInstaller para generar ejecutables (.exe).

## 3. Arquitectura del Proyecto

El proyecto sigue una estructura modular:

- **`main.py`**: Punto de entrada. Inicializa lógicas, logs y la ventana principal.
- **`core/`**: Lógica de negocio pura (Authentication, Reporting, Notification, ClinicLogic).
- **`database/`**:
  - `models.py`: Definición de tablas (User, Patient, Appointment, etc.).
  - `database_manager.py`: Gestión de conexiones y sesiones.
  - `database_migrator.py`: Lógica para migrar datos de SQLite a SQL Server.
- **`ui/`**: Componentes de la interfaz.
  - `main_window.py`: Ventana principal y navegación por pestañas.
  - `widgets/`: Paneles reutilizables (PsychologistPanel, UserManagementPanel, etc.).
  - `dialogs/`: Ventanas emergentes (Formularios de pacientes, citas, etc.).
- **`docs/`**: Documentación del sistema.

## 4. Base de Datos

### 4.1. Esquema Relacional

- **users**: Usuarios del sistema (rol, password hash).
- **patients**: Información clínica y personal. Relacionado con `users` (psychologist_id).
- **appointments**: Citas agendadas. Relacionado con `patients` y `users`.
- **expenses/incomes**: Registro financiero.

### 4.2. Configuración (`config.ini`)

El archivo `config.ini` debe estar junto al ejecutable. Parámetros clave:

```ini
[database]
db_type = mssql  ; o sqlite
mssql_host = LOCALHOST
mssql_port = 1433
mssql_database = clinic_db
mssql_user = sa
mssql_password = tu_password
mssql_driver = ODBC Driver 17 for SQL Server
```

## 5. Mantenimiento y Soporte (Rol SOPORTE)

### 5.1. Migración a SQL Server

El sistema incluye una herramienta integrada para migrar de SQLite a SQL Server.

1. Acceder con un usuario de rol **SOPORTE**.
2. Ir a la pestaña **⚙️ Base de Datos**.
3. Configurar las credenciales de SQL Server.
4. Usar el botón **"Migrar datos de SQLite a SQL Server"**.
   - Esto exportará los datos locales e importará en el servidor remoto.
   - Actualizará automáticamente el `config.ini`.

### 5.2. Logs y Auditoría

- **Logs de Aplicación**: Se guardan en la carpeta `logs/clinic_audit.log`. Útiles para depurar errores de conexión o fallos inesperados.
- **Auditoría de Acciones**: El sistema registra acciones críticas (login, crear usuario, eliminar paciente) en la base de datos, accesibles desde el panel de "Auditoría".

## 6. Compilación (.exe)

Para generar el ejecutable distribuible:

```bash
pyinstaller ClinicaPsicologica.spec
```

El archivo resultante estará en la carpeta `dist/`. Asegúrate de copiar la carpeta `assets` y crear un `config.ini` limpio junto al .exe.
