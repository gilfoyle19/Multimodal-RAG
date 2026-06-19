import json
import shutil
import sqlite3
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest

from multimodal_rag.storage import connect_sqlite, initialize_sqlite_database
from multimodal_rag.vector_indexing import (
    VectorEmbeddingInput,
    rebuild_vector_index_for_document,
    search_vector_index,
)


class FakeEmbeddingAdapter:
    def embed_texts(self, inputs: list[VectorEmbeddingInput]) -> list[list[float]]:
        return [_embedding_for_text(input_.text) for input_ in inputs]


@pytest.fixture
def local_runtime_path() -> Generator[Path]:
    runtime_path = Path("data") / "test-vector-indexing" / uuid.uuid4().hex
    runtime_path.mkdir(parents=True, exist_ok=True)
    try:
        yield runtime_path
    finally:
        shutil.rmtree(runtime_path, ignore_errors=True)


def _insert_document_with_chunks(connection: sqlite3.Connection, document_id: str) -> None:
    connection.execute(
        """
        INSERT INTO documents (
            document_id, title, source_path, content_hash, ingestion_status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            document_id,
            "Pump Fault Manual",
            f"database/{document_id}.pdf",
            f"sha256:{document_id}",
            "indexed",
        ),
    )
    connection.execute(
        """
        INSERT INTO pages (page_id, document_id, page_number, width_points, height_points)
        VALUES (?, ?, ?, ?, ?)
        """,
        (f"{document_id}:page:0001", document_id, 1, 300.0, 400.0),
    )
    connection.execute(
        """
        INSERT INTO source_elements (
            source_element_id, document_id, page_id, source_type, page_number,
            citation_key, section_path_json, label, content, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"{document_id}:source:text:0001:0001",
            document_id,
            f"{document_id}:page:0001",
            "text",
            1,
            f"{document_id}:p1:text:0001",
            json.dumps(["Troubleshooting"], sort_keys=True),
            "Reset Procedure",
            "Press reset for five seconds.",
            json.dumps({"equipment": "pump"}, sort_keys=True),
        ),
    )
    connection.execute(
        """
        INSERT INTO chunks (
            chunk_id, source_element_id, chunk_kind, searchable_text, metadata_json
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            f"{document_id}:chunk:text:0001:0001",
            f"{document_id}:source:text:0001:0001",
            "source_element",
            "Press reset for five seconds.",
            json.dumps({"equipment": "pump"}, sort_keys=True),
        ),
    )
    connection.execute(
        """
        INSERT INTO source_elements (
            source_element_id, document_id, page_id, source_type, page_number,
            citation_key, section_path_json, label, content, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"{document_id}:source:table:0001:0001",
            document_id,
            f"{document_id}:page:0001",
            "table",
            1,
            f"{document_id}:p1:table:0001",
            json.dumps([], sort_keys=True),
            "Fault Code Table",
            "Code | Action\nE12 | Check coolant",
            json.dumps({"table_kind": "faults"}, sort_keys=True),
        ),
    )
    connection.execute(
        """
        INSERT INTO chunks (
            chunk_id, source_element_id, chunk_kind, searchable_text,
            parent_source_element_id, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            f"{document_id}:chunk:table-row:0001:0001:0002",
            f"{document_id}:source:table:0001:0001",
            "table_row_helper",
            "Code: E12 | Action: Check coolant",
            f"{document_id}:source:table:0001:0001",
            json.dumps({"helper_kind": "table_row"}, sort_keys=True),
        ),
    )
    connection.execute(
        """
        INSERT INTO chunks (
            chunk_id, source_element_id, chunk_kind, searchable_text, metadata_json
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            f"{document_id}:chunk:table:0001:0001",
            f"{document_id}:source:table:0001:0001",
            "source_element",
            "Code | Action\nE12 | Check coolant",
            json.dumps({"table_kind": "faults"}, sort_keys=True),
        ),
    )
    connection.execute(
        """
        INSERT INTO source_elements (
            source_element_id, document_id, page_id, source_type, page_number,
            citation_key, section_path_json, label, content, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"{document_id}:source:text:0001:0002",
            document_id,
            f"{document_id}:page:0001",
            "text",
            1,
            f"{document_id}:p1:text:0002",
            json.dumps([], sort_keys=True),
            "Other",
            "Unrelated lubrication guidance.",
            json.dumps({}, sort_keys=True),
        ),
    )
    connection.execute(
        """
        INSERT INTO chunks (
            chunk_id, source_element_id, chunk_kind, searchable_text, metadata_json
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            f"{document_id}:chunk:text:0001:0002",
            f"{document_id}:source:text:0001:0002",
            "source_element",
            "Unrelated lubrication guidance.",
            json.dumps({}, sort_keys=True),
        ),
    )
    connection.commit()


