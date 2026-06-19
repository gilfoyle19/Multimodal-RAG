import json
import shutil
import sqlite3
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest

from multimodal_rag.hybrid_retrieval import retrieve_hybrid
from multimodal_rag.keyword_indexing import KeywordSearchResult
from multimodal_rag.storage import connect_sqlite, initialize_sqlite_database
from multimodal_rag.vector_indexing import VectorSearchResult


@pytest.fixture
def local_runtime_path() -> Generator[Path]:
    runtime_path = Path("data") / "test-hybrid-retrieval" / uuid.uuid4().hex
    runtime_path.mkdir(parents=True, exist_ok=True)
    try:
        yield runtime_path
    finally:
        shutil.rmtree(runtime_path, ignore_errors=True)


def _connection(local_runtime_path: Path) -> sqlite3.Connection:
    sqlite_path = local_runtime_path / "metadata.sqlite3"
    initialize_sqlite_database(sqlite_path)
    connection = connect_sqlite(sqlite_path)
    connection.execute(
        """
        INSERT INTO documents (
            document_id, title, source_path, content_hash, ingestion_status
        ) VALUES ('manual', 'Pump Manual', 'database/manual.pdf', 'sha256:manual', 'indexed')
        """
    )
    connection.execute(
        """
        INSERT INTO pages (page_id, document_id, page_number)
        VALUES ('page-1', 'manual', 3)
        """
    )
    connection.execute(
        """
        INSERT INTO source_elements (
            source_element_id, document_id, page_id, source_type, page_number,
            citation_key, section_path_json, label, content
        ) VALUES (?, 'manual', 'page-1', 'table', 3, ?, ?, ?, ?)
        """,
        (
            "source-fault-table",
            "manual:p3:table:1",
            json.dumps(["Troubleshooting", "Fault codes"]),
            "Fault table",
            "E12 | Check coolant flow",
        ),
    )
    connection.execute(
        """
        INSERT INTO source_elements (
            source_element_id, document_id, page_id, source_type, page_number,
            citation_key, section_path_json, label, content
        ) VALUES (?, 'manual', 'page-1', 'table_row_helper', 3, ?, ?, ?, ?)
        """,
        (
            "source-row-helper",
            "manual:p3:table-row:1",
            json.dumps(["Troubleshooting", "Fault codes"]),
            "Fault E12",
            "E12 | Check coolant flow",
        ),
    )
    connection.execute(
        """
        INSERT INTO source_elements (
            source_element_id, document_id, page_id, source_type, page_number,
            citation_key, section_path_json, label, content
        ) VALUES (?, 'manual', 'page-1', 'spec', 3, ?, ?, ?, ?)
        """,
        (
            "source-spec",
            "manual:p3:spec:1",
            json.dumps(["Specifications"]),
            "Operating pressure",
            "Maximum pressure is 10 bar.",
        ),
    )
    connection.commit()
    return connection


def test_keyword_only_hit_becomes_ranked_evidence_candidate(
    local_runtime_path: Path,
) -> None:
    connection = _connection(local_runtime_path)
    keyword_hits = [
        KeywordSearchResult(
            chunk_id="chunk-spec",
            source_element_id="source-spec",
            parent_source_element_id=None,
            document_id="manual",
            chunk_kind="source_element",
            excerpt="Maximum pressure is 10 bar.",
            score=0.8,
        )
    ]

    candidates = retrieve_hybrid(connection, vector_results=[], keyword_results=keyword_hits)

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.chunk_id == "chunk-spec"
    assert candidate.source_element_id == "source-spec"
    assert candidate.citation.page_number == 3
    assert candidate.citation.citation_key == "manual:p3:spec:1"
    assert candidate.retrieval_scores.vector is None
    assert candidate.retrieval_scores.keyword == 0.8
    assert candidate.retrieval_scores.rrf == 1 / 61


def test_vector_only_hit_preserves_vector_score(local_runtime_path: Path) -> None:
    connection = _connection(local_runtime_path)
    vector_hits = [
        VectorSearchResult(
            chunk_id="chunk-spec",
            source_element_id="source-spec",
            parent_source_element_id=None,
            document_id="manual",
            chunk_kind="source_element",
            excerpt="Maximum pressure is 10 bar.",
            score=0.9,
        )
    ]

    candidates = retrieve_hybrid(connection, vector_results=vector_hits, keyword_results=[])

    assert [candidate.chunk_id for candidate in candidates] == ["chunk-spec"]
    assert candidates[0].retrieval_scores.vector == 0.9
    assert candidates[0].retrieval_scores.keyword is None


