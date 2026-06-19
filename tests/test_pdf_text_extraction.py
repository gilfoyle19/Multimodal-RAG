import json
import shutil
import uuid
from collections.abc import Generator
from pathlib import Path
from types import TracebackType
from typing import Literal

import fitz  # type: ignore[import-untyped]
import pdfplumber
import pytest

from multimodal_rag.pdf_text_extraction import extract_pdf_text_source_elements
from multimodal_rag.storage import connect_sqlite, initialize_sqlite_database


@pytest.fixture
def local_runtime_path() -> Generator[Path]:
    runtime_path = Path("data") / "test-pdf-text-extraction" / uuid.uuid4().hex
    runtime_path.mkdir(parents=True, exist_ok=True)
    try:
        yield runtime_path
    finally:
        shutil.rmtree(runtime_path, ignore_errors=True)


def _create_pdf(pdf_path: Path) -> None:
    document = fitz.open()
    try:
        first_page = document.new_page(width=300, height=400)
        first_page.insert_text((72, 72), "Safety\nDisconnect power before service.")
        second_page = document.new_page(width=300, height=400)
        second_page.insert_text((72, 72), "Reset Procedure\nPress reset for five seconds.")
        document.save(pdf_path)
    finally:
        document.close()


def _create_pdf_with_table(pdf_path: Path) -> None:
    document = fitz.open()
    try:
        page = document.new_page(width=360, height=260)
        page.insert_text((72, 48), "Fault Codes")

        left = 72
        top = 80
        cell_width = 100
        cell_height = 26
        rows = [
            ["Code", "Action"],
            ["E12", "Check coolant"],
            ["E13", "Reset drive"],
        ]

        for row_index in range(len(rows) + 1):
            y = top + (row_index * cell_height)
            page.draw_line((left, y), (left + (2 * cell_width), y))
        for column_index in range(3):
            x = left + (column_index * cell_width)
            page.draw_line((x, top), (x, top + (len(rows) * cell_height)))

        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                page.insert_text(
                    (
                        left + (column_index * cell_width) + 6,
                        top + (row_index * cell_height) + 17,
                    ),
                    value,
                )

        document.save(pdf_path)
    finally:
        document.close()


