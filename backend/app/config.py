import os
from pathlib import Path
from urllib.parse import quote_plus
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

def load_mounted_secrets(path: str = "/var/secrets") -> None:
    secret_dir = Path(path)
    if not secret_dir.is_dir():
        return
    for secret_file in secret_dir.iterdir():
        if secret_file.is_file() and secret_file.name not in os.environ:
            os.environ[secret_file.name] = secret_file.read_text(encoding="utf-8").strip()
    if "DATABASE_URL" not in os.environ and os.environ.get("DATABASE_PASSWORD"):
        password = quote_plus(os.environ["DATABASE_PASSWORD"])
        os.environ["DATABASE_URL"] = f"postgresql+psycopg2://guardian:{password}@postgres:5432/guardian"

load_mounted_secrets()

class Settings(BaseSettings):
    app_env: str = "local"
    demo_mode: bool = True
    app_base_url: str = "http://localhost:3000"
    database_url: str = "sqlite:///./guardian.db"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    faiss_path: str = "/data/faiss"
    mcp_server_url: str = "http://localhost:8001"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    auto_execute_low_risk: bool = False
    production_approval_required: bool = True
    min_rca_confidence: float = 0.75
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "aiops-guardian@example.local"
    approval_email_to: str = "approver@example.local"
    availability_slo: float = Field(default=0.998, gt=0, lt=1)
    latency_threshold_ms: float = Field(default=500, gt=0)
    prometheus_url: str = "http://localhost:9090"
    auth_required: bool = False
    auth_secret: str = "local-development-secret-change-me"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
