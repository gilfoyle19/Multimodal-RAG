import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import fitz  # type: ignore[import-untyped]
import pdfplumber

from multimodal_rag.ingestion_status import (
    mark_document_ingestion_failed,
    mark_document_ingestion_indexed,
    mark_document_ingestion_indexing,
)


@dataclass(frozen=True)
class PdfTextExtractionSummary:
    document_id: str
    pages_extracted: int
    text_source_elements_created: int
    table_source_elements_created: int


def extract_pdf_text_source_elements(
    connection: sqlite3.Connection,
    document_id: str,
) -> PdfTextExtractionSummary:
    """Extract digital PDF page records and citeable text source elements."""

    mark_document_ingestion_indexing(connection, document_id)
    try:
        document_row = _load_document_row(connection, document_id)
        summary = _extract_pdf_text_source_elements(connection, document_row)
    except Exception:
        connection.rollback()
        mark_document_ingestion_failed(connection, document_id)
        raise

    mark_document_ingestion_indexed(connection, document_id)
    return summary


def _load_document_row(connection: sqlite3.Connection, document_id: str) -> sqlite3.Row:
    document_row = connection.execute(
        """
        SELECT document_id, source_path
        FROM documents
        WHERE document_id = ?
        """,
        (document_id,),
    ).fetchone()
    if document_row is None:
        raise ValueError(f"unknown document_id: {document_id}")
    return cast(sqlite3.Row, document_row)


def _extract_pdf_text_source_elements(
    connection: sqlite3.Connection,
    document_row: sqlite3.Row,
) -> PdfTextExtractionSummary:
    document_id = document_row["document_id"]
    source_path = Path(document_row["source_path"])
    pages_extracted = 0
    text_source_elements_created = 0
    table_source_elements_created = 0

    with fitz.open(source_path) as pdf_document, pdfplumber.open(source_path) as pdfplumber_document:
        for page_index, page in enumerate(pdf_document, start=1):
            page_id = _page_id(document_id, page_index)
            connection.execute(
                """
                INSERT INTO pages (
                    page_id, document_id, page_number, width_points, height_points
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(document_id, page_number) DO UPDATE SET
                    width_points = excluded.width_points,
                    height_points = excluded.height_points
                """,
                (
                    page_id,
                    document_id,
                    page_index,
                    float(page.rect.width),
                    float(page.rect.height),
                ),
            )
            pages_extracted += 1

            text = page.get_text("text").strip()
            if text:
                source_element_id = _text_source_element_id(document_id, page_index, 1)
                citation_key = _text_citation_key(document_id, page_index, 1)
                connection.execute(
                    """
                    INSERT INTO source_elements (
                        source_element_id, document_id, page_id, source_type, page_number,
                        citation_key, section_path_json, label, content, metadata_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(source_element_id) DO UPDATE SET
                        content = excluded.content,
                        metadata_json = excluded.metadata_json
                    """,
                    (
                        source_element_id,
                        document_id,
                        page_id,
                        "text",
                        page_index,
                        citation_key,
                        json.dumps([], sort_keys=True),
                        f"Page {page_index} Text 1",
                        text,
                        json.dumps({"extraction_method": "pymupdf_text"}, sort_keys=True),
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO chunks (
                        chunk_id, source_element_id, chunk_kind, searchable_text, metadata_json
                    )
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(chunk_id) DO UPDATE SET
                        searchable_text = excluded.searchable_text,
                        metadata_json = excluded.metadata_json
                    """,
                    (
                        _text_chunk_id(document_id, page_index, 1),
                        source_element_id,
                        "source_element",
                        text,
                        json.dumps({"extraction_method": "pymupdf_text"}, sort_keys=True),
                    ),
                )
                text_source_elements_created += 1

            table_source_elements_created += _extract_page_table_source_elements(
                connection=connection,
                document_id=document_id,
                page_id=page_id,
                page_number=page_index,
                tables=pdfplumber_document.pages[page_index - 1].extract_tables(),
            )

    connection.commit()
    return PdfTextExtractionSummary(
        document_id=document_id,
        pages_extracted=pages_extracted,
        text_source_elements_created=text_source_elements_created,
        table_source_elements_created=table_source_elements_created,
    )


def _extract_page_table_source_elements(
    connection: sqlite3.Connection,
    document_id: str,
    page_id: str,
    page_number: int,
    tables: list[list[list[str | None]]],
) -> int:
    table_source_elements_created = 0
    for table_index, table in enumerate(tables, start=1):
        content = _format_table_content(table)
        if not content:
            continue

        source_element_id = _table_source_element_id(document_id, page_number, table_index)
        citation_key = _table_citation_key(document_id, page_number, table_index)
        metadata = {
            "column_count": str(max(len(row) for row in table)),
            "extraction_method": "pdfplumber_table",
            "row_count": str(len(table)),
        }
        metadata_json = json.dumps(metadata, sort_keys=True)
        connection.execute(
            """
            INSERT INTO source_elements (
                source_element_id, document_id, page_id, source_type, page_number,
                citation_key, section_path_json, label, content, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_element_id) DO UPDATE SET
                content = excluded.content,
                metadata_json = excluded.metadata_json
            """,
            (
                source_element_id,
                document_id,
                page_id,
                "table",
                page_number,
                citation_key,
                json.dumps([], sort_keys=True),
                f"Page {page_number} Table {table_index}",
                content,
                metadata_json,
            ),
        )
        connection.execute(
            """
            INSERT INTO chunks (
                chunk_id, source_element_id, chunk_kind, searchable_text, metadata_json
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(chunk_id) DO UPDATE SET
                searchable_text = excluded.searchable_text,
                metadata_json = excluded.metadata_json
            """,
            (
                _table_chunk_id(document_id, page_number, table_index),
                source_element_id,
                "source_element",
                content,
                metadata_json,
            ),
        )
        table_source_elements_created += 1
    return table_source_elements_created


def _format_table_content(table: list[list[str | None]]) -> str:
    rows = []
    for row in table:
        normalized_cells = [_normalize_table_cell(cell) for cell in row]
        if any(normalized_cells):
            rows.append(" | ".join(normalized_cells).strip())
    return "\n".join(rows).strip()


def _normalize_table_cell(cell: str | None) -> str:
    if cell is None:
        return ""
    return " ".join(cell.split())


def _page_id(document_id: str, page_number: int) -> str:
    return f"{document_id}:page:{page_number:04d}"


def _text_source_element_id(document_id: str, page_number: int, text_index: int) -> str:
    return f"{document_id}:source:text:{page_number:04d}:{text_index:04d}"


def _text_chunk_id(document_id: str, page_number: int, text_index: int) -> str:
    return f"{document_id}:chunk:text:{page_number:04d}:{text_index:04d}"


def _text_citation_key(document_id: str, page_number: int, text_index: int) -> str:
    return f"{document_id}:p{page_number}:text:{text_index:04d}"


def _table_source_element_id(document_id: str, page_number: int, table_index: int) -> str:
    return f"{document_id}:source:table:{page_number:04d}:{table_index:04d}"


def _table_chunk_id(document_id: str, page_number: int, table_index: int) -> str:
    return f"{document_id}:chunk:table:{page_number:04d}:{table_index:04d}"


def _table_citation_key(document_id: str, page_number: int, table_index: int) -> str:
    return f"{document_id}:p{page_number}:table:{table_index:04d}"