def test_overlapping_hits_are_boosted(
    local_runtime_path: Path,
) -> None:
    connection = _connection(local_runtime_path)
    vector_hits = [
        VectorSearchResult(
            chunk_id="chunk-spec",
            source_element_id="source-spec",
            parent_source_element_id=None,
            document_id="manual",
            chunk_kind="source_element",
            excerpt="Maximum pressure is 10 bar.",
            score=0.9,
        ),
        VectorSearchResult(
            chunk_id="chunk-fault",
            source_element_id="source-fault-table",
            parent_source_element_id=None,
            document_id="manual",
            chunk_kind="source_element",
            excerpt="E12 | Check coolant flow",
            score=0.8,
        ),
    ]
    keyword_hits = [
        KeywordSearchResult(
            chunk_id="chunk-spec",
            source_element_id="source-spec",
            parent_source_element_id=None,
            document_id="manual",
            chunk_kind="source_element",
            excerpt="Maximum pressure is 10 bar.",
            score=0.7,
        )
    ]

    candidates = retrieve_hybrid(
        connection,
        vector_results=vector_hits,
        keyword_results=keyword_hits,
    )

    assert [candidate.chunk_id for candidate in candidates] == ["chunk-spec", "chunk-fault"]
    assert candidates[0].retrieval_scores.rrf == 2 / 61
    assert candidates[0].retrieval_scores.vector == 0.9
    assert candidates[0].retrieval_scores.keyword == 0.7


def test_equal_rrf_scores_are_ordered_by_chunk_id(local_runtime_path: Path) -> None:
    connection = _connection(local_runtime_path)
    vector_hits = [
        VectorSearchResult(
            chunk_id="chunk-spec",
            source_element_id="source-spec",
            parent_source_element_id=None,
            document_id="manual",
            chunk_kind="source_element",
            excerpt="Maximum pressure is 10 bar.",
            score=0.9,
        ),
        VectorSearchResult(
            chunk_id="chunk-fault",
            source_element_id="source-fault-table",
            parent_source_element_id=None,
            document_id="manual",
            chunk_kind="source_element",
            excerpt="E12 | Check coolant flow",
            score=0.8,
        ),
    ]
    keyword_hits = [
        KeywordSearchResult(
            chunk_id="chunk-fault",
            source_element_id="source-fault-table",
            parent_source_element_id=None,
            document_id="manual",
            chunk_kind="source_element",
            excerpt="E12 | Check coolant flow",
            score=0.7,
        ),
        KeywordSearchResult(
            chunk_id="chunk-spec",
            source_element_id="source-spec",
            parent_source_element_id=None,
            document_id="manual",
            chunk_kind="source_element",
            excerpt="Maximum pressure is 10 bar.",
            score=0.6,
        ),
    ]

    candidates = retrieve_hybrid(
        connection,
        vector_results=vector_hits,
        keyword_results=keyword_hits,
    )

    assert candidates[0].retrieval_scores.rrf == candidates[1].retrieval_scores.rrf
    assert [candidate.chunk_id for candidate in candidates] == ["chunk-fault", "chunk-spec"]


def test_empty_results_return_no_candidates(local_runtime_path: Path) -> None:
    connection = _connection(local_runtime_path)

    assert retrieve_hybrid(connection, vector_results=[], keyword_results=[]) == []


def test_hits_from_non_indexed_documents_are_excluded(local_runtime_path: Path) -> None:
    connection = _connection(local_runtime_path)
    connection.execute("UPDATE documents SET ingestion_status = 'failed'")
    connection.commit()
    keyword_hits = [
        KeywordSearchResult(
            chunk_id="chunk-spec",
            source_element_id="source-spec",
            parent_source_element_id=None,
            document_id="manual",
            chunk_kind="source_element",
            excerpt="Maximum pressure is 10 bar.",
            score=0.8,
        )
    ]

    assert retrieve_hybrid(connection, vector_results=[], keyword_results=keyword_hits) == []


def test_table_row_helper_maps_to_parent_fault_table(local_runtime_path: Path) -> None:
    connection = _connection(local_runtime_path)
    keyword_hits = [
        KeywordSearchResult(
            chunk_id="chunk-fault-row",
            source_element_id="source-row-helper",
            parent_source_element_id="source-fault-table",
            document_id="manual",
            chunk_kind="table_row_helper",
            excerpt="E12 | Check coolant flow",
            score=0.95,
        )
    ]

    candidates = retrieve_hybrid(connection, vector_results=[], keyword_results=keyword_hits)

    assert candidates[0].source_element_id == "source-fault-table"
    assert candidates[0].parent_source_element_id == "source-fault-table"
    assert candidates[0].citation.citation_key == "manual:p3:table:1"
