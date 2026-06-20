import json
import sqlite3
from typing import cast

from multimodal_rag.contracts import (
    EvidenceCandidate,
    RetrievalCandidate,
    RetrievalResponse,
    SourceElementType,
)
from multimodal_rag.hybrid_retrieval import retrieve_hybrid
from multimodal_rag.keyword_indexing import search_keyword_index
from multimodal_rag.local_reranking import TokenOverlapReranker, rerank_candidates
from multimodal_rag.settings import AppSettings
from multimodal_rag.storage import connect_sqlite
from multimodal_rag.vector_indexing import OpenAIEmbeddingAdapter, search_vector_index


class RetrievalInspectionService:
    """Run retrieval and expose its ranking metadata without generation."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def retrieve(self, query: str) -> RetrievalResponse:
        settings = self._settings
        with connect_sqlite(settings.sqlite_path) as connection:
            keyword_results = search_keyword_index(
                connection,
                query,
                limit=settings.keyword_candidate_limit,
            )
            vector_results = []
            if settings.openai_api_key is not None:
                vector_results = search_vector_index(
                    settings.chroma_path,
                    OpenAIEmbeddingAdapter(
                        settings.openai_api_key.get_secret_value(),
                        settings.openai_embedding_model,
                    ),
                    query,
                    limit=settings.vector_candidate_limit,
                )
            fused = retrieve_hybrid(
                connection,
                vector_results=vector_results,
                keyword_results=keyword_results,
                limit=settings.retrieval_candidate_limit,
            )
            ranked = rerank_candidates(
                query,
                fused[: settings.rerank_candidate_limit],
                reranker=TokenOverlapReranker(),
            )
            candidates = [
                _inspect_candidate(connection, candidate, rank)
                for rank, candidate in enumerate(ranked, start=1)
            ]
        return RetrievalResponse(query=query, candidates=candidates)


def _inspect_candidate(
    connection: sqlite3.Connection,
    candidate: EvidenceCandidate,
    rank: int,
) -> RetrievalCandidate:
    row = connection.execute(
        """
        SELECT
            documents.title AS document_title,
            source_elements.source_type,
            source_elements.section_path_json,
            source_elements.label
        FROM source_elements
        JOIN documents USING (document_id)
        WHERE source_elements.source_element_id = ?
        """,
        (candidate.source_element_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"retrieval candidate source is missing: {candidate.source_element_id}")
    channels = [
        channel
        for channel in ("vector", "keyword")
        if getattr(candidate.retrieval_scores, channel) is not None
    ]
    matched = " and ".join(channels) or "fused"
    rerank_score = candidate.retrieval_scores.rerank or 0.0
    return RetrievalCandidate(
        rank=rank,
        candidate_id=candidate.candidate_id,
        chunk_id=candidate.chunk_id,
        source_element_id=candidate.source_element_id,
        chunk_kind=candidate.chunk_kind,
        parent_source_element_id=candidate.parent_source_element_id,
        citation=candidate.citation,
        document_title=cast(str, row["document_title"]),
        section_path=cast(list[str], json.loads(row["section_path_json"])),
        source_type=SourceElementType(cast(str, row["source_type"])),
        label=cast(str | None, row["label"]),
        excerpt=candidate.excerpt,
        retrieval_scores=candidate.retrieval_scores,
        relevance_reason=(
            f"Matched {matched} search; local rerank score {rerank_score:.3f}."
        ),
    )
