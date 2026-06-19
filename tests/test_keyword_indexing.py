import json
import shutil
import sqlite3
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest

from multimodal_rag.keyword_indexing import (
    rebuild_keyword_index_for_document,
    search_keyword_index,
)
from multimodal_rag.storage import connect_sqlite, initialize_sqlite_database


@pytest.fixture
def local_runtime_path() -> Generator[Path]:
    runtime_path = Path("data") / "test-keyword-indexing" / uuid.uuid4().hex
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
            f"{document_id}:source:figure:0001:0001",
            document_id,
            f"{document_id}:page:0001",
            "figure",
            1,
            f"{document_id}:p1:figure:0001",
            json.dumps([], sort_keys=True),
            "Figure 1",
            "",
            json.dumps({"preview_type": "figure"}, sort_keys=True),
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
            f"{document_id}:chunk:figure-caption:0001:0001",
            f"{document_id}:source:figure:0001:0001",
            "figure_caption",
            "Pump seal orientation diagram.",
            f"{document_id}:source:figure:0001:0001",
            json.dumps({"caption_role": "generated_search_metadata"}, sort_keys=True),
        ),
    )
    connection.execute(
        """
        INSERT INTO documents (
            document_id, title, source_path, content_hash, ingestion_status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("doc_other", "Other Manual", "database/other.pdf", "sha256:other", "indexed"),
    )
    connection.execute(
        """
        INSERT INTO pages (page_id, document_id, page_number, width_points, height_points)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("doc_other:page:0001", "doc_other", 1, 300.0, 400.0),
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
            "doc_other:source:text:0001:0001",
            "doc_other",
            "doc_other:page:0001",
            "text",
            1,
            "doc_other:p1:text:0001",
            json.dumps([], sort_keys=True),
            "Other",
            "E12 belongs to another document.",
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
            "doc_other:chunk:text:0001:0001",
            "doc_other:source:text:0001:0001",
            "source_element",
            "E12 belongs to another document.",
            json.dumps({}, sort_keys=True),
        ),
    )
    connection.commit()


def test_keyword_index_matches_chunks_and_maps_back_to_source_elements(
    local_runtime_path: Path,
) -> None:
    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        _insert_document_with_chunks(connection, "doc_pump")

        indexed_count = rebuild_keyword_index_for_document(connection, "doc_pump")
        e12_results = search_keyword_index(connection, "E12 coolant")
        figure_results = search_keyword_index(connection, "orientation diagram")
        label_results = search_keyword_index(connection, "fault code")

    assert indexed_count == 4
    assert {result.chunk_id for result in e12_results} == {
        "doc_pump:chunk:table:0001:0001",
        "doc_pump:chunk:table-row:0001:0001:0002",
    }
    assert {result.source_element_id for result in e12_results} == {
        "doc_pump:source:table:0001:0001"
    }
    row_helper = next(
        result
        for result in e12_results
        if result.chunk_id == "doc_pump:chunk:table-row:0001:0001:0002"
    )
    assert row_helper.parent_source_element_id == "doc_pump:source:table:0001:0001"
    assert row_helper.chunk_kind == "table_row_helper"
    assert row_helper.document_id == "doc_pump"
    assert [result.chunk_id for result in figure_results] == [
        "doc_pump:chunk:figure-caption:0001:0001"
    ]
    assert {result.source_element_id for result in label_results} == {
        "doc_pump:source:table:0001:0001"
    }


def test_rebuilding_keyword_index_for_changed_document_removes_stale_entries(
    local_runtime_path: Path,
) -> None:
    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        _insert_document_with_chunks(connection, "doc_pump")
        rebuild_keyword_index_for_document(connection, "doc_pump")

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
            UPDATE chunks
            SET searchable_text = ?
            WHERE chunk_id = ?
            """,
            ("Code | Action\nE12 | Replace filter", "doc_pump:chunk:table:0001:0001"),
        )
        connection.commit()

        rebuild_keyword_index_for_document(connection, "doc_pump")
        stale_results = search_keyword_index(connection, "coolant")
        updated_results = search_keyword_index(connection, "replace filter")

    assert stale_results == []
    assert {result.chunk_id for result in updated_results} == {
        "doc_pump:chunk:table:0001:0001",
        "doc_pump:chunk:table-row:0001:0001:0002",
    }
