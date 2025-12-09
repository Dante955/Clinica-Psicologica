# Script de Diagnostico SQL Server
# Este script verifica todos los aspectos de la configuracion de SQL Server

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DIAGNOSTICO SQL SERVER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar servicios SQL
Write-Host "1. VERIFICANDO SERVICIOS SQL..." -ForegroundColor Yellow
$sqlServices = Get-Service | Where-Object {$_.Name -like "*SQL*"}
foreach ($service in $sqlServices) {
    $status = if ($service.Status -eq "Running") { "[OK]" } else { "[ERROR]" }
    $color = if ($service.Status -eq "Running") { "Green" } else { "Red" }
    Write-Host "   $status $($service.DisplayName): $($service.Status) - $($service.StartType)" -ForegroundColor $color
}
Write-Host ""

# 2. Verificar SQL Browser especificamente
Write-Host "2. VERIFICANDO SQL BROWSER..." -ForegroundColor Yellow
$browser = Get-Service -Name "SQLBrowser" -ErrorAction SilentlyContinue
if ($browser) {
    if ($browser.Status -eq "Running") {
        Write-Host "   [OK] SQL Browser esta corriendo" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] SQL Browser NO esta corriendo" -ForegroundColor Red
        Write-Host "   SOLUCION: Start-Service SQLBrowser" -ForegroundColor Yellow
    }
    if ($browser.StartType -ne "Automatic") {
        Write-Host "   [AVISO] SQL Browser no esta configurado para inicio automatico" -ForegroundColor Yellow
        Write-Host "   SOLUCION: Set-Service SQLBrowser -StartupType Automatic" -ForegroundColor Yellow
    }
} else {
    Write-Host "   [ERROR] SQL Browser no esta instalado" -ForegroundColor Red
}
Write-Host ""

# 3. Verificar reglas de firewall
Write-Host "3. VERIFICANDO REGLAS DE FIREWALL..." -ForegroundColor Yellow
try {
    $fwRule1433 = Get-NetFirewallRule -DisplayName "SQL Server" -ErrorAction SilentlyContinue
    $fwRule1434 = Get-NetFirewallRule -DisplayName "SQL Browser" -ErrorAction SilentlyContinue
    
    if ($fwRule1433) {
        Write-Host "   [OK] Regla de firewall para SQL Server (1433) encontrada" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] Regla de firewall para SQL Server (1433) NO encontrada" -ForegroundColor Red
    }
    
    if ($fwRule1434) {
        Write-Host "   [OK] Regla de firewall para SQL Browser (1434) encontrada" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] Regla de firewall para SQL Browser (1434) NO encontrada" -ForegroundColor Red
    }
} catch {
    Write-Host "   [AVISO] No se pudo verificar reglas de firewall" -ForegroundColor Yellow
}
Write-Host ""

# 4. Verificar puertos en escucha
Write-Host "4. VERIFICANDO PUERTOS EN ESCUCHA..." -ForegroundColor Yellow
$port1433 = Get-NetTCPConnection -LocalPort 1433 -State Listen -ErrorAction SilentlyContinue
$port1434 = Get-NetUDPEndpoint -LocalPort 1434 -ErrorAction SilentlyContinue

if ($port1433) {
    Write-Host "   [OK] Puerto 1433 (SQL Server) esta en escucha" -ForegroundColor Green
    Write-Host "       Proceso: $($port1433.OwningProcess)" -ForegroundColor Gray
} else {
    Write-Host "   [ERROR] Puerto 1433 NO esta en escucha" -ForegroundColor Red
    Write-Host "   PROBLEMA CRITICO: SQL Server no esta escuchando en el puerto 1433" -ForegroundColor Red
    Write-Host "   SOLUCION: Verifica la configuracion de TCP/IP en SQL Server Configuration Manager" -ForegroundColor Yellow
}

if ($port1434) {
    Write-Host "   [OK] Puerto 1434 (SQL Browser) esta en escucha" -ForegroundColor Green
} else {
    Write-Host "   [ERROR] Puerto 1434 NO esta en escucha" -ForegroundColor Red
    Write-Host "   SOLUCION: Inicia el servicio SQL Browser" -ForegroundColor Yellow
}
Write-Host ""

