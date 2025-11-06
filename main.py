from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, timedelta
import os
import shutil
import uuid
import sqlite3

from core.config import settings
from core.database import get_db, init_db
from core.security import (
    encrypt_dict, decrypt_data, hash_password, verify_password,
    create_access_token, verify_token
)
from core.audit import log_acceso, log_error, log_backup


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class PacienteCreate(BaseModel):
    nombre: str
    apellido: str
    telefono: str
    email: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    direccion: Optional[str] = None

class PacienteResponse(BaseModel):
    id_paciente: str
    nombre: str
    apellido: str
    telefono: str
    fecha_nacimiento: Optional[str] = None
    email: Optional[str] = None

class CitaCreate(BaseModel):
    id_paciente: str
    fecha_hora_inicio: str  # ISO8601
    fecha_hora_fin: str

class NotaClinicaCreate(BaseModel):
    id_cita: str
    nota: str
    codigo_cie10: Optional[str] = None
    plan_tratamiento: Optional[str] = None

class PagoCreate(BaseModel):
    id_cita: str
    monto: float
    metodo_pago: str
    transaccion_id: Optional[str] = None


app = FastAPI(
    title="Clínica Psicológica API",
    description="API segura para gestión de clínica (Dueño Único)",
    version="1.0.0"
)

# CORS (ajusta dominios en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependencia: valida JWT y retorna usuario"""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    
    # Verificar que el usuario existe y está activo
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario, activo FROM Usuarios WHERE id_usuario = ?", (payload["sub"],))
        user = cursor.fetchone()
        
        if not user or not user["activo"]:
            raise HTTPException(status_code=401, detail="Usuario inactivo")
    
    return payload["sub"]  # Retorna id_usuario


@app.post("/login")
def login(form: LoginRequest):
    """Autenticación y generación de token"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_usuario, contrasena_hash FROM Usuarios WHERE email = ?", (form.email,))
            user = cursor.fetchone()
            
            if not user or not verify_password(user["contrasena_hash"], form.password):
                raise HTTPException(status_code=401, detail="Credenciales inválidas")
            
            # Actualizar último acceso
            cursor.execute("UPDATE Usuarios SET ultimo_acceso = ? WHERE id_usuario = ?",
                         (datetime.utcnow().isoformat(), user["id_usuario"]))
        
        # Crear token
        access_token = create_access_token(data={"sub": user["id_usuario"]})
        log_acceso(user["id_usuario"], "Usuarios", user["id_usuario"], "LOGIN")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60
        }
    except Exception as e:
        log_error(f"Login fallido: {e}")
        raise HTTPException(status_code=500, detail="Error interno")


@app.post("/pacientes", status_code=201)
def crear_paciente(
    paciente: PacienteCreate,
    current_user: str = Depends(get_current_user)
):
    """Crea paciente con datos encriptados"""
    try:
        paciente_id = str(uuid.uuid4())
        
        # Encriptar datos sensibles
        datos_enc = encrypt_dict({
            "nombre": paciente.nombre,
            "apellido": paciente.apellido,
            "direccion": paciente.direccion
        })
        telefono_enc = encrypt_dict({"telefono": paciente.telefono})
        email_enc = encrypt_dict({"email": paciente.email}) if paciente.email else None
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Pacientes (id_paciente, datos_sensibles_encriptados, 
                                     telefono_encriptado, email_encriptado, fecha_nacimiento)
                VALUES (?, ?, ?, ?, ?)
            """, (paciente_id, datos_enc, telefono_enc, email_enc, paciente.fecha_nacimiento))
        
        log_acceso(current_user, "Pacientes", paciente_id, "INSERT")
        return {"id_paciente": paciente_id, "mensaje": "Paciente creado"}
    except Exception as e:
        log_error(f"Error creando paciente: {e}")
        raise HTTPException(status_code=500, detail="Error creando paciente")

