import shutil
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest

from multimodal_rag.openai_cache import OpenAICache, OpenAICacheKey, hash_openai_input
from multimodal_rag.storage import connect_sqlite, initialize_sqlite_database


@pytest.fixture
def local_runtime_path() -> Generator[Path]:
    runtime_path = Path("data") / "test-openai-cache" / uuid.uuid4().hex
    runtime_path.mkdir(parents=True, exist_ok=True)
    try:
        yield runtime_path
    finally:
        shutil.rmtree(runtime_path, ignore_errors=True)


def test_cache_miss_returns_none(local_runtime_path: Path) -> None:
    sqlite_path = local_runtime_path / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        cache = OpenAICache(connection)
        result = cache.lookup(
            OpenAICacheKey(
                input_hash="sha256:question",
                model="gpt-test",
                prompt_version="decomposition-v1",
                schema_version="decomposition-schema-v1",
            )
        )

    assert result is None


def test_written_response_is_retrievable(local_runtime_path: Path) -> None:
    sqlite_path = local_runtime_path / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)
    key = OpenAICacheKey(
        input_hash="sha256:question",
        model="gpt-test",
        prompt_version="verification-v1",
        schema_version="verification-schema-v1",
    )

    with connect_sqlite(sqlite_path) as connection:
        OpenAICache(connection).write(key, {"accepted_evidence_ids": ["candidate-1"]})
        connection.commit()

    with connect_sqlite(sqlite_path) as connection:
        result = OpenAICache(connection).lookup(key)

    assert result == {"accepted_evidence_ids": ["candidate-1"]}


@pytest.mark.parametrize(
    ("field", "different_value"),
    [
        ("input_hash", "sha256:different-question"),
        ("model", "gpt-test-new"),
        ("prompt_version", "verification-v2"),
        ("schema_version", "verification-schema-v2"),
    ],
)
def test_cache_entries_are_separated_by_every_key_dimension(
    local_runtime_path: Path,
    field: str,
    different_value: str,
) -> None:
    sqlite_path = local_runtime_path / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)
    dimensions = {
        "input_hash": "sha256:question",
        "model": "gpt-test",
        "prompt_version": "verification-v1",
        "schema_version": "verification-schema-v1",
    }

    with connect_sqlite(sqlite_path) as connection:
        cache = OpenAICache(connection)
        cache.write(OpenAICacheKey(**dimensions), {"supported": True})
        dimensions[field] = different_value

        result = cache.lookup(OpenAICacheKey(**dimensions))

    assert result is None


def test_input_hash_is_deterministic_for_structurally_equal_payloads() -> None:
    first = hash_openai_input({"question": "Why?", "entities": ["pump", "seal"]})
    second = hash_openai_input({"entities": ["pump", "seal"], "question": "Why?"})

    assert first == second
    assert first.startswith("sha256:")
