import shutil
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from multimodal_rag.query_decomposition import (
    QUERY_DECOMPOSITION_PROMPT_VERSION,
    QueryDecompositionInput,
    decompose_query,
)
from multimodal_rag.storage import connect_sqlite, initialize_sqlite_database


class FakeQueryDecompositionAdapter:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.calls: list[QueryDecompositionInput] = []

    def decompose(self, decomposition_input: QueryDecompositionInput) -> dict[str, Any]:
        self.calls.append(decomposition_input)
        return self.responses[len(self.calls) - 1]


@pytest.fixture
def local_runtime_path() -> Generator[Path]:
    runtime_path = Path("data") / "test-query-decomposition" / uuid.uuid4().hex
    runtime_path.mkdir(parents=True, exist_ok=True)
    try:
        yield runtime_path
    finally:
        shutil.rmtree(runtime_path, ignore_errors=True)


def test_valid_model_response_returns_contract_validated_decomposition() -> None:
    adapter = FakeQueryDecompositionAdapter(
        [
            {
                "sub_questions": [
                    {
                        "subquestion_id": "sq_1",
                        "question": "What does fault E12 mean?",
                    },
                    {
                        "subquestion_id": "sq_2",
                        "question": "How is fault E12 repaired?",
                    },
                ],
                "entities": ["E12"],
            }
        ]
    )

    result = decompose_query(
        "What does E12 mean and how is it repaired?",
        adapter,
    )

    assert [part.question for part in result.sub_questions] == [
        "What does fault E12 mean?",
        "How is fault E12 repaired?",
    ]
    assert result.entities == ["E12"]
    assert result.fallback_used is False
    assert len(adapter.calls) == 1
    assert adapter.calls[0].validation_feedback is None


def test_invalid_model_response_gets_one_retry_with_validation_feedback() -> None:
    adapter = FakeQueryDecompositionAdapter(
        [
            {"sub_questions": [], "entities": ["E12"]},
            {
                "sub_questions": [
                    {"subquestion_id": "sq_1", "question": "What does E12 mean?"}
                ],
                "entities": ["E12"],
            },
        ]
    )

    result = decompose_query("What does E12 mean?", adapter)

    assert result.sub_questions[0].question == "What does E12 mean?"
    assert len(adapter.calls) == 2
    assert adapter.calls[1].validation_feedback is not None
    assert "sub_questions" in adapter.calls[1].validation_feedback
    assert "at least 1 item" in adapter.calls[1].validation_feedback


def test_two_invalid_model_responses_fall_back_to_complete_original_question() -> None:
    question = "What does E12 mean, how is it repaired, and what torque is required?"
    adapter = FakeQueryDecompositionAdapter(
        [
            {"sub_questions": [], "entities": []},
            {
                "sub_questions": [
                    {"subquestion_id": "sq_1", "question": "What does E12 mean?"},
                    {"subquestion_id": "sq_1", "question": "How is it repaired?"},
                ],
                "entities": ["E12"],
            },
        ]
    )

    result = decompose_query(question, adapter)

    assert result.model_dump() == {
        "sub_questions": [{"subquestion_id": "sq_1", "question": question}],
        "entities": [],
        "fallback_used": True,
    }
    assert len(adapter.calls) == 2


def test_valid_decomposition_is_reused_from_versioned_openai_cache(
    local_runtime_path: Path,
) -> None:
    sqlite_path = local_runtime_path / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)
    response = {
        "sub_questions": [{"subquestion_id": "sq_1", "question": "What is E12?"}],
        "entities": ["E12"],
    }

    with connect_sqlite(sqlite_path) as connection:
        first_adapter = FakeQueryDecompositionAdapter([response])
        first = decompose_query(
            "What is E12?",
            first_adapter,
            connection=connection,
            model="gpt-test",
            schema_version="decomposition-v1",
        )
        connection.commit()
        cached_adapter = FakeQueryDecompositionAdapter([])
        second = decompose_query(
            "What is E12?",
            cached_adapter,
            connection=connection,
            model="gpt-test",
            schema_version="decomposition-v1",
        )
        cache_row = connection.execute(
            "SELECT prompt_version FROM openai_cache_entries"
        ).fetchone()

    assert second == first
    assert cached_adapter.calls == []
    assert cache_row["prompt_version"] == QUERY_DECOMPOSITION_PROMPT_VERSION