def test_extract_pdf_text_persists_pages_source_elements_and_chunks(
    local_runtime_path: Path,
) -> None:
    pdf_path = local_runtime_path / "database" / "pump.pdf"
    pdf_path.parent.mkdir()
    _create_pdf(pdf_path)
    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        connection.execute(
            """
            INSERT INTO documents (
                document_id, title, source_path, content_hash, ingestion_status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ("doc_pump", "Pump Manual", str(pdf_path), "sha256:pump", "discovered"),
        )
        connection.commit()

        summary = extract_pdf_text_source_elements(connection, "doc_pump")
        pages = connection.execute(
            "SELECT page_id, page_number, width_points, height_points FROM pages ORDER BY page_number"
        ).fetchall()
        sources = connection.execute(
            """
            SELECT source_element_id, page_id, source_type, page_number, citation_key,
                   section_path_json, label, content, metadata_json
            FROM source_elements
            ORDER BY page_number
            """
        ).fetchall()
        chunks = connection.execute(
            "SELECT chunk_id, source_element_id, chunk_kind, searchable_text FROM chunks ORDER BY chunk_id"
        ).fetchall()
        status = connection.execute(
            "SELECT ingestion_status FROM documents WHERE document_id = ?",
            ("doc_pump",),
        ).fetchone()["ingestion_status"]

    assert summary.pages_extracted == 2
    assert summary.text_source_elements_created == 2
    assert status == "indexed"
    assert [row["page_number"] for row in pages] == [1, 2]
    assert pages[0]["page_id"] == "doc_pump:page:0001"
    assert pages[0]["width_points"] == 300.0
    assert pages[0]["height_points"] == 400.0
    assert [row["source_type"] for row in sources] == ["text", "text"]
    assert sources[0]["source_element_id"] == "doc_pump:source:text:0001:0001"
    assert sources[0]["page_id"] == "doc_pump:page:0001"
    assert sources[0]["citation_key"] == "doc_pump:p1:text:0001"
    assert json.loads(sources[0]["section_path_json"]) == []
    assert sources[0]["label"] == "Page 1 Text 1"
    assert "Disconnect power before service." in sources[0]["content"]
    assert json.loads(sources[0]["metadata_json"]) == {"extraction_method": "pymupdf_text"}
    assert chunks[0]["chunk_id"] == "doc_pump:chunk:text:0001:0001"
    assert chunks[0]["source_element_id"] == sources[0]["source_element_id"]
    assert chunks[0]["chunk_kind"] == "source_element"
    assert chunks[0]["searchable_text"] == sources[0]["content"]


def test_extract_pdf_text_persists_whole_table_source_elements(
    local_runtime_path: Path,
) -> None:
    pdf_path = local_runtime_path / "database" / "faults.pdf"
    pdf_path.parent.mkdir()
    _create_pdf_with_table(pdf_path)
    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        connection.execute(
            """
            INSERT INTO documents (
                document_id, title, source_path, content_hash, ingestion_status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ("doc_faults", "Fault Manual", str(pdf_path), "sha256:faults", "discovered"),
        )
        connection.commit()

        summary = extract_pdf_text_source_elements(connection, "doc_faults")
        table_source = connection.execute(
            """
            SELECT source_element_id, page_id, source_type, page_number, citation_key,
                   section_path_json, label, content, metadata_json
            FROM source_elements
            WHERE source_type = 'table'
            """
        ).fetchone()
        table_chunk = connection.execute(
            """
            SELECT chunk_id, source_element_id, chunk_kind, searchable_text, parent_source_element_id,
                   metadata_json
            FROM chunks
            WHERE source_element_id = ?
            """,
            (table_source["source_element_id"],),
        ).fetchone()

    assert summary.table_source_elements_created == 1
    assert table_source["source_element_id"] == "doc_faults:source:table:0001:0001"
    assert table_source["page_id"] == "doc_faults:page:0001"
    assert table_source["page_number"] == 1
    assert table_source["citation_key"] == "doc_faults:p1:table:0001"
    assert json.loads(table_source["section_path_json"]) == []
    assert table_source["label"] == "Page 1 Table 1"
    assert "Code | Action" in table_source["content"]
    assert "E12 | Check coolant" in table_source["content"]
    assert json.loads(table_source["metadata_json"]) == {
        "column_count": "2",
        "extraction_method": "pdfplumber_table",
        "row_count": "3",
    }
    assert table_chunk["chunk_id"] == "doc_faults:chunk:table:0001:0001"
    assert table_chunk["source_element_id"] == table_source["source_element_id"]
    assert table_chunk["chunk_kind"] == "source_element"
    assert table_chunk["searchable_text"] == table_source["content"]
    assert table_chunk["parent_source_element_id"] is None
    assert json.loads(table_chunk["metadata_json"]) == {
        "column_count": "2",
        "extraction_method": "pdfplumber_table",
        "row_count": "3",
    }


def test_extract_pdf_text_persists_row_helper_chunks_for_table_rows(
    local_runtime_path: Path,
) -> None:
    pdf_path = local_runtime_path / "database" / "faults.pdf"
    pdf_path.parent.mkdir()
    _create_pdf_with_table(pdf_path)
    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        connection.execute(
            """
            INSERT INTO documents (
                document_id, title, source_path, content_hash, ingestion_status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ("doc_faults", "Fault Manual", str(pdf_path), "sha256:faults", "discovered"),
        )
        connection.commit()

        extract_pdf_text_source_elements(connection, "doc_faults")
        table_source = connection.execute(
            """
            SELECT source_element_id, citation_key
            FROM source_elements
            WHERE source_type = 'table'
            """
        ).fetchone()
        row_helpers = connection.execute(
            """
            SELECT chunk_id, source_element_id, chunk_kind, searchable_text,
                   parent_source_element_id, metadata_json
            FROM chunks
            WHERE chunk_kind = 'table_row_helper'
            ORDER BY chunk_id
            """
        ).fetchall()
        row_helper_source_count = connection.execute(
            "SELECT COUNT(*) FROM source_elements WHERE source_type = 'table_row_helper'"
        ).fetchone()[0]

    assert row_helper_source_count == 0
    assert [row["chunk_id"] for row in row_helpers] == [
        "doc_faults:chunk:table-row:0001:0001:0002",
        "doc_faults:chunk:table-row:0001:0001:0003",
    ]
    assert [row["source_element_id"] for row in row_helpers] == [
        table_source["source_element_id"],
        table_source["source_element_id"],
    ]
    assert [row["parent_source_element_id"] for row in row_helpers] == [
        table_source["source_element_id"],
        table_source["source_element_id"],
    ]
    assert row_helpers[0]["searchable_text"] == "Code: E12 | Action: Check coolant"
    assert row_helpers[1]["searchable_text"] == "Code: E13 | Action: Reset drive"
    assert json.loads(row_helpers[0]["metadata_json"]) == {
        "chunk_role": "retrieval_helper",
        "citation_source_element_id": table_source["source_element_id"],
        "citation_key": table_source["citation_key"],
        "column_count": "2",
        "extraction_method": "pdfplumber_table",
        "helper_kind": "table_row",
        "is_primary_citation": "false",
        "row_count": "3",
        "row_index": "2",
    }


def test_extract_pdf_text_marks_document_failed_when_pdf_cannot_be_opened(
    local_runtime_path: Path,
) -> None:
    pdf_path = local_runtime_path / "database" / "broken.pdf"
    pdf_path.parent.mkdir()
    pdf_path.write_text("not a real PDF", encoding="utf-8")
    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        connection.execute(
            """
            INSERT INTO documents (
                document_id, title, source_path, content_hash, ingestion_status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ("doc_broken", "Broken Manual", str(pdf_path), "sha256:broken", "discovered"),
        )
        connection.commit()

        with pytest.raises(Exception):
            extract_pdf_text_source_elements(connection, "doc_broken")

        status = connection.execute(
            "SELECT ingestion_status FROM documents WHERE document_id = ?",
            ("doc_broken",),
        ).fetchone()["ingestion_status"]
        page_count = connection.execute(
            "SELECT COUNT(*) FROM pages WHERE document_id = ?",
            ("doc_broken",),
        ).fetchone()[0]

    assert status == "failed"
    assert page_count == 0


def test_extract_pdf_text_rolls_back_partial_rows_when_table_extraction_fails(
    local_runtime_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_path = local_runtime_path / "database" / "faults.pdf"
    pdf_path.parent.mkdir()
    _create_pdf_with_table(pdf_path)
    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    initialize_sqlite_database(sqlite_path)

    class FailingPdfPlumberPage:
        def extract_tables(self) -> list[list[list[str | None]]]:
            raise RuntimeError("table parser failed")

    class FailingPdfPlumberDocument:
        pages = [FailingPdfPlumberPage()]

        def __enter__(self) -> "FailingPdfPlumberDocument":
            return self

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> Literal[False]:
            return False

    def open_failing_pdfplumber(_source_path: Path) -> FailingPdfPlumberDocument:
        return FailingPdfPlumberDocument()

    monkeypatch.setattr(pdfplumber, "open", open_failing_pdfplumber)

    with connect_sqlite(sqlite_path) as connection:
        connection.execute(
            """
            INSERT INTO documents (
                document_id, title, source_path, content_hash, ingestion_status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ("doc_faults", "Fault Manual", str(pdf_path), "sha256:faults", "discovered"),
        )
        connection.commit()

        with pytest.raises(RuntimeError, match="table parser failed"):
            extract_pdf_text_source_elements(connection, "doc_faults")

        status = connection.execute(
            "SELECT ingestion_status FROM documents WHERE document_id = ?",
            ("doc_faults",),
        ).fetchone()["ingestion_status"]
        page_count = connection.execute(
            "SELECT COUNT(*) FROM pages WHERE document_id = ?",
            ("doc_faults",),
        ).fetchone()[0]
        source_count = connection.execute(
            "SELECT COUNT(*) FROM source_elements WHERE document_id = ?",
            ("doc_faults",),
        ).fetchone()[0]
        chunk_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM chunks
            JOIN source_elements USING (source_element_id)
            WHERE source_elements.document_id = ?
            """,
            ("doc_faults",),
        ).fetchone()[0]

    assert status == "failed"
    assert page_count == 0
    assert source_count == 0
    assert chunk_count == 0
