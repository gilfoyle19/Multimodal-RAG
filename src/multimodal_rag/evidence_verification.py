import json
import sqlite3
from typing import Any, Protocol

from pydantic import BaseModel, Field, ValidationError

from multimodal_rag.contracts import (
    ContractModel,
    EvidenceCandidate,
    EvidenceVerificationResult,
    QueryDecomposition,
    VerifiedEvidence,
)
from multimodal_rag.local_reranking import select_candidates_for_verification
from multimodal_rag.openai_cache import OpenAICache, OpenAICacheKey, hash_openai_input


EVIDENCE_VERIFICATION_PROMPT_VERSION = "evidence-verification-v1"


class EvidenceVerificationInput(BaseModel):
    decomposition: QueryDecomposition
    candidates: list[EvidenceCandidate]
    validation_feedback: str | None = None


class EvidenceVerificationAdapter(Protocol):
    def verify(self, verification_input: EvidenceVerificationInput) -> dict[str, Any]:
        """Return structured evidence verification decisions."""


class OpenAIEvidenceVerificationAdapter:
    """OpenAI-backed adapter behind the fakeable verification boundary."""

    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self._client: Any = OpenAI(api_key=api_key)
        self._model = model

    def verify(self, verification_input: EvidenceVerificationInput) -> dict[str, Any]:
        instruction = (
            "Verify whether each supplied evidence candidate directly supports each required "
            "sub-question. Accept only supplied candidate IDs. Return JSON with "
            "accepted_evidence entries containing candidate_id, supported_subquestion_ids, and "
            "relevance_reason, plus unsupported_subquestion_ids. Every sub-question must be "
            "classified as supported or unsupported. Do not use general knowledge."
        )
        if verification_input.validation_feedback is not None:
            instruction += (
                " The previous response was invalid. Correct these validation errors: "
                f"{verification_input.validation_feedback}"
            )
        response = self._client.responses.create(
            model=self._model,
            input=[
                {"role": "system", "content": instruction},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "sub_questions": [
                                part.model_dump(mode="json")
                                for part in verification_input.decomposition.sub_questions
                            ],
                            "candidates": [
                                {
                                    "candidate_id": candidate.candidate_id,
                                    "excerpt": candidate.excerpt,
                                }
                                for candidate in verification_input.candidates
                            ],
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                },
            ],
        )
        parsed = json.loads(response.output_text)
        if not isinstance(parsed, dict):
            raise ValueError("invalid evidence verification response")
        return parsed


class EvidenceVerificationError(RuntimeError):
    """Raised when model output remains invalid after the single retry."""


class _AcceptedEvidence(ContractModel):
    candidate_id: str = Field(min_length=1)
    supported_subquestion_ids: list[str] = Field(min_length=1)
    relevance_reason: str = Field(min_length=1)


class _VerificationDecision(ContractModel):
    accepted_evidence: list[_AcceptedEvidence] = Field(default_factory=list)
    unsupported_subquestion_ids: list[str] = Field(default_factory=list)


def verify_evidence(
    decomposition: QueryDecomposition,
    ranked_candidates: list[EvidenceCandidate],
    adapter: EvidenceVerificationAdapter,
    *,
    candidate_limit: int = 5,
    connection: sqlite3.Connection | None = None,
    model: str | None = None,
    schema_version: str | None = None,
    prompt_version: str = EVIDENCE_VERIFICATION_PROMPT_VERSION,
) -> EvidenceVerificationResult:
    """Verify the configured reranked shortlist against all required sub-questions."""

    candidates = select_candidates_for_verification(ranked_candidates, limit=candidate_limit)
    initial_input = EvidenceVerificationInput(
        decomposition=decomposition,
        candidates=candidates,
    )
    cache: OpenAICache | None = None
    cache_key: OpenAICacheKey | None = None
    if connection is not None:
        if model is None or schema_version is None:
            raise ValueError("model and schema_version are required when caching verification")
        cache = OpenAICache(connection)
        cache_key = OpenAICacheKey(
            input_hash=hash_openai_input(
                {
                    "decomposition": decomposition.model_dump(mode="json"),
                    "candidates": [candidate.model_dump(mode="json") for candidate in candidates],
                }
            ),
            model=model,
            prompt_version=prompt_version,
            schema_version=schema_version,
        )
        cached = cache.lookup(cache_key)
        if cached is not None:
            return _validate_and_normalize(cached, decomposition, candidates)

    response = adapter.verify(initial_input)
    try:
        result = _validate_and_normalize(response, decomposition, candidates)
    except (ValidationError, ValueError) as error:
        feedback = _validation_feedback(error)
        retry_response = adapter.verify(
            initial_input.model_copy(update={"validation_feedback": feedback})
        )
        try:
            result = _validate_and_normalize(retry_response, decomposition, candidates)
        except (ValidationError, ValueError) as retry_error:
            raise EvidenceVerificationError(
                "evidence verification failed after validation retry"
            ) from retry_error
        response = retry_response

    if cache is not None and cache_key is not None:
        cache.write(cache_key, response)
    return result


