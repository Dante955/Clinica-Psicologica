import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from argon2 import PasswordHasher
from datetime import datetime, timedelta
from jose import JWTError, jwt
from core.config import settings

# Inicialización
fernet = Fernet(settings.master_key.encode())
ph = PasswordHasher()

# =============================================
# ENCRIPTACIÓN DE DATOS
# =============================================

def encrypt_dict(data: dict) -> bytes:
    """Encripta dict -> bytes para SQLite"""
    if not data:
        return None
    json_str = json.dumps(data, ensure_ascii=False)
    return fernet.encrypt(json_str.encode('utf-8'))

def decrypt_data(encrypted_blob: bytes) -> dict:
    """Desencripta bytes de SQLite -> dict"""
    if not encrypted_blob:
        return {}
    try:
        decrypted_str = fernet.decrypt(encrypted_blob).decode('utf-8')
        return json.loads(decrypted_str)
    except Exception as e:
        print(f"❌ Error desencriptando: {e}")
        return {}

def hash_password(password: str) -> str:
    """Hash seguro con Argon2id"""
    return ph.hash(password)

def verify_password(hash_str: str, password: str) -> bool:
    """Verifica hash Argon2id"""
    try:
        ph.verify(hash_str, password)
        # Rehash si es necesario (mejora de seguridad)
        if ph.check_needs_rehash(hash_str):
            return "NEED_REHASH"
        return True
    except:
        return False

# =============================================
# JWT TOKENS
# =============================================

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Crea token JWT"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.algorithm)

def verify_token(token: str) -> dict:
    """Verifica y decodifica JWT"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None