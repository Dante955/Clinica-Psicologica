# Guía Rápida: Solución al Error de Timeout SQL Server

## 🎯 Problema Identificado

- ✅ Puerto 1433 (SQL Server): **ACCESIBLE**
- ❌ Puerto 1434 (SQL Browser): **NO ACCESIBLE** (no es crítico)
- ❌ Configuración del cliente: Usando Windows Auth en vez de SQL Auth

## 📋 Solución en 3 Pasos

### PASO 1: En el SERVIDOR (192.168.0.9)

#### A. Verificar que SQL Server esté escuchando en puerto 1433

1. Abre **SQL Server Configuration Manager**
2. Ve a: `SQL Server Network Configuration` → `Protocols for SQLEXPRESS`
3. Haz clic derecho en **TCP/IP** → **Properties**
4. Ve a la pestaña **IP Addresses**
5. Desplázate hasta el final a la sección **IPAll**:
   - **TCP Dynamic Ports**: debe estar **VACÍO** (borra cualquier valor)
   - **TCP Port**: debe ser **1433**
6. Haz clic en **OK**
7. **Reinicia el servicio SQL Server**:
   ```powershell
   Restart-Service 'MSSQL$SQLEXPRESS'
   ```

#### B. Habilitar Autenticación Mixta

1. Abre **SQL Server Management Studio (SSMS)**
2. Conéctate al servidor localmente (usa Windows Authentication)
3. Haz clic derecho en el servidor → **Properties**
4. Ve a **Security**
5. Selecciona **SQL Server and Windows Authentication mode**
6. Haz clic en **OK**
7. **Reinicia el servicio SQL Server**

#### C. Habilitar y configurar el usuario 'sa'

En SSMS, ejecuta este SQL:

```sql
USE master;
GO

-- Habilitar el usuario sa
ALTER LOGIN sa ENABLE;
GO

-- Cambiar contraseña (usa una contraseña segura)
ALTER LOGIN sa WITH PASSWORD = 'TuContraseñaSegura123!';
GO
```

**IMPORTANTE:** Anota la contraseña que uses, la necesitarás en el cliente.

#### D. Configurar Firewall (opcional, ejecutar como Administrador)

```powershell
netsh advfirewall firewall add rule name="SQL Server" dir=in action=allow protocol=TCP localport=1433
netsh advfirewall firewall add rule name="SQL Browser" dir=in action=allow protocol=UDP localport=1434
```

O ejecuta el script:

```powershell
.\scripts\configurar_servidor_sql.ps1
```

---

### PASO 2: En el CLIENTE (192.168.0.15)

#### Editar el archivo `config.ini`

Abre `c:\Users\Admin\Trabajo\config.ini` y asegúrate de que la sección `[database]` tenga:

```ini
[database]
db_type = mssql
mssql_host = 192.168.0.9
mssql_port = 1433
mssql_database = clinic_db
mssql_user = sa
mssql_password = TuContraseñaSegura123!
mssql_driver = ODBC Driver 17 for SQL Server
mssql_trusted = false
```

**IMPORTANTE:**

- Usa la **IP** (192.168.0.9), NO el nombre del servidor
- Usa **SQL Authentication** (`mssql_trusted = false`)
- Pon la **misma contraseña** que configuraste para 'sa' en el servidor

---

### PASO 3: Probar la Conexión

En el cliente, ejecuta el script de prueba:

```powershell
python scripts\test_conexion_sql.py
```

O usa el verificador de conexión:

```powershell
python verificar_conexion.py
```

---

## 🔍 Diagnóstico de Errores Comunes

### Error: "Login timeout expired"

- **Causa:** El servidor no responde
- **Solución:** Verifica que TCP/IP esté configurado correctamente en el servidor

### Error: "Login failed for user 'sa'"

- **Causa:** Credenciales incorrectas o usuario deshabilitado
- **Solución:**
  1. Verifica que la autenticación mixta esté habilitada
  2. Verifica que el usuario 'sa' esté habilitado
  3. Verifica que la contraseña sea correcta

### Error: "Cannot open database 'clinic_db'"

- **Causa:** La base de datos no existe
- **Solución:** Crea la base de datos o usa 'master' temporalmente

---

## ✅ Verificación Final

Desde el cliente, ejecuta:

```powershell
# Verificar conectividad de red
Test-NetConnection -ComputerName 192.168.0.9 -Port 1433

# Debe mostrar: TcpTestSucceeded : True
```

Si `TcpTestSucceeded : True`, entonces el problema es de autenticación, no de red.

---

## 📝 Notas Importantes

1. **No necesitas SQL Browser** si te conectas directamente con IP:Puerto
2. **Windows Authentication no funciona** entre PCs diferentes en la mayoría de los casos
3. **Usa SQL Authentication** (usuario 'sa') para conexiones remotas
4. **Anota la contraseña** del usuario 'sa' de forma segura

---

## 🆘 Si Nada Funciona

1. Verifica que ambas PCs estén en la misma red (192.168.0.x)
2. Desactiva temporalmente el firewall del servidor para probar
3. Usa 'master' en vez de 'clinic_db' para probar la conexión
4. Verifica los logs de SQL Server en el servidor
