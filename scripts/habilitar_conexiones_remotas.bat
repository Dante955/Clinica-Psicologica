@echo off
REM Script para habilitar conexiones remotas a SQL Server
REM Ejecutar como Administrador

echo ============================================
echo Habilitando conexiones remotas a SQL Server
echo ============================================
echo.

REM Habilitar regla de firewall para SQL Server (puerto 1433)
echo Configurando Firewall para SQL Server (puerto 1433)...
netsh advfirewall firewall add rule name="SQL Server" dir=in action=allow protocol=TCP localport=1433
if %errorlevel% equ 0 (
    echo ✓ Regla de firewall para SQL Server creada
) else (
    echo ✗ Error al crear regla de firewall
)

echo.

REM Habilitar regla de firewall para SQL Browser (puerto 1434 UDP)
echo Configurando Firewall para SQL Browser (puerto 1434)...
netsh advfirewall firewall add rule name="SQL Browser" dir=in action=allow protocol=UDP localport=1434
if %errorlevel% equ 0 (
    echo ✓ Regla de firewall para SQL Browser creada
) else (
    echo ✗ Error al crear regla de firewall
)

echo.
echo ============================================
echo IMPORTANTE: Configuración Manual Requerida
echo ============================================
echo.
echo Debes completar estos pasos manualmente:
echo.
echo 1. Abrir "SQL Server Configuration Manager"
echo 2. Ir a: SQL Server Network Configuration
echo 3. Seleccionar: Protocols for SQLEXPRESS
echo 4. Hacer clic derecho en "TCP/IP" y seleccionar "Enable"
echo 5. Reiniciar el servicio SQL Server
echo.
echo ============================================
echo Tu IP del servidor es: 192.168.0.9
echo ============================================
echo.
echo En las PCs clientes, usa este config.ini:
echo.
echo [database]
echo db_type = mssql
echo mssql_host = 192.168.0.9
echo mssql_port = 1433
echo mssql_database = clinic_db
echo mssql_driver = ODBC Driver 17 for SQL Server
echo mssql_trusted = false
echo mssql_user = tu_usuario
echo mssql_password = tu_contraseña
echo.
pause