@app.get("/pacientes/{id_paciente}", response_model=PacienteResponse)
def obtener_paciente(
    id_paciente: str,
    current_user: str = Depends(get_current_user)
):
    """Obtiene y desencripta paciente"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Pacientes WHERE id_paciente = ? AND activo = 1", (id_paciente,))
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Paciente no encontrado")
            
            # Desencriptar
            datos = decrypt_data(row["datos_sensibles_encriptados"])
            telefono = decrypt_data(row["telefono_encriptado"])
            email = decrypt_data(row["email_encriptado"])
            
            log_acceso(current_user, "Pacientes", id_paciente, "SELECT")
            
            return {
                "id_paciente": id_paciente,
                "nombre": datos.get("nombre"),
                "apellido": datos.get("apellido"),
                "telefono": telefono.get("telefono"),
                "email": email.get("email"),
                "fecha_nacimiento": row["fecha_nacimiento"]
            }
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error obteniendo paciente: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo paciente")

@app.get("/pacientes", response_model=List[PacienteResponse])
def listar_pacientes(
    limite: int = 100,
    offset: int = 0,
    current_user: str = Depends(get_current_user)
):
    """Lista pacientes activos (solo metadatos para speed)"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id_paciente, datos_sensibles_encriptados, telefono_encriptado, email_encriptado, fecha_nacimiento
                FROM Pacientes
                WHERE activo = 1
                LIMIT ? OFFSET ?
            """, (limite, offset))
            
            pacientes = []
            for row in cursor.fetchall():
                datos = decrypt_data(row["datos_sensibles_encriptados"])
                telefono = decrypt_data(row["telefono_encriptado"])
                email = decrypt_data(row["email_encriptado"])
                
                pacientes.append({
                    "id_paciente": row["id_paciente"],
                    "nombre": datos.get("nombre"),
                    "apellido": datos.get("apellido"),
                    "telefono": telefono.get("telefono"),
                    "email": email.get("email"),
                    "fecha_nacimiento": row["fecha_nacimiento"]
                })
            
            log_acceso(current_user, "Pacientes", "ALL", "SELECT")
            return pacientes
    except Exception as e:
        log_error(f"Error listando pacientes: {e}")
        raise HTTPException(status_code=500, detail="Error listando pacientes")

@app.delete("/pacientes/{id_paciente}")
def eliminar_paciente_logico(
    id_paciente: str,
    current_user: str = Depends(get_current_user)
):
    """Eliminación lógica (GDPR compliant)"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE Pacientes SET activo = 0 WHERE id_paciente = ?", (id_paciente,))
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Paciente no encontrado")
        
        log_acceso(current_user, "Pacientes", id_paciente, "DELETE")
        return {"mensaje": "Paciente desactivado (eliminación lógica)"}
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error eliminando paciente: {e}")
        raise HTTPException(status_code=500, detail="Error eliminando paciente")


@app.post("/citas", status_code=201)
def crear_cita(
    cita: CitaCreate,
    current_user: str = Depends(get_current_user)
):
    """Programa nueva cita"""
    try:
        cita_id = str(uuid.uuid4())
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Citas (id_cita, id_paciente, fecha_hora_inicio, fecha_hora_fin)
                VALUES (?, ?, ?, ?)
            """, (cita_id, cita.id_paciente, cita.fecha_hora_inicio, cita.fecha_hora_fin))
        
        log_acceso(current_user, "Citas", cita_id, "INSERT")
        return {"id_cita": cita_id, "mensaje": "Cita creada"}
    except Exception as e:
        log_error(f"Error creando cita: {e}")
        raise HTTPException(status_code=500, detail="Error creando cita")

@app.get("/citas")
def listar_citas(
    fecha: Optional[str] = None,
    estado: Optional[str] = None,
    current_user: str = Depends(get_current_user)
):
    """Lista citas con filtro opcional"""
    try:
        query = """
            SELECT c.*, p.datos_sensibles_encriptados
            FROM Citas c
            JOIN Pacientes p ON c.id_paciente = p.id_paciente
            WHERE c.estado != 'Cancelada'
        """
        params = []
        
        if fecha:
            query += " AND DATE(c.fecha_hora_inicio) = ?"
            params.append(fecha)
        if estado:
            query += " AND c.estado = ?"
            params.append(estado)
        
        query += " ORDER BY c.fecha_hora_inicio DESC"
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            citas = []
            for row in cursor.fetchall():
                datos = decrypt_data(row["datos_sensibles_encriptados"])
                citas.append({
                    "id_cita": row["id_cita"],
                    "id_paciente": row["id_paciente"],
                    "paciente_nombre": f"{datos.get('nombre')} {datos.get('apellido')}",
                    "fecha_hora_inicio": row["fecha_hora_inicio"],
                    "fecha_hora_fin": row["fecha_hora_fin"],
                    "estado": row["estado"]
                })
            
            log_acceso(current_user, "Citas", "ALL", "SELECT")
            return citas
    except Exception as e:
        log_error(f"Error listando citas: {e}")
        raise HTTPException(status_code=500, detail="Error listando citas")


@app.post("/notas-clinicas", status_code=201)
def crear_nota_clinica(
    nota: NotaClinicaCreate,
    current_user: str = Depends(get_current_user)
):
    """Crear nota clínica encriptada"""
    try:
        registro_id = str(uuid.uuid4())
        nota_enc = encrypt_dict({"nota": nota.nota})
        plan_enc = encrypt_dict({"plan": nota.plan_tratamiento}) if nota.plan_tratamiento else None
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Registro_Sesion (id_registro, id_cita, nota_clinica_encriptada, plan_tratamiento_encriptado, codigo_cie10)
                VALUES (?, ?, ?, ?, ?)
            """, (registro_id, nota.id_cita, nota_enc, plan_enc, nota.codigo_cie10))
        
        log_acceso(current_user, "Registro_Sesion", registro_id, "INSERT")
        return {"id_registro": registro_id, "mensaje": "Nota clínica guardada"}
    except Exception as e:
        log_error(f"Error guardando nota: {e}")
        raise HTTPException(status_code=500, detail="Error guardando nota")

