import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"

# Cargar .env de forma simple (no depende de python-dotenv)
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        # no sobrescribimos variables ya exportadas en el entorno
        os.environ.setdefault(k, v)

class Settings:
    def __init__(self):
        self.master_key = os.getenv("CLINICA_MASTER_KEY") or os.getenv("clinica_master_key")
        if not self.master_key:
            raise RuntimeError("Falta CLINICA_MASTER_KEY en .env o entorno")
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY") or os.getenv("jwt_secret_key")
        if not self.jwt_secret_key:
            raise RuntimeError("Falta JWT_SECRET_KEY en .env o entorno")
        self.algorithm = os.getenv("ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./clinica.db")
        self.upload_dir = os.getenv("UPLOAD_DIR", "./secure/uploads")
        self.backup_dir = os.getenv("BACKUP_DIR", "./backups")

settings = Settings()
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.backup_dir, exist_ok=True)