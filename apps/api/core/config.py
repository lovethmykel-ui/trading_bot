import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Quantum Ensemble"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://quantum_user:quantum_password@localhost:5432/quantum_ensemble")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "YOUR_SUPER_SECRET_KEY_HERE")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Bybit Settings
    BYBIT_TESTNET: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
