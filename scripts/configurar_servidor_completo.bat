@echo off
REM ========================================
REM Script de Configuracion Completa SQL Server
REM Ejecutar como ADMINISTRADOR en el SERVIDOR
REM ========================================

echo.
echo ========================================
echo   CONFIGURACION SQL SERVER - SERVIDOR
echo ========================================
echo.

REM Verificar si se esta ejecutando como administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Este script debe ejecutarse como ADMINISTRADOR
    echo.
    echo Haz clic derecho en el archivo y selecciona "Ejecutar como administrador"
    pause
    exit /b 1
)

echo [1/8] Verificando servicios SQL Server...
echo.

REM Iniciar SQL Server Browser
echo Iniciando SQL Server Browser...
net start SQLBrowser >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] SQL Server Browser iniciado
) else (
    echo [INFO] SQL Server Browser ya estaba corriendo o no se pudo iniciar
)

REM Configurar SQL Browser para inicio automatico
sc config SQLBrowser start=auto >nul 2>&1
echo [OK] SQL Browser configurado para inicio automatico
echo.

REM Iniciar SQL Server
echo [2/8] Verificando SQL Server (SQLEXPRESS)...
net start "MSSQL$SQLEXPRESS" >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] SQL Server iniciado
) else (
    echo [INFO] SQL Server ya estaba corriendo
)
echo.

REM Configurar reglas de firewall
echo [3/8] Configurando reglas de firewall...
echo.

REM Eliminar reglas existentes
netsh advfirewall firewall delete rule name="SQL Server" >nul 2>&1
netsh advfirewall firewall delete rule name="SQL Browser" >nul 2>&1

REM Agregar nuevas reglas
netsh advfirewall firewall add rule name="SQL Server" dir=in action=allow protocol=TCP localport=1433 >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Regla de firewall para SQL Server (puerto 1433) creada
) else (
    echo [ERROR] No se pudo crear la regla de firewall para SQL Server
)

netsh advfirewall firewall add rule name="SQL Browser" dir=in action=allow protocol=UDP localport=1434 >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Regla de firewall para SQL Browser (puerto 1434) creada
) else (
    echo [ERROR] No se pudo crear la regla de firewall para SQL Browser
)
echo.

REM Verificar puertos en escucha
echo [4/8] Verificando puertos en escucha...
echo.

powershell -Command "$port1433 = Get-NetTCPConnection -LocalPort 1433 -State Listen -ErrorAction SilentlyContinue; if ($port1433) { Write-Host '[OK] Puerto 1433 (SQL Server) esta en escucha' -ForegroundColor Green } else { Write-Host '[ERROR] Puerto 1433 NO esta en escucha' -ForegroundColor Red; Write-Host '        ACCION REQUERIDA: Configurar TCP/IP manualmente' -ForegroundColor Yellow }"

powershell -Command "$port1434 = Get-NetUDPEndpoint -LocalPort 1434 -ErrorAction SilentlyContinue; if ($port1434) { Write-Host '[OK] Puerto 1434 (SQL Browser) esta en escucha' -ForegroundColor Green } else { Write-Host '[AVISO] Puerto 1434 NO esta en escucha' -ForegroundColor Yellow }"
echo.

REM Obtener IP del servidor
echo [5/8] Obteniendo direccion IP del servidor...
echo.
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4" ^| findstr /V "127.0.0.1"') do (
    set IP=%%a
    set IP=!IP: =!
    echo [INFO] IP del servidor: !IP!
)
echo.

REM Crear script SQL para configurar autenticacion y usuario sa
echo [6/8] Creando script SQL de configuracion...
echo.

set SQL_SCRIPT=%TEMP%\config_sql_server.sql

echo -- Configuracion SQL Server > "%SQL_SCRIPT%"
echo USE master; >> "%SQL_SCRIPT%"
echo GO >> "%SQL_SCRIPT%"
echo. >> "%SQL_SCRIPT%"
echo -- Habilitar autenticacion mixta >> "%SQL_SCRIPT%"
echo EXEC xp_instance_regwrite N'HKEY_LOCAL_MACHINE', >> "%SQL_SCRIPT%"
echo     N'Software\Microsoft\MSSQLServer\MSSQLServer', >> "%SQL_SCRIPT%"
echo     N'LoginMode', REG_DWORD, 2; >> "%SQL_SCRIPT%"
echo GO >> "%SQL_SCRIPT%"
echo. >> "%SQL_SCRIPT%"
echo -- Habilitar el usuario sa >> "%SQL_SCRIPT%"
echo ALTER LOGIN sa ENABLE; >> "%SQL_SCRIPT%"
echo GO >> "%SQL_SCRIPT%"
echo. >> "%SQL_SCRIPT%"
echo -- Cambiar contraseña del usuario sa >> "%SQL_SCRIPT%"
echo ALTER LOGIN sa WITH PASSWORD = '270786'; >> "%SQL_SCRIPT%"
echo GO >> "%SQL_SCRIPT%"
echo. >> "%SQL_SCRIPT%"
echo -- Crear base de datos si no existe >> "%SQL_SCRIPT%"
echo IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'clinic_db') >> "%SQL_SCRIPT%"
echo BEGIN >> "%SQL_SCRIPT%"
echo     CREATE DATABASE clinic_db; >> "%SQL_SCRIPT%"
echo     PRINT 'Base de datos clinic_db creada'; >> "%SQL_SCRIPT%"
echo END >> "%SQL_SCRIPT%"
echo ELSE >> "%SQL_SCRIPT%"
echo BEGIN >> "%SQL_SCRIPT%"
echo     PRINT 'Base de datos clinic_db ya existe'; >> "%SQL_SCRIPT%"
echo END >> "%SQL_SCRIPT%"
echo GO >> "%SQL_SCRIPT%"
echo. >> "%SQL_SCRIPT%"
echo -- Verificar configuracion >> "%SQL_SCRIPT%"
echo SELECT SERVERPROPERTY('IsIntegratedSecurityOnly') as IsWindowsAuthOnly; >> "%SQL_SCRIPT%"
echo SELECT name, is_disabled FROM sys.server_principals WHERE name = 'sa'; >> "%SQL_SCRIPT%"
echo GO >> "%SQL_SCRIPT%"

