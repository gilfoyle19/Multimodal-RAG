import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, cast

from multimodal_rag.contracts import (
    ChunkKind,
    CitationIdentity,
    EvidenceCandidate,
    RetrievalScores,
)
from multimodal_rag.keyword_indexing import KeywordSearchResult
from multimodal_rag.vector_indexing import VectorSearchResult


RRF_RANK_CONSTANT = 60


@dataclass
class _FusedHit:
    chunk_id: str
    source_element_id: str
    parent_source_element_id: str | None
    document_id: str
    chunk_kind: str
    excerpt: str
    vector_score: float | None = None
    keyword_score: float | None = None
    rrf_score: float = 0.0


class _RankedSearchResult(Protocol):
    @property
    def chunk_id(self) -> str: ...

    @property
    def source_element_id(self) -> str: ...

    @property
    def parent_source_element_id(self) -> str | None: ...

    @property
    def document_id(self) -> str: ...

    @property
    def chunk_kind(self) -> str: ...

    @property
    def excerpt(self) -> str: ...

    @property
    def score(self) -> float: ...


def retrieve_hybrid(
    connection: sqlite3.Connection,
    *,
    vector_results: Sequence[VectorSearchResult],
    keyword_results: Sequence[KeywordSearchResult],
    limit: int = 10,
) -> list[EvidenceCandidate]:
    """Fuse ranked vector and keyword hits into citeable evidence candidates."""

    fused: dict[str, _FusedHit] = {}
    _add_ranked_hits(fused, vector_results, channel="vector")
    _add_ranked_hits(fused, keyword_results, channel="keyword")

    ranked_hits = sorted(fused.values(), key=lambda hit: (-hit.rrf_score, hit.chunk_id))
    candidates: list[EvidenceCandidate] = []
    for hit in ranked_hits:
        row = connection.execute(
            """
            SELECT
                source_elements.source_element_id,
                source_elements.page_id,
                source_elements.page_number,
                source_elements.citation_key
            FROM source_elements
            JOIN documents USING (document_id)
            WHERE source_elements.source_element_id = ?
              AND documents.document_id = ?
              AND documents.ingestion_status = 'indexed'
            """,
            (hit.parent_source_element_id or hit.source_element_id, hit.document_id),
        ).fetchone()
        if row is None:
            continue

        source_element_id = cast(str, row["source_element_id"])
        citation = CitationIdentity(
            document_id=hit.document_id,
            page_id=cast(str, row["page_id"]),
            source_element_id=source_element_id,
            page_number=cast(int, row["page_number"]),
            citation_key=cast(str, row["citation_key"]),
        )
        candidates.append(
            EvidenceCandidate(
                candidate_id=f"candidate:{hit.chunk_id}",
                chunk_id=hit.chunk_id,
                source_element_id=source_element_id,
                chunk_kind=ChunkKind(hit.chunk_kind),
                parent_source_element_id=hit.parent_source_element_id,
                citation=citation,
                excerpt=hit.excerpt,
                retrieval_scores=RetrievalScores(
                    vector=hit.vector_score,
                    keyword=hit.keyword_score,
                    rrf=hit.rrf_score,
                ),
            )
        )
        if len(candidates) == limit:
            break
    return candidates


def _add_ranked_hits(
    fused: dict[str, _FusedHit],
    results: Sequence[_RankedSearchResult],
    *,
    channel: str,
) -> None:
    for rank, result in enumerate(results, start=1):
        hit = fused.setdefault(
            result.chunk_id,
            _FusedHit(
                chunk_id=result.chunk_id,
                source_element_id=result.source_element_id,
                parent_source_element_id=result.parent_source_element_id,
                document_id=result.document_id,
                chunk_kind=result.chunk_kind,
                excerpt=result.excerpt,
            ),
        )
        hit.rrf_score += 1.0 / (RRF_RANK_CONSTANT + rank)
        if channel == "vector":
            hit.vector_score = result.score
        else:
            hit.keyword_score = result.score
