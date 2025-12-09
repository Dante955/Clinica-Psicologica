# Script para configurar SQL Server en el SERVIDOR
# Ejecutar como Administrador en la PC servidor (192.168.0.9)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CONFIGURACION SQL SERVER - SERVIDOR" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Iniciar SQL Browser
Write-Host "1. Iniciando SQL Server Browser..." -ForegroundColor Yellow
try {
    Start-Service SQLBrowser -ErrorAction Stop
    Set-Service SQLBrowser -StartupType Automatic
    Write-Host "   [OK] SQL Browser iniciado" -ForegroundColor Green
} catch {
    Write-Host "   [ERROR] No se pudo iniciar SQL Browser: $_" -ForegroundColor Red
}
Write-Host ""

# 2. Verificar servicio SQL Server
Write-Host "2. Verificando SQL Server..." -ForegroundColor Yellow
$sqlService = Get-Service -Name "MSSQL`$SQLEXPRESS" -ErrorAction SilentlyContinue
if ($sqlService -and $sqlService.Status -eq "Running") {
    Write-Host "   [OK] SQL Server esta corriendo" -ForegroundColor Green
} else {
    Write-Host "   [ERROR] SQL Server no esta corriendo" -ForegroundColor Red
    Write-Host "   Intentando iniciar..." -ForegroundColor Yellow
    Start-Service "MSSQL`$SQLEXPRESS"
}
Write-Host ""

# 3. Configurar Firewall
Write-Host "3. Configurando reglas de firewall..." -ForegroundColor Yellow

# Eliminar reglas existentes si existen
netsh advfirewall firewall delete rule name="SQL Server" 2>$null
netsh advfirewall firewall delete rule name="SQL Browser" 2>$null

# Agregar nuevas reglas
$result1 = netsh advfirewall firewall add rule name="SQL Server" dir=in action=allow protocol=TCP localport=1433
$result2 = netsh advfirewall firewall add rule name="SQL Browser" dir=in action=allow protocol=UDP localport=1434

if ($LASTEXITCODE -eq 0) {
    Write-Host "   [OK] Reglas de firewall configuradas" -ForegroundColor Green
} else {
    Write-Host "   [ERROR] No se pudieron configurar las reglas de firewall" -ForegroundColor Red
}
Write-Host ""

# 4. Verificar puertos
Write-Host "4. Verificando puertos en escucha..." -ForegroundColor Yellow
$port1433 = Get-NetTCPConnection -LocalPort 1433 -State Listen -ErrorAction SilentlyContinue
$port1434 = Get-NetUDPEndpoint -LocalPort 1434 -ErrorAction SilentlyContinue

if ($port1433) {
    Write-Host "   [OK] Puerto 1433 en escucha" -ForegroundColor Green
} else {
    Write-Host "   [ERROR] Puerto 1433 NO esta en escucha" -ForegroundColor Red
    Write-Host "   ACCION REQUERIDA: Configura TCP/IP en SQL Server Configuration Manager" -ForegroundColor Yellow
}

if ($port1434) {
    Write-Host "   [OK] Puerto 1434 en escucha" -ForegroundColor Green
} else {
    Write-Host "   [AVISO] Puerto 1434 NO esta en escucha (SQL Browser)" -ForegroundColor Yellow
}
Write-Host ""

# 5. Mostrar IP
Write-Host "5. Direccion IP del servidor:" -ForegroundColor Yellow
$ip = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*"} | Select-Object -First 1
Write-Host "   IP: $($ip.IPAddress)" -ForegroundColor Cyan
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PASOS MANUALES REQUERIDOS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANTE: Debes hacer estos pasos manualmente:" -ForegroundColor Yellow
Write-Host ""
Write-Host "A. Configurar TCP/IP en SQL Server Configuration Manager:" -ForegroundColor White
Write-Host "   1. Abre 'SQL Server Configuration Manager'" -ForegroundColor Gray
Write-Host "   2. Ve a: SQL Server Network Configuration -> Protocols for SQLEXPRESS" -ForegroundColor Gray
Write-Host "   3. Haz clic derecho en TCP/IP -> Properties" -ForegroundColor Gray
Write-Host "   4. En la pestana IP Addresses, seccion IPAll:" -ForegroundColor Gray
Write-Host "      - TCP Dynamic Ports: (VACIO)" -ForegroundColor Gray
Write-Host "      - TCP Port: 1433" -ForegroundColor Gray
Write-Host "   5. Reinicia el servicio: Restart-Service 'MSSQL`$SQLEXPRESS'" -ForegroundColor Gray
Write-Host ""
Write-Host "B. Habilitar autenticacion mixta en SQL Server:" -ForegroundColor White
Write-Host "   1. Abre SQL Server Management Studio (SSMS)" -ForegroundColor Gray
Write-Host "   2. Conectate al servidor localmente" -ForegroundColor Gray
Write-Host "   3. Clic derecho en servidor -> Properties -> Security" -ForegroundColor Gray
Write-Host "   4. Selecciona 'SQL Server and Windows Authentication mode'" -ForegroundColor Gray
Write-Host "   5. Reinicia el servicio SQL Server" -ForegroundColor Gray
Write-Host ""
Write-Host "C. Habilitar usuario 'sa' (en SSMS):" -ForegroundColor White
Write-Host "   Ejecuta este SQL:" -ForegroundColor Gray
Write-Host "   ALTER LOGIN sa ENABLE;" -ForegroundColor Cyan
Write-Host "   ALTER LOGIN sa WITH PASSWORD = 'TuContraseñaSegura123!';" -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
