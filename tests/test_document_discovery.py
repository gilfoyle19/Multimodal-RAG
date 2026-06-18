import json
import shutil
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest

from multimodal_rag.discovery import discover_document_candidates
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
