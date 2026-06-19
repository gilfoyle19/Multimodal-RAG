from functools import lru_cache
from pathlib import Path

from typing import Any

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


STRICT_NOT_FOUND_MESSAGE = (
    "I don't have necessary information in the given documents to answer this question."
)


class AppSettings(BaseSettings):
    """Runtime configuration for local paths, hosted models, and retrieval gates."""

    model_config = SettingsConfigDict(
        env_prefix="MULTIMODAL_RAG_",
        env_file=".env",
        extra="ignore",
    )

    database_path: Path = Path("database")
    data_path: Path = Path("data")
    sqlite_path: Path = Path("data/app.sqlite3")
    chroma_path: Path = Path("data/chroma")
    artifacts_path: Path = Path("data/artifacts")

    openai_api_key: SecretStr | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_caption_model: str = "gpt-4.1-mini"
    openai_decomposition_model: str = "gpt-4.1-mini"
    openai_verification_model: str = "gpt-4.1-mini"
    openai_answer_model: str = "gpt-4.1-mini"
    openai_cache_enabled: bool = True
    openai_cache_schema_version: str = "v1"

    retrieval_candidate_limit: int = Field(default=20, ge=1)
    keyword_candidate_limit: int = Field(default=20, ge=1)
    vector_candidate_limit: int = Field(default=20, ge=1)
    rerank_candidate_limit: int = Field(default=10, ge=1)
    verification_candidate_limit: int = Field(default=5, ge=1)

    allow_partial_answers: bool = True
    strict_not_found_message: str = STRICT_NOT_FOUND_MESSAGE

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def normalize_blank_openai_api_key(cls, value: Any) -> Any:
        if value == "":
            return None
        return value

    @model_validator(mode="after")
    def validate_candidate_limits(self) -> "AppSettings":
        if self.rerank_candidate_limit > self.retrieval_candidate_limit:
            raise ValueError("rerank_candidate_limit cannot exceed retrieval_candidate_limit")
        if self.verification_candidate_limit > self.rerank_candidate_limit:
            raise ValueError("verification_candidate_limit cannot exceed rerank_candidate_limit")
        return self


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