echo [OK] Script SQL creado en: %SQL_SCRIPT%
echo.

REM Ejecutar script SQL
echo [7/8] Ejecutando configuracion SQL Server...
echo.
echo Intentando ejecutar script SQL...

sqlcmd -S localhost\SQLEXPRESS -E -C -i "%SQL_SCRIPT%" -o "%TEMP%\sql_output.txt" 2>&1

if %errorLevel% equ 0 (
    echo [OK] Script SQL ejecutado exitosamente
    echo.
    echo Resultado:
    type "%TEMP%\sql_output.txt"
) else (
    echo [ERROR] No se pudo ejecutar el script SQL automaticamente
    echo.
    echo ACCION REQUERIDA: Ejecuta manualmente en SQL Server Management Studio:
    echo.
    type "%SQL_SCRIPT%"
    echo.
    echo O ejecuta:
    echo sqlcmd -S localhost\SQLEXPRESS -E -C -i "%SQL_SCRIPT%"
)
echo.

REM Reiniciar SQL Server para aplicar cambios
echo [8/8] Reiniciando SQL Server para aplicar cambios...
echo.

net stop "MSSQL$SQLEXPRESS" >nul 2>&1
timeout /t 2 /nobreak >nul
net start "MSSQL$SQLEXPRESS" >nul 2>&1

if %errorLevel% equ 0 (
    echo [OK] SQL Server reiniciado exitosamente
) else (
    echo [ERROR] No se pudo reiniciar SQL Server
    echo        Reinicia manualmente: Restart-Service 'MSSQL$SQLEXPRESS'
)
echo.

REM Esperar a que SQL Server este listo
echo Esperando a que SQL Server este listo...
timeout /t 5 /nobreak >nul
echo.

REM Probar conexion
echo ========================================
echo   PROBANDO CONEXION
echo ========================================
echo.

echo Probando conexion con usuario sa...
sqlcmd -S localhost\SQLEXPRESS -U sa -P 270786 -C -Q "SELECT @@VERSION" -o "%TEMP%\test_connection.txt" 2>&1

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo   [EXITO] CONFIGURACION COMPLETADA
    echo ========================================
    echo.
    echo [OK] SQL Server esta configurado correctamente
    echo [OK] Usuario 'sa' habilitado con contraseña: 270786
    echo [OK] Autenticacion mixta habilitada
    echo [OK] Firewall configurado
    echo.
    echo CONFIGURACION PARA CLIENTES:
    echo.
    echo [database]
    echo db_type = mssql
    for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4" ^| findstr /V "127.0.0.1"') do (
        set IP=%%a
        set IP=!IP: =!
        echo mssql_host = !IP!
    )
    echo mssql_port = 1433
    echo mssql_database = clinic_db
    echo mssql_user = sa
    echo mssql_password = 270786
    echo mssql_driver = ODBC Driver 17 for SQL Server
    echo mssql_trusted = false
    echo.
) else (
    echo.
    echo ========================================
    echo   [AVISO] CONFIGURACION PARCIAL
    echo ========================================
    echo.
    echo Algunas configuraciones se aplicaron, pero la conexion con 'sa' fallo.
    echo.
    echo PASOS MANUALES REQUERIDOS:
    echo.
    echo 1. Abre SQL Server Management Studio (SSMS)
    echo 2. Conectate con Windows Authentication
    echo 3. Ejecuta este script SQL:
    echo.
    type "%SQL_SCRIPT%"
    echo.
    echo 4. Reinicia el servicio SQL Server
    echo.
)

echo.
echo ========================================
echo   INFORMACION DEL SISTEMA
echo ========================================
echo.

echo Nombre del equipo: %COMPUTERNAME%
echo.

echo Direcciones IP:
ipconfig | findstr /C:"IPv4"
echo.

echo Estado de servicios SQL:
sc query "MSSQL$SQLEXPRESS" | findstr "STATE"
sc query "SQLBrowser" | findstr "STATE"
echo.

echo Puertos en escucha:
netstat -an | findstr ":1433"
netstat -an | findstr ":1434"
echo.

echo ========================================
echo.
echo Script completado. Presiona cualquier tecla para salir...
pause >nul
