# Configuración de SQL Server para Inicio Automático

## Tu IP del Servidor: **192.168.0.9**

## Configuración Realizada

### ✅ Servicios Configurados para Inicio Automático

Los siguientes servicios se han configurado para iniciar automáticamente con Windows:

1. **SQL Server (SQLEXPRESS)** - Motor de base de datos
2. **SQL Server Browser** - Permite que los clientes encuentren el servidor en la red

### 🚀 Optimizaciones Aplicadas

- **Inicio Automático**: Los servicios inician cuando Windows arranca
- **Inicio Diferido**: Para no ralentizar el arranque de Windows
- **Prioridad Normal**: Balance entre rendimiento y recursos del sistema

## Configuración para PCs Clientes

En cada PC cliente, crea o edita el archivo `config.ini`:

```ini
[database]
db_type = mssql
mssql_host = 192.168.0.9
mssql_port = 1433
mssql_database = clinic_db
mssql_driver = ODBC Driver 17 for SQL Server
mssql_trusted = false
mssql_user = sa
mssql_password = tu_contraseña_aqui
```

## Pasos Adicionales Requeridos

### 1. Habilitar TCP/IP (IMPORTANTE)

Debes hacer esto manualmente:

1. Abre **SQL Server Configuration Manager**
2. Ve a: **SQL Server Network Configuration** → **Protocols for SQLEXPRESS**
3. Haz clic derecho en **TCP/IP** → **Enable**
4. Reinicia el servicio SQL Server

### 2. Configurar Firewall

Ejecuta como Administrador:

```batch
scripts\habilitar_conexiones_remotas.bat
```

O manualmente:

```powershell
# Permitir SQL Server (puerto 1433)
netsh advfirewall firewall add rule name="SQL Server" dir=in action=allow protocol=TCP localport=1433

# Permitir SQL Browser (puerto 1434)
netsh advfirewall firewall add rule name="SQL Browser" dir=in action=allow protocol=UDP localport=1434
```

### 3. Eliminar Columna Salary

Ejecuta el script SQL:

```sql
-- En SQL Server Management Studio
USE clinic_db;
GO

ALTER TABLE dbo.users DROP COLUMN salary;
GO
```

## Verificar Configuración

Para verificar que todo está configurado correctamente:

```powershell
# Ver estado de servicios SQL
Get-Service | Where-Object {$_.Name -like "*SQL*"} | Select-Object Name, Status, StartType

# Probar conectividad desde cliente
Test-NetConnection -ComputerName 192.168.0.9 -Port 1433
```

## Solución de Problemas - Error de Timeout

> **📖 GUÍA COMPLETA:** Ver [SOLUCION_TIMEOUT_SQL.md](SOLUCION_TIMEOUT_SQL.md) para instrucciones paso a paso detalladas.

### ❌ Error: "TCP Provider: Tiempo de espera de la operación de espera agotado"

Este error indica que el cliente no puede conectarse al servidor. Sigue estos pasos:

#### ⚡ Solución Rápida (Más Común)

**El problema más común es usar Windows Authentication en vez de SQL Authentication.**

En la PC cliente, verifica que `config.ini` tenga:

```ini
[database]
db_type = mssql
mssql_host = 192.168.0.9          # Usa la IP, NO el nombre del servidor
mssql_port = 1433                  # Especifica el puerto
mssql_database = clinic_db
mssql_user = sa                    # Usuario SQL Server
mssql_password = TuContraseña      # Contraseña del usuario sa
mssql_driver = ODBC Driver 17 for SQL Server
mssql_trusted = false              # IMPORTANTE: false para SQL Auth
```

**En el servidor, asegúrate de:**

1. Habilitar autenticación mixta (SQL Server + Windows)
2. Habilitar el usuario 'sa'
3. Configurar TCP/IP en puerto 1433 (ver pasos detallados abajo)

#### 1. ✅ Verificar que SQL Server esté ejecutándose

```powershell
Get-Service | Where-Object {$_.Name -like "*SQL*"} | Select-Object Name, Status, StartType
```

Ambos servicios deben estar en estado "Running":

