from pydantic_settings import BaseSettings, SettingsConfigDict

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
    prometheus_url: str = "http://localhost:9090"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
