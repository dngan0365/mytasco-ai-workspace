from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cấu hình toàn cục, đọc từ biến môi trường hoặc file .env."""

    app_name: str = "My Tasco AI Workspace"

    jwt_secret: str = "please-change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    dataset_path: str = "app/data/ai_workspace_dataset_vietnamese_participants.xlsx"
    # Neu file nay ton tai (do services/ingestion/build_index.py tao ra), orchestrator
    # se nap thang artifact thay vi tu doc/parse lai xlsx moi lan khoi dong.
    index_artifact_path: str = "../ingestion/output/knowledge_index.pkl"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"

    top_k_retrieval: int = 4
    database_url: str = "postgresql+psycopg://mytasco:mytasco_dev_password@postgres:5432/mytasco"
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "enterprise_chunks"
    embedding_provider: str = "sentence_transformers"
    embedding_model: str = "intfloat/multilingual-e5-base"
    embedding_dimension: int = 768
    upload_dir: str = "data/uploads"
    max_upload_mb: int = 15
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    enable_telemetry: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
