# Guía de Respaldos de PostgreSQL

Esta guía explica cómo hacer respaldos (backups) de la base de datos de la Clínica Psicológica y cómo restaurarlos en caso de emergencia.

## ¿Por Qué Hacer Respaldos?

Los respaldos protegen tus datos contra:

- 🔥 Fallas de hardware
- 🐛 Errores de software
- 👤 Errores humanos
- 💾 Corrupción de datos
- 🔒 Ataques de ransomware

> [!IMPORTANT] > **Regla 3-2-1**: Mantén 3 copias de tus datos, en 2 medios diferentes, con 1 copia fuera del sitio.

## Tipos de Respaldo

### 1. Respaldo Manual (Recomendado para empezar)

- Se ejecuta cuando tú lo decides
- Útil antes de hacer cambios importantes
- Fácil de realizar

### 2. Respaldo Automático (Recomendado para producción)

- Se ejecuta automáticamente según un horario
- No requiere intervención manual
- Más confiable a largo plazo

## Respaldo Manual con pg_dump

### Paso 1: Abrir Símbolo del Sistema

1. Presiona `Win + R`
2. Escribe: `cmd`
3. Presiona Enter

### Paso 2: Navegar a la Carpeta de PostgreSQL

```cmd
cd "C:\Program Files\PostgreSQL\16\bin"
```

### Paso 3: Crear el Respaldo

**Comando básico:**

```cmd
pg_dump -U postgres -d clinic_db -F c -f "C:\Respaldos\clinic_backup_%date:~-4,4%%date:~-7,2%%date:~-10,2%.backup"
```

**Explicación:**

- `-U postgres`: Usuario de PostgreSQL
- `-d clinic_db`: Nombre de la base de datos
- `-F c`: Formato custom (comprimido)
- `-f`: Ruta del archivo de respaldo

**Ejemplo de uso:**

```cmd
pg_dump -U postgres -d clinic_db -F c -f "C:\Respaldos\clinic_backup_20241124.backup"
```

Cuando te pida la contraseña, ingresa la contraseña del usuario `postgres`.

### Paso 4: Verificar el Respaldo

1. Navega a la carpeta `C:\Respaldos\`
2. Verifica que el archivo `.backup` se haya creado
3. Revisa el tamaño del archivo (debería ser mayor a 0 KB)

## Restaurar un Respaldo

### Cuándo Restaurar

- Después de una pérdida de datos
- Al migrar a un nuevo servidor
- Para crear una copia de prueba de la base de datos

### Paso 1: Detener la Aplicación

**Importante:** Cierra la aplicación de Clínica Psicológica en todas las computadoras antes de restaurar.

### Paso 2: Eliminar la Base de Datos Actual (Opcional)

Si quieres restaurar sobre una base de datos existente:

1. Abre SQL Shell (psql)
2. Conéctate a PostgreSQL
3. Ejecuta:
   ```sql
   DROP DATABASE clinic_db;
   CREATE DATABASE clinic_db;
   \q
   ```

### Paso 3: Restaurar el Respaldo

1. Abre Símbolo del Sistema
2. Navega a la carpeta de PostgreSQL:
   ```cmd
   cd "C:\Program Files\PostgreSQL\16\bin"
   ```
3. Ejecuta el comando de restauración:
   ```cmd
   pg_restore -U postgres -d clinic_db -c "C:\Respaldos\clinic_backup_20241124.backup"
   ```

**Explicación:**

- `-U postgres`: Usuario de PostgreSQL
- `-d clinic_db`: Base de datos destino
- `-c`: Limpiar (drop) objetos antes de crear
- Última parte: Ruta del archivo de respaldo

### Paso 4: Verificar la Restauración

1. Abre SQL Shell (psql)
2. Conéctate a `clinic_db`
3. Verifica los datos:
   ```sql
   \c clinic_db
   SELECT COUNT(*) FROM users;
   SELECT COUNT(*) FROM patients;
   SELECT COUNT(*) FROM appointments;
   ```

Si los conteos son correctos, ¡la restauración fue exitosa! ✅

## Respaldos Automáticos con Programador de Tareas

### Paso 1: Crear Script de Respaldo

1. Abre Notepad
2. Copia el siguiente script:

```batch
@echo off
REM Script de respaldo automático para Clínica Psicológica
REM Configuración
set PGPASSWORD=TU_CONTRASEÑA_AQUI
set BACKUP_DIR=C:\Respaldos\Auto
set PGBIN=C:\Program Files\PostgreSQL\16\bin
set DATABASE=clinic_db
set USER=postgres

REM Crear carpeta de respaldos si no existe
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM Generar nombre de archivo con fecha y hora
set TIMESTAMP=%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%
set TIMESTAMP=%TIMESTAMP: =0%
set BACKUP_FILE=%BACKUP_DIR%\clinic_backup_%TIMESTAMP%.backup

REM Ejecutar respaldo
"%PGBIN%\pg_dump" -U %USER% -d %DATABASE% -F c -f "%BACKUP_FILE%"

REM Verificar si el respaldo fue exitoso
if %ERRORLEVEL% EQU 0 (
    echo Respaldo exitoso: %BACKUP_FILE%
) else (
    echo ERROR: El respaldo falló
)

REM Eliminar respaldos antiguos (más de 30 días)
forfiles /P "%BACKUP_DIR%" /M *.backup /D -30 /C "cmd /c del @path" 2>nul