# 5. Obtener IP del servidor
Write-Host "5. DIRECCION IP DEL SERVIDOR..." -ForegroundColor Yellow
$ipAddresses = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*"}
foreach ($ip in $ipAddresses) {
    Write-Host "   IP: $($ip.IPAddress) - $($ip.InterfaceAlias)" -ForegroundColor Cyan
}
Write-Host ""

# 6. Verificar conectividad local
Write-Host "6. PROBANDO CONECTIVIDAD LOCAL..." -ForegroundColor Yellow
$testLocal1433 = Test-NetConnection -ComputerName localhost -Port 1433 -WarningAction SilentlyContinue -InformationLevel Quiet
if ($testLocal1433) {
    Write-Host "   [OK] Puerto 1433 accesible localmente" -ForegroundColor Green
} else {
    Write-Host "   [ERROR] Puerto 1433 NO accesible localmente" -ForegroundColor Red
}
Write-Host ""

# 7. Resumen y recomendaciones
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RESUMEN Y PROXIMOS PASOS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$issues = @()

if (-not $browser -or $browser.Status -ne "Running") {
    $issues += "SQL Browser no esta corriendo"
}

if (-not $port1433) {
    $issues += "Puerto 1433 no esta en escucha - PROBLEMA PRINCIPAL"
}

if (-not $port1434) {
    $issues += "Puerto 1434 no esta en escucha"
}

if ($issues.Count -eq 0) {
    Write-Host "[OK] CONFIGURACION CORRECTA EN EL SERVIDOR" -ForegroundColor Green
    Write-Host ""
    Write-Host "Si aun tienes problemas de conexion desde clientes, verifica:" -ForegroundColor Yellow
    Write-Host "1. Modo de autenticacion SQL Server (debe ser mixto)" -ForegroundColor White
    Write-Host "2. Usuario 'sa' debe estar habilitado" -ForegroundColor White
    Write-Host "3. Contrasena correcta en config.ini del cliente" -ForegroundColor White
    Write-Host "4. Firewall del cliente permite conexiones salientes" -ForegroundColor White
} else {
    Write-Host "[ERROR] PROBLEMAS ENCONTRADOS:" -ForegroundColor Red
    Write-Host ""
    foreach ($issue in $issues) {
        Write-Host "   - $issue" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "SOLUCIONES PASO A PASO:" -ForegroundColor Yellow
    Write-Host ""
    
    if (-not $port1433) {
        Write-Host "PROBLEMA PRINCIPAL: Puerto 1433 no esta en escucha" -ForegroundColor Red
        Write-Host ""
        Write-Host "SOLUCION - Configurar TCP/IP:" -ForegroundColor Yellow
        Write-Host "1. Abre 'SQL Server Configuration Manager'" -ForegroundColor White
        Write-Host "2. Ve a: SQL Server Network Configuration -> Protocols for SQLEXPRESS" -ForegroundColor White
        Write-Host "3. Haz clic derecho en TCP/IP -> Properties" -ForegroundColor White
        Write-Host "4. En la pestana IP Addresses, ve hasta el final a la seccion IPAll:" -ForegroundColor White
        Write-Host "   - TCP Dynamic Ports: (debe estar VACIO - borra cualquier valor)" -ForegroundColor White
        Write-Host "   - TCP Port: 1433" -ForegroundColor White
        Write-Host "5. Haz clic en OK" -ForegroundColor White
        Write-Host "6. Reinicia el servicio SQL Server con:" -ForegroundColor White
        Write-Host "   Restart-Service 'MSSQL`$SQLEXPRESS'" -ForegroundColor Cyan
        Write-Host ""
    }
    
    if (-not $browser -or $browser.Status -ne "Running") {
        Write-Host "Iniciar SQL Browser:" -ForegroundColor Yellow
        Write-Host "   Start-Service SQLBrowser" -ForegroundColor Cyan
        Write-Host "   Set-Service SQLBrowser -StartupType Automatic" -ForegroundColor Cyan
        Write-Host ""
    }
    
    Write-Host "Agregar reglas de firewall (ejecuta como Administrador):" -ForegroundColor Yellow
    Write-Host '   netsh advfirewall firewall add rule name="SQL Server" dir=in action=allow protocol=TCP localport=1433' -ForegroundColor Cyan
    Write-Host '   netsh advfirewall firewall add rule name="SQL Browser" dir=in action=allow protocol=UDP localport=1434' -ForegroundColor Cyan
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
