import json
import shutil
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest

from multimodal_rag.discovery import discover_document_candidates
from multimodal_rag.ingestion_status import (
    list_queryable_document_ids,
    mark_document_ingestion_failed,
    mark_document_ingestion_indexed,
    mark_document_ingestion_indexing,
)
from multimodal_rag.keyword_indexing import rebuild_keyword_index_for_document, search_keyword_index
from multimodal_rag.storage import connect_sqlite, initialize_sqlite_database


@pytest.fixture
def local_runtime_path() -> Generator[Path]:
    runtime_path = Path("data") / "test-discovery" / uuid.uuid4().hex
    runtime_path.mkdir(parents=True, exist_ok=True)
    try:
        yield runtime_path
    finally:
        shutil.rmtree(runtime_path, ignore_errors=True)


def test_discovery_records_pdf_without_sidecar(local_runtime_path: Path) -> None:
    database_path = local_runtime_path / "database"
    database_path.mkdir()
    pdf_path = database_path / "pump-manual.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n% test fixture\n")

    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        discovered = discover_document_candidates(database_path, connection)
        page_count = connection.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
        source_count = connection.execute("SELECT COUNT(*) FROM source_elements").fetchone()[0]
        chunk_count = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        row = connection.execute("SELECT * FROM documents").fetchone()

    assert len(discovered) == 1
    assert discovered[0].title == "pump-manual"
    assert discovered[0].source_path == str(pdf_path)
    assert discovered[0].provenance == {}
    assert discovered[0].ingestion_status == "discovered"
    assert row["title"] == "pump-manual"
    assert row["source_path"] == str(pdf_path)
    assert row["content_hash"].startswith("sha256:")
    assert json.loads(row["provenance_json"]) == {}
    assert row["ingestion_status"] == "discovered"
    assert page_count == 0
    assert source_count == 0
    assert chunk_count == 0


def test_discovery_parses_matching_metadata_sidecar(local_runtime_path: Path) -> None:
    database_path = local_runtime_path / "database"
    database_path.mkdir()
    pdf_path = database_path / "compressor-service.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n% service fixture\n")
    pdf_path.with_suffix(".json").write_text(
        json.dumps(
            {
                "title": "Compressor Service Manual",
                "publisher": "Example Industrial",
                "revision": "A",
            }
        ),
        encoding="utf-8",
    )

    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        discovered = discover_document_candidates(database_path, connection)
        row = connection.execute("SELECT * FROM documents").fetchone()

    assert len(discovered) == 1
    assert discovered[0].title == "Compressor Service Manual"
    assert discovered[0].provenance == {
        "title": "Compressor Service Manual",
        "publisher": "Example Industrial",
        "revision": "A",
    }
    assert row["title"] == "Compressor Service Manual"
    assert json.loads(row["provenance_json"]) == discovered[0].provenance


def test_discovery_finds_pdfs_under_configured_database_path(local_runtime_path: Path) -> None:
    database_path = local_runtime_path / "configured-manuals"
    nested_path = database_path / "assets" / "line-a"
    nested_path.mkdir(parents=True)
    first_pdf_path = database_path / "pump.pdf"
    second_pdf_path = nested_path / "valve.PDF"
    first_pdf_path.write_bytes(b"%PDF-1.7\n% pump\n")
    second_pdf_path.write_bytes(b"%PDF-1.7\n% valve\n")
    (database_path / "notes.txt").write_text("not a PDF", encoding="utf-8")

    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        discovered = discover_document_candidates(database_path, connection)
        persisted_count = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]

    assert {candidate.title for candidate in discovered} == {"pump", "valve"}
    assert {candidate.source_path for candidate in discovered} == {
        str(first_pdf_path),
        str(second_pdf_path),
    }
    assert persisted_count == 2


def test_discovery_skips_unchanged_indexed_pdf(local_runtime_path: Path) -> None:
    database_path = local_runtime_path / "database"
    database_path.mkdir()
    pdf_path = database_path / "pump.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n% pump\n")

    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        discovered = discover_document_candidates(database_path, connection)
        document_id = discovered[0].document_id
        mark_document_ingestion_indexed(connection, document_id)

        rediscovered = discover_document_candidates(database_path, connection)
        row = connection.execute(
            "SELECT ingestion_status FROM documents WHERE document_id = ?",
            (document_id,),
        ).fetchone()

    assert rediscovered[0].ingestion_status == "skipped"
    assert row["ingestion_status"] == "skipped"


def test_discovery_marks_changed_pdf_for_clean_reindexing(local_runtime_path: Path) -> None:
    database_path = local_runtime_path / "database"
    database_path.mkdir()
    pdf_path = database_path / "pump.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n% first revision\n")

    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        discovered = discover_document_candidates(database_path, connection)
        document_id = discovered[0].document_id
        mark_document_ingestion_indexed(connection, document_id)
        connection.execute(
            """
            INSERT INTO pages (page_id, document_id, page_number)
            VALUES (?, ?, ?)
            """,
            ("page_pump_0001", document_id, 1),
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
                "source_pump_0001",
                document_id,
                "page_pump_0001",
                "text",
                1,
                f"{document_id}:p1:text:0001",
                json.dumps([], sort_keys=True),
                "Pump Text",
                "Old coolant guidance.",
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
                "chunk_pump_0001",
                "source_pump_0001",
                "source_element",
                "Old coolant guidance.",
                json.dumps({}, sort_keys=True),
            ),
        )
        connection.commit()
        rebuild_keyword_index_for_document(connection, document_id)

        pdf_path.write_bytes(b"%PDF-1.7\n% second revision\n")
        rediscovered = discover_document_candidates(database_path, connection)
        row = connection.execute(
            "SELECT content_hash, ingestion_status FROM documents WHERE document_id = ?",
            (document_id,),
        ).fetchone()
        page_count = connection.execute(
            "SELECT COUNT(*) FROM pages WHERE document_id = ?",
            (document_id,),
        ).fetchone()[0]
        stale_keyword_results = search_keyword_index(connection, "coolant")

    assert rediscovered[0].ingestion_status == "discovered"
    assert row["content_hash"] == rediscovered[0].content_hash
    assert row["ingestion_status"] == "discovered"
    assert page_count == 0
    assert stale_keyword_results == []


def test_ingestion_status_helpers_record_visible_states(local_runtime_path: Path) -> None:
    database_path = local_runtime_path / "database"
    database_path.mkdir()
    pdf_path = database_path / "pump.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n% pump\n")

    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        discovered = discover_document_candidates(database_path, connection)
        document_id = discovered[0].document_id

        mark_document_ingestion_indexing(connection, document_id)
        indexing_status = connection.execute(
            "SELECT ingestion_status FROM documents WHERE document_id = ?",
            (document_id,),
        ).fetchone()["ingestion_status"]

        mark_document_ingestion_failed(connection, document_id)
        failed_status = connection.execute(
            "SELECT ingestion_status FROM documents WHERE document_id = ?",
            (document_id,),
        ).fetchone()["ingestion_status"]

        mark_document_ingestion_indexed(connection, document_id)
        indexed_status = connection.execute(
            "SELECT ingestion_status FROM documents WHERE document_id = ?",
            (document_id,),
        ).fetchone()["ingestion_status"]
        queryable_ids = list_queryable_document_ids(connection)

    assert indexing_status == "indexing"
    assert failed_status == "failed"
    assert indexed_status == "indexed"
    assert queryable_ids == [document_id]