REM Limpiar variable de contraseña
set PGPASSWORD=
```

3. **Reemplaza** `TU_CONTRASEÑA_AQUI` con la contraseña real de PostgreSQL
4. Guarda el archivo como `C:\Scripts\backup_clinic.bat`

> [!WARNING]
> Este archivo contiene la contraseña en texto plano. Protégelo adecuadamente:
>
> - Haz clic derecho → Propiedades → Seguridad
> - Asegúrate de que solo los administradores tengan acceso

### Paso 2: Programar la Tarea

1. **Abrir Programador de Tareas:**

   - Presiona `Win + R`
   - Escribe: `taskschd.msc`
   - Presiona Enter

2. **Crear Tarea Básica:**

   - Haz clic en "Crear tarea básica..." (panel derecho)
   - Nombre: `Respaldo Clínica Psicológica`
   - Descripción: `Respaldo automático diario de la base de datos`
   - Haz clic en "Siguiente"

3. **Desencadenador:**

   - Selecciona "Diariamente"
   - Haz clic en "Siguiente"
   - Configura la hora (recomendado: 2:00 AM cuando nadie usa el sistema)
   - Haz clic en "Siguiente"

4. **Acción:**

   - Selecciona "Iniciar un programa"
   - Haz clic en "Siguiente"
   - Programa: `C:\Scripts\backup_clinic.bat`
   - Haz clic en "Siguiente"

5. **Finalizar:**

   - Revisa la configuración
   - Marca "Abrir el cuadro de diálogo Propiedades al hacer clic en Finalizar"
   - Haz clic en "Finalizar"

6. **Configuración Adicional:**
   - En la pestaña "General":
     - Marca "Ejecutar tanto si el usuario inició sesión como si no"
     - Marca "Ejecutar con los privilegios más altos"
   - En la pestaña "Condiciones":
     - Desmarca "Iniciar la tarea solo si el equipo está conectado a la corriente alterna"
   - Haz clic en "Aceptar"
   - Ingresa la contraseña de Windows si se solicita

### Paso 3: Probar la Tarea

1. En el Programador de Tareas, busca tu tarea
2. Haz clic derecho → "Ejecutar"
3. Espera unos segundos
4. Verifica que se creó el archivo en `C:\Respaldos\Auto\`

## Estrategia de Respaldos Recomendada

### Para Uso Básico (1-5 usuarios)

- **Respaldo automático diario** a las 2:00 AM
- **Retención:** 30 días
- **Ubicación:** Disco duro local

### Para Uso Intensivo (5+ usuarios)

- **Respaldo automático diario** a las 2:00 AM
- **Respaldo semanal completo** los domingos
- **Retención:** 90 días
- **Ubicación:** Disco duro local + copia en disco externo

### Mejores Prácticas

1. ✅ Prueba restaurar un respaldo al menos una vez al mes
2. ✅ Guarda copias en un disco externo semanalmente
3. ✅ Verifica que los respaldos automáticos se estén ejecutando
4. ✅ Monitorea el espacio en disco de la carpeta de respaldos
5. ✅ Documenta el proceso de restauración

## Respaldo a Disco Externo o Red

### Opción 1: Copiar Manualmente

1. Conecta un disco externo USB
2. Copia la carpeta `C:\Respaldos\` al disco externo
3. Desconecta el disco y guárdalo en un lugar seguro

### Opción 2: Sincronización Automática

Usa herramientas como:

- **Robocopy** (incluido en Windows)
- **FreeFileSync** (gratuito)
- **Google Drive / OneDrive** (nube)

**Ejemplo con Robocopy:**

```cmd
robocopy "C:\Respaldos" "E:\Respaldos_Clinica" /MIR /R:3 /W:10
```

## Solución de Problemas

### El respaldo falla con "Permission denied"

- Ejecuta el Símbolo del sistema como Administrador
- Verifica que tengas permisos de escritura en la carpeta de destino

### El archivo de respaldo está vacío (0 KB)

- Verifica que la contraseña sea correcta
- Asegúrate de que la base de datos `clinic_db` exista
- Revisa los logs de PostgreSQL en `C:\Program Files\PostgreSQL\16\data\log\`

### La tarea programada no se ejecuta

- Verifica que el servicio "Programador de tareas" esté en ejecución
- Revisa el historial de la tarea en el Programador de Tareas
- Asegúrate de que la computadora esté encendida a la hora programada

### Error: "pg_dump no se reconoce como comando"

- Verifica que estés en la carpeta correcta: `C:\Program Files\PostgreSQL\16\bin`
- O agrega PostgreSQL al PATH del sistema

## Checklist de Respaldos

### Configuración Inicial

- [ ] Crear carpeta `C:\Respaldos\`
- [ ] Crear carpeta `C:\Scripts\`
- [ ] Crear script de respaldo `backup_clinic.bat`
- [ ] Programar tarea automática
- [ ] Probar respaldo manual
- [ ] Probar restauración

### Mantenimiento Mensual

- [ ] Verificar que los respaldos automáticos se estén ejecutando
- [ ] Revisar espacio en disco
- [ ] Copiar respaldos a disco externo
- [ ] Probar restaurar un respaldo antiguo
- [ ] Documentar cualquier problema

## Recursos Adicionales

- [Documentación oficial de pg_dump](https://www.postgresql.org/docs/16/app-pgdump.html)
- [Documentación oficial de pg_restore](https://www.postgresql.org/docs/16/app-pgrestore.html)

---

**Última actualización:** 2024-11-24