def _validate_and_normalize(
    response: dict[str, Any],
    decomposition: QueryDecomposition,
    candidates: list[EvidenceCandidate],
) -> EvidenceVerificationResult:
    decision = _VerificationDecision.model_validate(response)
    candidate_by_id = {candidate.candidate_id: candidate for candidate in candidates}
    subquestion_ids = {part.subquestion_id for part in decomposition.sub_questions}
    supported_ids: set[str] = set()
    verified: list[VerifiedEvidence] = []

    seen_candidates: set[str] = set()
    for accepted in decision.accepted_evidence:
        if accepted.candidate_id not in candidate_by_id:
            raise ValueError(f"unknown candidate id: {accepted.candidate_id}")
        if accepted.candidate_id in seen_candidates:
            raise ValueError(f"duplicate accepted candidate id: {accepted.candidate_id}")
        seen_candidates.add(accepted.candidate_id)
        accepted_ids = set(accepted.supported_subquestion_ids)
        if len(accepted_ids) != len(accepted.supported_subquestion_ids):
            raise ValueError("supported subquestion ids must be unique per candidate")
        unknown = accepted_ids - subquestion_ids
        if unknown:
            raise ValueError(f"unknown subquestion id: {sorted(unknown)[0]}")
        supported_ids.update(accepted_ids)
        candidate = candidate_by_id[accepted.candidate_id]
        verified.append(
            VerifiedEvidence(
                evidence_id=f"evidence:{candidate.candidate_id}",
                candidate_id=candidate.candidate_id,
                source_element_id=candidate.source_element_id,
                citation=candidate.citation,
                supported_subquestion_ids=accepted.supported_subquestion_ids,
                excerpt=candidate.excerpt,
                relevance_reason=accepted.relevance_reason,
            )
        )

    unsupported_ids = set(decision.unsupported_subquestion_ids)
    if len(unsupported_ids) != len(decision.unsupported_subquestion_ids):
        raise ValueError("unsupported subquestion ids must be unique")
    unknown_unsupported = unsupported_ids - subquestion_ids
    if unknown_unsupported:
        raise ValueError(f"unknown subquestion id: {sorted(unknown_unsupported)[0]}")
    overlap = supported_ids & unsupported_ids
    if overlap:
        raise ValueError(f"subquestion cannot be both supported and unsupported: {sorted(overlap)[0]}")
    missing = subquestion_ids - supported_ids - unsupported_ids
    if missing:
        raise ValueError(f"subquestion must be classified: {sorted(missing)[0]}")

    return EvidenceVerificationResult(
        verified_evidence=verified,
        unsupported_subquestion_ids=decision.unsupported_subquestion_ids,
    )


def _validation_feedback(error: ValidationError | ValueError) -> str:
    if not isinstance(error, ValidationError):
        return str(error)
    return json.dumps(
        [
            {
                "location": [str(part) for part in detail["loc"]],
                "message": detail["msg"],
                "error_type": detail["type"],
            }
            for detail in error.errors(include_url=False, include_input=False)
        ],
        sort_keys=True,
        separators=(",", ":"),
    )
