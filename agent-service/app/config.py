"""All configuration comes from environment variables (set in docker-compose).

Keeping this in one small typed object means the rest of the code never reads
os.environ directly, and every tunable knob is visible in one place.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://citegraph:citegraph@db:5432/citegraph"

    agent_grpc_port: int = 50051
    agent_http_port: int = 8000

    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2:3b"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    chunk_size_tokens: int = 350
    chunk_overlap_tokens: int = 60

    retrieval_top_k: int = 6
    retrieval_min_similarity: float = 0.25
    citation_support_threshold: float = 0.45

    # Path to a trained logistic-regression classifier. If present it is used
    # for citation verification; otherwise we fall back to the similarity
    # threshold. Both are compared in the offline evaluation.
    classifier_path: str = "app/eval/classifier.joblib"


settings = Settings()
