# Guía de Configuración Multi-Usuario

Esta guía te ayudará a configurar la aplicación para que 2-3 computadoras puedan trabajar simultáneamente.

## 📋 Requisitos Previos

- Todas las computadoras deben estar en la misma red local (WiFi o cable)
- Una computadora actuará como "servidor" (donde estará la base de datos)
- Las demás computadoras serán "clientes"

---

## 🖥️ Paso 1: Configurar la Computadora Servidor

### 1.1 Crear Carpeta Compartida

1. En la computadora que será el servidor, crea una carpeta:

   ```
   C:\ClinicaCompartida
   ```

2. Copia estos archivos a la carpeta compartida:
   - `clinic.db` (la base de datos)
   - `config.ini`
   - Carpeta `backups\` (opcional pero recomendado)

### 1.2 Compartir la Carpeta en Red

**En Windows:**

1. Click derecho en la carpeta `C:\ClinicaCompartida`
2. Selecciona **"Propiedades"**
3. Ve a la pestaña **"Compartir"**
4. Click en **"Compartir..."**
5. Agrega los usuarios que tendrán acceso (o selecciona "Todos")
6. Establece permisos de **"Lectura y escritura"**
7. Click en **"Compartir"** y luego **"Listo"**
8. **Anota la ruta de red** que aparece, por ejemplo:
   ```
   \\NOMBRE-PC\ClinicaCompartida
   ```

### 1.3 Obtener la IP del Servidor

1. Abre **CMD** (Símbolo del sistema)
2. Escribe: `ipconfig`
3. Busca **"Dirección IPv4"**, por ejemplo: `192.168.1.100`
4. **Anota esta IP** - la necesitarás para los clientes

---

## 💻 Paso 2: Configurar las Computadoras Cliente

### 2.1 Mapear la Unidad de Red

En cada computadora cliente:

1. Abre **"Este equipo"** o **"Mi PC"**
2. Click en **"Mapear unidad de red"** (en la cinta superior)
3. Selecciona una letra de unidad (por ejemplo: **Z:**)
4. En "Carpeta", escribe la ruta del servidor:
   ```
   \\ 192.168.56.1\ClinicaCompartida
   ```
   O usa el nombre del PC:
   ``` 
   //DESKTOP-GVBVF8K/ClinicaCompartida

   ```
5. Marca ✅ **"Volver a conectar al iniciar sesión"**
6. Marca ✅ **"Conectarse con credenciales diferentes"** (si es necesario)
7. Click en **"Finalizar"**

### 2.2 Instalar la Aplicación en Cada Cliente

1. Copia la aplicación completa a cada computadora cliente:

   ```
   C:\Users\Admin\Trabajo
   ```

2. Instala las dependencias en cada cliente:
   ```bash
   pip install -r requirements.txt
   ```

### 2.3 Configurar la Ruta de la Base de Datos

En cada computadora cliente, edita el archivo `database_manager.py`:

**Ubicación:** `C:\Users\Admin\Trabajo\database\database_manager.py`

Busca la línea que dice:

```python
return "sqlite:///clinic.db"
```

Cámbiala por la ruta de red:

```python
return "sqlite:///Z:/clinic.db"
```

(Usa la letra de unidad que mapeaste en el paso 2.1)

---

## ⚙️ Paso 3: Configuración Adicional para SQLite Multi-Usuario

SQLite tiene limitaciones para acceso concurrente. Necesitamos optimizarlo:

### 3.1 Habilitar WAL Mode (Write-Ahead Logging)

Esto permite que múltiples usuarios lean mientras uno escribe.

Ejecuta este script **UNA SOLA VEZ** desde la computadora servidor:

```python
import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('Z:/clinic.db')  # Usa tu ruta de red

# Habilitar WAL mode
conn.execute('PRAGMA journal_mode=WAL;')
conn.execute('PRAGMA synchronous=NORMAL;')
conn.execute('PRAGMA temp_store=MEMORY;')
conn.execute('PRAGMA mmap_size=30000000000;')

conn.commit()
conn.close()

print("✅ Base de datos optimizada para multi-usuario")
```

---

## 🚀 Paso 4: Iniciar la Aplicación

1. **En el servidor:** Puedes ejecutar la aplicación normalmente
2. **En cada cliente:** Ejecuta la aplicación con:
   ```bash
   python main.py
   ```

---

## ⚠️ Limitaciones y Recomendaciones

### Limitaciones de SQLite en Red:

- ✅ **Funciona bien** con 2-5 usuarios simultáneos
- ⚠️ **Puede tener problemas** con más de 5 usuarios
- ⚠️ **Requiere red estable** - WiFi fuerte o cable ethernet
- ⚠️ **No recomendado** para más de 10 usuarios

### Recomendaciones:

1. **Respaldos Automáticos:**

   - Los respaldos se crean automáticamente al iniciar
   - Guarda copias en otra ubicación regularmente

2. **Evitar Conflictos:**

   - No edites el mismo paciente desde 2 computadoras al mismo tiempo
   - Cierra la aplicación correctamente (no fuerces el cierre)

3. **Red Estable:**

   - Usa conexión por cable si es posible
   - Asegúrate de que el servidor esté siempre encendido

4. **Permisos:**
   - Todos los usuarios deben tener permisos de lectura/escritura
   - Verifica que el antivirus no bloquee el acceso a la red

---

## 🔧 Solución de Problemas

### Problema: "Base de datos bloqueada"

**Solución:**

1. Cierra todas las instancias de la aplicación
2. Espera 30 segundos
3. Vuelve a abrir

### Problema: "No se puede conectar a la base de datos"

**Solución:**

1. Verifica que la unidad de red esté mapeada (debe aparecer en "Este equipo")
2. Prueba abrir la carpeta compartida manualmente
3. Verifica que el servidor esté encendido y en la red

### Problema: La aplicación es muy lenta

**Solución:**

1. Verifica la velocidad de la red
2. Considera usar cable ethernet en lugar de WiFi
3. Reduce el número de usuarios simultáneos

---

## 🎯 Alternativa: PostgreSQL (Para Más Usuarios)

Si necesitas más de 5 usuarios simultáneos, considera migrar a PostgreSQL:

### Ventajas:

- ✅ Soporta 50+ usuarios simultáneos
- ✅ Mejor rendimiento
- ✅ Más robusto

### Desventajas:

- ❌ Requiere instalar y configurar servidor PostgreSQL
- ❌ Más complejo de mantener
- ❌ Requiere conocimientos técnicos

**Si decides usar PostgreSQL, necesitarás:**

1. Instalar PostgreSQL en el servidor
2. Crear la base de datos
3. Cambiar `db_type = postgresql` en `config.ini`
4. Configurar las credenciales de conexión

---

## 📞 Soporte

Si tienes problemas con la configuración multi-usuario:

1. Verifica que todas las computadoras estén en la misma red
2. Asegúrate de que los permisos de la carpeta compartida sean correctos
3. Prueba la conexión abriendo la carpeta compartida manualmente
4. Revisa los logs en `logs/clinic_audit.log`

---

## ✅ Checklist de Configuración

- [ ] Carpeta compartida creada en el servidor
- [ ] Permisos de lectura/escritura configurados
- [ ] Unidad de red mapeada en cada cliente
- [ ] Base de datos optimizada con WAL mode
- [ ] Aplicación instalada en cada cliente
- [ ] Ruta de base de datos actualizada en cada cliente
- [ ] Prueba exitosa desde cada computadora

¡Listo! Ahora puedes trabajar con múltiples computadoras simultáneamente. 🎉
