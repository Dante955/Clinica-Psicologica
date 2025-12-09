# Documentación de Requerimientos - Clínica Psicológica

## 1. Introducción

Este documento define los requerimientos funcionales y no funcionales para el sistema de gestión de la Clínica Psicológica. El sistema está diseñado para gestionar pacientes, citas, historias clínicas y reportes financieros.

## 2. Requerimientos Funcionales

### 2.1. Gestión de Usuarios y Autenticación

- **RF-001**: El sistema debe permitir el inicio de sesión con nombre de usuario y contraseña.
- **RF-002**: El sistema debe manejar roles de usuario: ADMINISTRADOR, PSICOLOGO, SOPORTE.
- **RF-003**: Solo los administradores pueden crear, editar y eliminar otros usuarios.
- **RF-004**: El rol SOPORTE debe tener acceso a configuraciones técnicas (Base de Datos, Email, Logs) pero no a datos clínicos sensibles.

### 2.2. Gestión de Pacientes

- **RF-005**: El sistema debe permitir registrar nuevos pacientes con información personal y de contacto.
- **RF-006**: Se debe poder diferenciar entre pacientes Adultos y Niños (con tutores).
- **RF-007**: Los psicólogos solo deben ver sus propios pacientes (a menos que sean administradores).
- **RF-008**: Se debe poder editar y eliminar pacientes (con confirmación de eliminación en cascada para citas).

### 2.3. Gestión de Citas

- **RF-009**: El sistema debe permitir agendar citas asociando un paciente y un psicólogo.
- **RF-010**: Se debe visualizar un calendario con las citas programadas.
- **RF-011**: Los estados de las citas deben ser gestionables: Programada, Completada, Cancelada, No Asistió.
- **RF-012**: El sistema debe permitir enviar recordatorios de citas por correo electrónico.

### 2.4. Gestión Financiera

- **RF-013**: El sistema debe registrar pagos asociados a las citas.
- **RF-014**: El sistema debe permitir registrar gastos operativos.
- **RF-015**: El sistema debe generar reportes financieros (Ingresos vs Gastos) y visualizarlos gráficamente.
- **RF-016**: Solo los administradores deben tener acceso a los reportes financieros.

### 2.5. Configuración y Mantenimiento

- **RF-017**: El sistema debe permitir configurar la conexión a base de datos (SQLite y SQL Server).
- **RF-018**: El sistema debe tener una herramienta de migración de datos de SQLite a SQL Server.
- **RF-019**: El sistema debe registrar logs de auditoría para acciones críticas.

## 3. Requerimientos No Funcionales

### 3.1. Rendimiento

- **RNF-001**: La aplicación debe cargar en menos de 5 segundos.
- **RNF-002**: Las consultas a la base de datos no deben congelar la interfaz de usuario (uso de hilos o tiempos de respuesta rápidos).

### 3.2. Seguridad

- **RNF-003**: Las contraseñas de usuario deben almacenarse hasheadas (no texto plano).
- **RNF-004**: La conexión a SQL Server debe soportar autenticación segura.

### 3.3. Usabilidad

- **RNF-005**: La interfaz debe ser intuitiva y consistente (tema visual unificado).
- **RNF-006**: El sistema debe proporcionar feedback al usuario (mensajes de éxito/error).

### 3.4. Compatibilidad

- **RNF-007**: El sistema debe funcionar en entorno Windows 10/11.
- **RNF-008**: El sistema debe ser capaz de operar en red local (para conexión a SQL Server).
