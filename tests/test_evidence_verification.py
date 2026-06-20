import shutil
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from multimodal_rag.contracts import (
    ChunkKind,
    CitationIdentity,
    EvidenceCandidate,
    QueryDecomposition,
    RetrievalScores,
)
from multimodal_rag.evidence_verification import (
    EVIDENCE_VERIFICATION_PROMPT_VERSION,
    EvidenceVerificationError,
    EvidenceVerificationInput,
    verify_evidence,
)
from multimodal_rag.storage import connect_sqlite, initialize_sqlite_database


class FakeEvidenceVerificationAdapter:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.calls: list[EvidenceVerificationInput] = []

    def verify(self, verification_input: EvidenceVerificationInput) -> dict[str, Any]:
        self.calls.append(verification_input)
        return self.responses[len(self.calls) - 1]


@pytest.fixture
def local_runtime_path() -> Generator[Path]:
    runtime_path = Path("data") / "test-evidence-verification" / uuid.uuid4().hex
    runtime_path.mkdir(parents=True, exist_ok=True)
    try:
        yield runtime_path
    finally:
        shutil.rmtree(runtime_path, ignore_errors=True)


def _decomposition() -> QueryDecomposition:
    return QueryDecomposition.model_validate(
        {
            "sub_questions": [
                {"subquestion_id": "sq_1", "question": "What does E12 mean?"},
                {"subquestion_id": "sq_2", "question": "How is E12 repaired?"},
            ],
            "entities": ["E12"],
        }
    )


def _candidate(candidate_id: str, rerank: float) -> EvidenceCandidate:
    source_id = f"source:{candidate_id}"
    return EvidenceCandidate(
        candidate_id=candidate_id,
        chunk_id=f"chunk:{candidate_id}",
        source_element_id=source_id,
        chunk_kind=ChunkKind.SOURCE_ELEMENT,
        citation=CitationIdentity(
            document_id="doc-1",
            page_id="page-1",
            source_element_id=source_id,
            page_number=1,
            citation_key=f"manual.pdf:p1:{source_id}",
        ),
        excerpt=f"Excerpt for {candidate_id}",
        retrieval_scores=RetrievalScores(rerank=rerank),
    )


def test_accepts_evidence_and_sends_only_configured_top_candidates() -> None:
    candidates = [_candidate("c1", 0.9), _candidate("c2", 0.8), _candidate("c3", 0.7)]
    adapter = FakeEvidenceVerificationAdapter(
        [
            {
                "accepted_evidence": [
                    {
                        "candidate_id": "c1",
                        "supported_subquestion_ids": ["sq_1"],
                        "relevance_reason": "Defines E12 directly.",
                    }
                ],
                "unsupported_subquestion_ids": ["sq_2"],
            }
        ]
    )

    result = verify_evidence(_decomposition(), candidates, adapter, candidate_limit=2)

    assert [item.candidate_id for item in adapter.calls[0].candidates] == ["c1", "c2"]
    assert result.verified_evidence[0].candidate_id == "c1"
    assert result.verified_evidence[0].evidence_id == "evidence:c1"
    assert result.unsupported_subquestion_ids == ["sq_2"]


def test_rejected_evidence_explicitly_marks_all_subquestions_unsupported() -> None:
    adapter = FakeEvidenceVerificationAdapter(
        [
            {
                "accepted_evidence": [],
                "unsupported_subquestion_ids": ["sq_1", "sq_2"],
            }
        ]
    )

    result = verify_evidence(_decomposition(), [_candidate("c1", 0.9)], adapter)

    assert result.verified_evidence == []
    assert result.unsupported_subquestion_ids == ["sq_1", "sq_2"]


def test_partial_verification_preserves_supported_and_unsupported_parts() -> None:
    adapter = FakeEvidenceVerificationAdapter(
        [
            {
                "accepted_evidence": [
                    {
                        "candidate_id": "c2",
                        "supported_subquestion_ids": ["sq_2"],
                        "relevance_reason": "Provides the documented reset procedure.",
                    }
                ],
                "unsupported_subquestion_ids": ["sq_1"],
            }
        ]
    )

    result = verify_evidence(_decomposition(), [_candidate("c2", 0.8)], adapter)

    assert result.verified_evidence[0].supported_subquestion_ids == ["sq_2"]
    assert result.unsupported_subquestion_ids == ["sq_1"]


def test_invalid_candidate_reference_retries_with_deterministic_feedback() -> None:
    adapter = FakeEvidenceVerificationAdapter(
        [
            {
                "accepted_evidence": [
                    {
                        "candidate_id": "invented",
                        "supported_subquestion_ids": ["sq_1"],
                        "relevance_reason": "Unsupported reference.",
                    }
                ],
                "unsupported_subquestion_ids": ["sq_2"],
            },
            {
                "accepted_evidence": [
                    {
                        "candidate_id": "c1",
                        "supported_subquestion_ids": ["sq_1", "sq_2"],
                        "relevance_reason": "Supports both requested parts.",
                    }
                ],
                "unsupported_subquestion_ids": [],
            },
        ]
    )

    result = verify_evidence(_decomposition(), [_candidate("c1", 0.9)], adapter)

    assert len(adapter.calls) == 2
    assert adapter.calls[1].validation_feedback == "unknown candidate id: invented"
    assert result.unsupported_subquestion_ids == []


def test_two_invalid_responses_raise_deterministic_verification_error() -> None:
    invalid = {
        "accepted_evidence": [],
        "unsupported_subquestion_ids": ["sq_1"],
    }
    adapter = FakeEvidenceVerificationAdapter([invalid, invalid])

    with pytest.raises(
        EvidenceVerificationError,
        match="evidence verification failed after validation retry",
    ):
        verify_evidence(_decomposition(), [_candidate("c1", 0.9)], adapter)

    assert len(adapter.calls) == 2
    assert adapter.calls[1].validation_feedback is not None
    assert "sq_2" in adapter.calls[1].validation_feedback


def test_valid_verification_is_reused_from_versioned_openai_cache(
    local_runtime_path: Path,
) -> None:
    sqlite_path = local_runtime_path / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)
    response = {
        "accepted_evidence": [
            {
                "candidate_id": "c1",
                "supported_subquestion_ids": ["sq_1", "sq_2"],
                "relevance_reason": "Supports both requested parts.",
            }
        ],
        "unsupported_subquestion_ids": [],
    }
    candidates = [_candidate("c1", 0.9)]

    with connect_sqlite(sqlite_path) as connection:
        first_adapter = FakeEvidenceVerificationAdapter([response])
        first = verify_evidence(
            _decomposition(),
            candidates,
            first_adapter,
            connection=connection,
            model="gpt-test",
            schema_version="verification-v1",
        )
        connection.commit()
        cached_adapter = FakeEvidenceVerificationAdapter([])
        second = verify_evidence(
            _decomposition(),
            candidates,
            cached_adapter,
            connection=connection,
            model="gpt-test",
            schema_version="verification-v1",
        )
        cache_row = connection.execute(
            "SELECT prompt_version FROM openai_cache_entries"
        ).fetchone()

    assert second == first
    assert cached_adapter.calls == []
    assert cache_row["prompt_version"] == EVIDENCE_VERIFICATION_PROMPT_VERSION