@app.get("/notas-clinicas/{id_cita}")
def obtener_nota_clinica(
    id_cita: str,
    current_user: str = Depends(get_current_user)
):
    """Obtiene y desencripta nota clínica"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Registro_Sesion WHERE id_cita = ?", (id_cita,))
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Nota no encontrada")
            
            nota = decrypt_data(row["nota_clinica_encriptada"])
            plan = decrypt_data(row["plan_tratamiento_encriptado"])
            
            log_acceso(current_user, "Registro_Sesion", row["id_registro"], "SELECT")
            
            return {
                "id_registro": row["id_registro"],
                "nota": nota.get("nota"),
                "codigo_cie10": row["codigo_cie10"],
                "plan_tratamiento": plan.get("plan"),
                "version": row["version"],
                "creado_en": row["creado_en"]
            }
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error obteniendo nota: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo nota")

@app.post("/pagos", status_code=201)
def registrar_pago(
    pago: PagoCreate,
    current_user: str = Depends(get_current_user)
):
    """Registra pago por cita"""
    try:
        pago_id = str(uuid.uuid4())
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Pagos (id_pago, id_cita, monto, metodo_pago, transaccion_id, estado, fecha_pago)
                VALUES (?, ?, ?, ?, ?, 'Pagado', ?)
            """, (pago_id, pago.id_cita, pago.monto, pago.metodo_pago, pago.transaccion_id, datetime.utcnow().isoformat()))
        
        log_acceso(current_user, "Pagos", pago_id, "INSERT")
        return {"id_pago": pago_id, "mensaje": "Pago registrado"}
    except Exception as e:
        log_error(f"Error registrando pago: {e}")
        raise HTTPException(status_code=500, detail="Error registrando pago")

