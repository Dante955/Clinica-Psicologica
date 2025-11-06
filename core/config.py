import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # mapeo explícito a las variables en .env (coincide con .env actual)
    master_key: str = Field(..., env="CLINICA_MASTER_KEY")
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    algorithm: str = Field("HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(480, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    database_url: str = Field("sqlite:///./clinica.db", env="DATABASE_URL")
    upload_dir: str = Field("./secure/uploads", env="UPLOAD_DIR")
    backup_dir: str = Field("./backups", env="BACKUP_DIR")
    
    class Config:
        env_file = ".env"

settings = Settings()
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.backup_dir, exist_ok=True)