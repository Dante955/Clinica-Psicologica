@echo off
REM Script para configurar SQL Server para inicio automático
REM Ejecutar como Administrador

echo ============================================
echo Configurando SQL Server para inicio automático
echo ============================================
echo.

REM Configurar servicio SQL Server para inicio automático
echo Configurando servicio SQL Server (SQLEXPRESS)...
sc config "MSSQL$SQLEXPRESS" start= auto
if %errorlevel% equ 0 (
    echo ✓ SQL Server configurado para inicio automático
) else (
    echo ✗ Error al configurar SQL Server
)

echo.

REM Configurar SQL Server Browser para inicio automático
echo Configurando SQL Server Browser...
sc config "SQLBrowser" start= auto
if %errorlevel% equ 0 (
    echo ✓ SQL Server Browser configurado para inicio automático
) else (
    echo ✗ Error al configurar SQL Server Browser
)

echo.

REM Iniciar los servicios ahora
echo Iniciando servicios...
net start "MSSQL$SQLEXPRESS"
net start "SQLBrowser"

echo.
echo ============================================
echo Configuración completada
echo ============================================
echo.
echo Tu IP del servidor es: 192.168.0.9
echo.
echo Usa esta IP en el config.ini de las PCs clientes:
echo   mssql_host = 192.168.0.9
echo.
pause
