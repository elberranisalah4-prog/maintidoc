"""MAINTIDOC Configuration Module

Defines core configuration, file paths, model configurations,
security parameters, and operational budgets as specified in the cadrage.
"""

from pathlib import Path
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CORPUS_DIR = DATA_DIR / "synthetic_corpus"
IMAGES_DIR = CORPUS_DIR / "images"
PROMPTS_DIR = BASE_DIR / "prompts"
DOCS_DIR = BASE_DIR / "docs"

class BudgetConfig(BaseModel):
    max_mcp_calls: int = 3
    max_model_calls: int = 6
    max_processing_time_sec: float = 60.0
    max_image_size_mb: float = 10.0
    max_context_tokens: int = 8192
    max_output_tokens: int = 2048

class ModelConfig(BaseModel):
    vlm_model_name: str = "Qwen/Qwen2.5-VL-7B-Instruct"
    text_embedding_model: str = "BAAI/bge-m3"
    visual_embedding_model: str = "openai/clip-vit-base-patch32"
    reranker_model: str = "BAAI/bge-reranker-base"
    reranker_top_k: int = 5
    vector_dimension: int = 128  # normalized embedding dim for fast local/FAISS indexing

class SecurityConfig(BaseModel):
    enable_prompt_injection_guard: bool = True
    enable_rbac: bool = True
    strict_hitl_ticket_creation: bool = True
    jwt_secret: str = "maintidoc-demo-secret-key-2026"
    jwt_algorithm: str = "HS256"

class Settings(BaseModel):
    project_name: str = "MAINTIDOC"
    environment: str = "development"
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    models: ModelConfig = Field(default_factory=ModelConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

settings = Settings()
