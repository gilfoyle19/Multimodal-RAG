import re
from typing import Protocol

from multimodal_rag.contracts import EvidenceCandidate, RetrievalScores


class LocalReranker(Protocol):
    """Local scoring boundary for fused evidence candidates."""

    def score(self, query: str, excerpts: list[str]) -> list[float]: ...


class TokenOverlapReranker:
    """Dependency-free local reranker suitable for tests and local fallback use."""

    def score(self, query: str, excerpts: list[str]) -> list[float]:
        query_tokens = _tokens(query)
        if not query_tokens:
            return [0.0 for _ in excerpts]
        return [len(query_tokens & _tokens(excerpt)) / len(query_tokens) for excerpt in excerpts]


def select_candidates_for_verification(
    ranked_candidates: list[EvidenceCandidate],
    *,
    limit: int,
) -> list[EvidenceCandidate]:
    """Apply the configured cost boundary before hosted verification."""

    if limit < 1:
        raise ValueError("verification candidate limit must be at least one")
    return ranked_candidates[:limit]


def rerank_candidates(
    query: str,
    candidates: list[EvidenceCandidate],
    *,
    reranker: LocalReranker,
) -> list[EvidenceCandidate]:
    """Score fused candidates locally and return a deterministic ranking."""

    if not candidates:
        return []

    scores = reranker.score(query, [candidate.excerpt for candidate in candidates])
    if len(scores) != len(candidates):
        raise ValueError("reranker must return one score per candidate")

    scored = [
        candidate.model_copy(
            update={
                "retrieval_scores": RetrievalScores.model_validate(
                    {
                        **candidate.retrieval_scores.model_dump(),
                        "rerank": score,
                    }
                )
            }
        )
        for candidate, score in zip(candidates, scores, strict=True)
    ]
    return sorted(
        scored,
        key=lambda candidate: (
            -float(candidate.retrieval_scores.rerank or 0.0),
            candidate.candidate_id,
        ),
    )


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.casefold()))