- `MSSQL$SQLEXPRESS` o `MSSQLSERVER`
- `SQLBrowser`

#### 2. ✅ Verificar que TCP/IP esté habilitado Y configurado correctamente

**IMPORTANTE**: No solo habilitar TCP/IP, también verificar el puerto:

1. Abre **SQL Server Configuration Manager**
2. Ve a: **SQL Server Network Configuration** → **Protocols for SQLEXPRESS**
3. Haz clic derecho en **TCP/IP** → **Properties**
4. En la pestaña **IP Addresses**:
   - Busca la sección **IPAll** (al final)
   - **TCP Dynamic Ports**: debe estar **VACÍO** (borra cualquier valor)
   - **TCP Port**: debe ser **1433**
5. Haz clic en **OK** y **reinicia el servicio SQL Server**

#### 3. ✅ Verificar SQL Server Browser

El servicio SQL Browser es **CRÍTICO** para instancias nombradas como SQLEXPRESS:

```powershell
# Verificar estado
Get-Service SQLBrowser

# Si no está corriendo, iniciarlo
Start-Service SQLBrowser
Set-Service SQLBrowser -StartupType Automatic
```

#### 4. ✅ Verificar Firewall de Windows

Ejecuta estos comandos como **Administrador**:

```powershell
# Ver reglas existentes
netsh advfirewall firewall show rule name=all | Select-String -Pattern "SQL"

# Agregar reglas si no existen
netsh advfirewall firewall add rule name="SQL Server" dir=in action=allow protocol=TCP localport=1433
netsh advfirewall firewall add rule name="SQL Browser" dir=in action=allow protocol=UDP localport=1434
```

#### 5. ✅ Verificar Modo de Autenticación de SQL Server

SQL Server debe permitir autenticación mixta (Windows + SQL):

1. Abre **SQL Server Management Studio (SSMS)**
2. Conéctate al servidor localmente
3. Haz clic derecho en el servidor → **Properties**
4. Ve a **Security**
5. Selecciona **SQL Server and Windows Authentication mode**
6. Haz clic en **OK** y **reinicia el servicio**

#### 6. ✅ Verificar que el usuario 'sa' esté habilitado

```sql
-- En SQL Server Management Studio
USE master;
GO

-- Habilitar el usuario sa
ALTER LOGIN sa ENABLE;
GO

-- Cambiar contraseña si es necesario
ALTER LOGIN sa WITH PASSWORD = 'TuContraseñaSegura123!';
GO
```

#### 7. ✅ Probar conectividad de red

Desde la PC cliente, ejecuta:

```powershell
# Verificar que puedes hacer ping al servidor
ping 192.168.0.9

# Verificar que el puerto 1433 está abierto
Test-NetConnection -ComputerName 192.168.0.9 -Port 1433

# Verificar que el puerto 1434 (SQL Browser) está abierto
Test-NetConnection -ComputerName 192.168.0.9 -Port 1434
```

**Resultado esperado**:

- `TcpTestSucceeded : True` para el puerto 1433
- `TcpTestSucceeded : True` para el puerto 1434

#### 8. ✅ Verificar configuración del cliente

En la PC cliente, verifica el archivo `config.ini`:

```ini
[database]
db_type = mssql
mssql_host = 192.168.0.9
mssql_port = 1433
mssql_database = clinic_db
mssql_driver = ODBC Driver 17 for SQL Server
mssql_trusted = false
mssql_user = sa
mssql_password = TuContraseñaAqui
```

#### 9. ✅ Probar con diferentes formatos de conexión

Si nada funciona, prueba estos formatos alternativos en `config.ini`:

**Opción A - Con instancia nombrada:**

```ini
mssql_host = 192.168.0.9\SQLEXPRESS
mssql_port =
```

**Opción B - Solo IP y puerto:**

```ini
mssql_host = 192.168.0.9
mssql_port = 1433
```

**Opción C - Con nombre del servidor:**

```ini
mssql_host = NOMBRE-PC\SQLEXPRESS
mssql_port =
```

### 🔍 Script de Diagnóstico

Ejecuta el script `scripts\diagnostico_sql.ps1` para verificar automáticamente todos estos puntos.