def test_vector_index_persists_chunk_ids_and_maps_back_to_sqlite_sources(
    local_runtime_path: Path,
) -> None:
    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    chroma_path = local_runtime_path / "data" / "chroma"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        _insert_document_with_chunks(connection, "doc_pump")

        indexed_count = rebuild_vector_index_for_document(
            connection,
            "doc_pump",
            chroma_path,
            FakeEmbeddingAdapter(),
        )
        results = search_vector_index(
            chroma_path,
            FakeEmbeddingAdapter(),
            "E12 coolant",
            limit=2,
        )

    assert indexed_count == 4
    assert chroma_path.exists()
    assert [result.chunk_id for result in results] == [
        "doc_pump:chunk:table-row:0001:0001:0002",
        "doc_pump:chunk:table:0001:0001",
    ]
    assert {result.source_element_id for result in results} == {
        "doc_pump:source:table:0001:0001"
    }
    assert results[0].parent_source_element_id == "doc_pump:source:table:0001:0001"
    assert results[0].document_id == "doc_pump"
    assert results[0].chunk_kind == "table_row_helper"


def test_rebuilding_vector_index_for_changed_document_removes_stale_entries(
    local_runtime_path: Path,
) -> None:
    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    chroma_path = local_runtime_path / "data" / "chroma"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        _insert_document_with_chunks(connection, "doc_pump")
        rebuild_vector_index_for_document(
            connection,
            "doc_pump",
            chroma_path,
            FakeEmbeddingAdapter(),
        )

        connection.execute(
            """
            UPDATE chunks
            SET searchable_text = ?
            WHERE chunk_id = ?
            """,
            ("Code: E12 | Action: Replace filter", "doc_pump:chunk:table-row:0001:0001:0002"),
        )
        connection.execute(
            """
            DELETE FROM chunks
            WHERE chunk_id = ?
            """,
            ("doc_pump:chunk:table:0001:0001",),
        )
        connection.commit()

        indexed_count = rebuild_vector_index_for_document(
            connection,
            "doc_pump",
            chroma_path,
            FakeEmbeddingAdapter(),
        )
        stale_results = search_vector_index(
            chroma_path,
            FakeEmbeddingAdapter(),
            "coolant",
            limit=4,
        )
        updated_results = search_vector_index(
            chroma_path,
            FakeEmbeddingAdapter(),
            "replace filter",
            limit=4,
        )

    assert indexed_count == 3
    assert "doc_pump:chunk:table:0001:0001" not in {
        result.chunk_id for result in stale_results
    }
    assert updated_results[0].chunk_id == "doc_pump:chunk:table-row:0001:0001:0002"
    assert "doc_pump:chunk:table:0001:0001" not in {
        result.chunk_id for result in updated_results
    }


def _embedding_for_text(text: str) -> list[float]:
    normalized = text.lower()
    return [
        1.0 if "e12" in normalized else 0.0,
        1.0 if "coolant" in normalized else 0.0,
        1.0 if "replace" in normalized or "filter" in normalized else 0.0,
        1.0 if "reset" in normalized else 0.0,
    ]