@app.post("/facturas/{id_pago}/subir")
def subir_factura_pdf(
    id_pago: str,
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    """Subir PDF de factura"""
    try:
        # Validar PDF
        if not file.content_type == "application/pdf":
            raise HTTPException(status_code=400, detail="Solo archivos PDF")
        
        # Guardar archivo
        filename = f"{uuid.uuid4()}.pdf"
        ruta = os.path.join(settings.upload_dir, "facturas", filename)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        
        with open(ruta, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Registrar en BD
        factura_id = str(uuid.uuid4())
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Facturas (id_factura, id_pago, numero_factura, pdf_ruta, fecha_emision)
                VALUES (?, ?, ?, ?, ?)
            """, (factura_id, id_pago, f"FAC-{datetime.now().year}-{id_pago[:8]}", ruta, datetime.utcnow().isoformat()))
        
        log_acceso(current_user, "Facturas", factura_id, "UPLOAD")
        return {"id_factura": factura_id, "ruta": ruta}
    except Exception as e:
        log_error(f"Error subiendo factura: {e}")
        raise HTTPException(status_code=500, detail="Error subiendo factura")


@app.get("/reportes/financiero")
def reporte_financiero(
    fecha_inicio: str,
    fecha_fin: str,
    current_user: str = Depends(get_current_user)
):
    """Reporte de ingresos vs egresos"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Ingresos
            cursor.execute("""
                SELECT SUM(monto) as total_ingresos, COUNT(*) as num_pagos
                FROM Pagos
                WHERE fecha_pago BETWEEN ? AND ? AND estado = 'Pagado'
            """, (fecha_inicio, fecha_fin))
            ingresos = cursor.fetchone()
            
            # Egresos
            cursor.execute("""
                SELECT SUM(monto) as total_egresos, COUNT(*) as num_gastos
                FROM Gastos
                WHERE fecha BETWEEN ? AND ?
            """, (fecha_inicio, fecha_fin))
            egresos = cursor.fetchone()
            
            log_acceso(current_user, "Reportes", "FINANCIERO", "SELECT")
            
            return {
                "periodo": f"{fecha_inicio} a {fecha_fin}",
                "ingresos": {
                    "total": ingresos["total_ingresos"] or 0,
                    "num_pagos": ingresos["num_pagos"]
                },
                "egresos": {
                    "total": egresos["total_egresos"] or 0,
                    "num_gastos": egresos["num_gastos"]
                },
                "ganancia_neta": (ingresos["total_ingresos"] or 0) - (egresos["total_egresos"] or 0)
            }
    except Exception as e:
        log_error(f"Error generando reporte: {e}")
        raise HTTPException(status_code=500, detail="Error generando reporte")

@app.post("/backup/crear")
def crear_backup(current_user: str = Depends(get_current_user)):
    """Crea backup cifrado de la BD"""
    try:
        backup_id = str(uuid.uuid4())
        fecha = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        ruta_backup = os.path.join(settings.backup_dir, f"clinica_{fecha}.db.gpg")
        
        # Crear backup usando sqlite3
        with sqlite3.connect('clinica.db') as conn:
            with open('temp_backup.sql', 'w') as f:
                for line in conn.iterdump():
                    f.write('%s\n' % line)
        
        # Cifrar con GPG (requiere tener gpg instalado)
        import subprocess
        subprocess.run([
            "gpg", "--cipher-algo", "AES256", "--symmetric", "--output", ruta_backup, "temp_backup.sql"
        ], input=settings.master_key.encode(), check=True)
        
        # Limpiar
        os.remove("temp_backup.sql")
        
        # Registrar
        tamano = os.path.getsize(ruta_backup) / (1024**3)  # GB
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Backups (id_backup, fecha_inicio, fecha_fin, ruta_almacenamiento, tamano_gb, estado)
                VALUES (?, ?, ?, ?, ?, 'Completado')
            """, (backup_id, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), ruta_backup, tamano))
        
        log_backup(ruta_backup, tamano, "Completado")
        return {"backup_id": backup_id, "ruta": ruta_backup, "tamano_gb": tamano}
    except Exception as e:
        log_error(f"Error creando backup: {e}")
        raise HTTPException(status_code=500, detail="Error creando backup")


@app.get("/health")
def health_check():
    """Health check de la API"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if os.path.exists("clinica.db") else "disconnected"
    }

@app.get("/dashboard")
def dashboard(current_user: str = Depends(get_current_user)):
    """Dashboard con estadísticas clave"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Pacientes activos
            cursor.execute("SELECT COUNT(*) as total FROM Pacientes WHERE activo = 1")
            total_pacientes = cursor.fetchone()["total"]
            
            # Citas de hoy
            cursor.execute("SELECT COUNT(*) as total FROM Citas WHERE DATE(fecha_hora_inicio) = DATE('now')")
            citas_hoy = cursor.fetchone()["total"]
            
            # Ingresos del mes
            cursor.execute("""
                SELECT SUM(monto) as total FROM Pagos
                WHERE strftime('%Y-%m', fecha_pago) = strftime('%Y-%m', 'now')
            """)
            ingresos_mes = cursor.fetchone()["total"] or 0
            
            log_acceso(current_user, "Dashboard", "STATS", "SELECT")
            
            return {
                "pacientes_activos": total_pacientes,
                "citas_hoy": citas_hoy,
                "ingresos_mes": ingresos_mes
            }
    except Exception as e:
        log_error(f"Error en dashboard: {e}")
        raise HTTPException(status_code=500, detail="Error en dashboard")

if __name__ == "__main__":
    import uvicorn
    
    # Inicializar DB si no existe
    if not os.path.exists("clinica.db"):
        init_db()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Desactivar en producción
        ssl_keyfile="certs/key.pem",  # Opcional: SSL
        ssl_certfile="certs/cert.pem"
    )