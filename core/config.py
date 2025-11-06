import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    master_key: str
    jwt_secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    database_url: str
    upload_dir: str
    backup_dir: str
    
    class Config:
        env_file = ".env"

settings = Settings()
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.backup_dir, exist_ok=True)