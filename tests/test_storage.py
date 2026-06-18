import json
import shutil
import sqlite3
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest

from multimodal_rag.storage import connect_sqlite, initialize_sqlite_database


@pytest.fixture
def local_runtime_path() -> Generator[Path]:
    runtime_path = Path("data") / "test-runtime" / uuid.uuid4().hex
    runtime_path.mkdir(parents=True, exist_ok=True)
    try:
        yield runtime_path
    finally:
        shutil.rmtree(runtime_path, ignore_errors=True)


def test_sqlite_bootstrap_creates_deterministic_schema(local_runtime_path: Path) -> None:
    sqlite_path = local_runtime_path / "runtime" / "app.sqlite3"

    initialize_sqlite_database(sqlite_path)
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        table_names = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        foreign_keys_enabled = connection.execute("PRAGMA foreign_keys").fetchone()[0]
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]

    assert sqlite_path.exists()
    assert sqlite_path.parent == local_runtime_path / "runtime"
    assert foreign_keys_enabled == 1
    assert journal_mode == "wal"
    assert table_names == {
        "ask_traces",
        "chunks",
        "documents",
        "evaluation_cases",
        "openai_cache_entries",
        "pages",
        "schema_migrations",
        "source_elements",
    }


def test_sqlite_persists_core_metadata_relationships(local_runtime_path: Path) -> None:
    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        connection.execute(
            """
            INSERT INTO documents (
                document_id, title, source_path, content_hash, provenance_json
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "doc_manual_a",
                "Pump Manual",
                "database/pump-manual.pdf",
                "sha256:manual-a",
                json.dumps({"publisher": "Example Co"}, sort_keys=True),
            ),
        )
        connection.execute(
            """
            INSERT INTO pages (page_id, document_id, page_number, width_points, height_points)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("page_manual_a_0001", "doc_manual_a", 1, 612.0, 792.0),
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
                "src_manual_a_warning_0001",
                "doc_manual_a",
                "page_manual_a_0001",
                "warning",
                1,
                "doc_manual_a:p1:warning:0001",
                json.dumps(["Safety"], sort_keys=True),
                "Warning 1",
                "Disconnect power before opening the panel.",
                json.dumps({}, sort_keys=True),
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
                "chunk_manual_a_warning_0001",
                "src_manual_a_warning_0001",
                "source_element",
                "Disconnect power before opening the panel.",
                None,
                json.dumps({}, sort_keys=True),
            ),
        )
        connection.execute(
            """
            INSERT INTO openai_cache_entries (
                cache_key, input_hash, model, prompt_version, schema_version,
                response_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "caption:hash:model:v1:v1",
                "sha256:caption-input",
                "gpt-4.1-mini",
                "caption-v1",
                "v1",
                json.dumps({"caption": "A warning label."}, sort_keys=True),
            ),
        )
        connection.execute(
            """
            INSERT INTO evaluation_cases (
                case_id, question, expected_status, fixture_json
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "eval_warning_001",
                "What should I do before opening the panel?",
                "grounded",
                json.dumps({"required_answer_points": ["Disconnect power"]}, sort_keys=True),
            ),
        )
        connection.execute(
            """
            INSERT INTO ask_traces (
                trace_id, question, status, trace_json
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "trace_warning_001",
                "What should I do before opening the panel?",
                "grounded",
                json.dumps({"retrieval": {"candidate_count": 1}}, sort_keys=True),
            ),
        )
        connection.commit()

    with connect_sqlite(sqlite_path) as connection:
        row = connection.execute(
            """
            SELECT
                documents.title,
                pages.page_number,
                source_elements.citation_key,
                chunks.searchable_text
            FROM chunks
            JOIN source_elements USING (source_element_id)
            JOIN pages USING (page_id)
            JOIN documents ON source_elements.document_id = documents.document_id
            WHERE chunks.chunk_id = ?
            """,
            ("chunk_manual_a_warning_0001",),
        ).fetchone()
        cache_count = connection.execute("SELECT COUNT(*) FROM openai_cache_entries").fetchone()[0]
        evaluation_count = connection.execute("SELECT COUNT(*) FROM evaluation_cases").fetchone()[0]
        trace_count = connection.execute("SELECT COUNT(*) FROM ask_traces").fetchone()[0]

    assert tuple(row) == (
        "Pump Manual",
        1,
        "doc_manual_a:p1:warning:0001",
        "Disconnect power before opening the panel.",
    )
    assert cache_count == 1
    assert evaluation_count == 1
    assert trace_count == 1


def test_sqlite_rejects_source_elements_without_existing_page(local_runtime_path: Path) -> None:
    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        try:
            connection.execute(
                """
                INSERT INTO source_elements (
                    source_element_id, document_id, page_id, source_type, page_number,
                    citation_key, section_path_json, content, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "src_orphan",
                    "doc_missing",
                    "page_missing",
                    "text",
                    1,
                    "doc_missing:p1:text:0001",
                    json.dumps([], sort_keys=True),
                    "Orphan source.",
                    json.dumps({}, sort_keys=True),
                ),
            )
        except sqlite3.IntegrityError as exc:
            assert "FOREIGN KEY" in str(exc)
        else:
            raise AssertionError("source element insert should require an existing page")
