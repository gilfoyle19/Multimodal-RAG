from pathlib import Path

import pytest
from pydantic import ValidationError
from pytest import MonkeyPatch

from multimodal_rag.settings import AppSettings


def test_settings_defaults_use_local_paths_without_credentials() -> None:
    settings = AppSettings()

    assert settings.database_path == Path("database")
    assert settings.data_path == Path("data")
    assert settings.sqlite_path == Path("data/app.sqlite3")
    assert settings.chroma_path == Path("data/chroma")
    assert settings.artifacts_path == Path("data/artifacts")
    assert settings.openai_api_key is None
    assert settings.openai_embedding_model
    assert settings.openai_answer_model
    assert settings.openai_cache_enabled is True
    assert settings.strict_not_found_message == (
        "I don't have necessary information in the given documents to answer this question."
    )


def test_settings_accept_environment_overrides_without_live_credentials(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("MULTIMODAL_RAG_DATABASE_PATH", "manuals")
    monkeypatch.setenv("MULTIMODAL_RAG_DATA_PATH", "runtime")
    monkeypatch.setenv("MULTIMODAL_RAG_OPENAI_EMBEDDING_MODEL", "text-embedding-test")
    monkeypatch.setenv("MULTIMODAL_RAG_RETRIEVAL_CANDIDATE_LIMIT", "12")

    settings = AppSettings()

    assert settings.database_path == Path("manuals")
    assert settings.data_path == Path("runtime")
    assert settings.openai_embedding_model == "text-embedding-test"
    assert settings.retrieval_candidate_limit == 12


def test_settings_reject_invalid_retrieval_thresholds() -> None:
    with pytest.raises(ValidationError):
        AppSettings(retrieval_candidate_limit=0)

    with pytest.raises(ValidationError):
        AppSettings(verification_candidate_limit=6, rerank_candidate_limit=5)


def test_local_artifact_and_secret_paths_are_gitignored() -> None:
    ignored_paths = {
        line.strip() for line in Path(".gitignore").read_text(encoding="utf-8").splitlines()
    }

    assert ".env" in ignored_paths
    assert ".env.*" in ignored_paths
    assert "database/" in ignored_paths
    assert "data/" in ignored_paths
    assert "artifacts/" in ignored_paths
