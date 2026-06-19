import json
import re
import sqlite3
from dataclasses import dataclass
from typing import Any, cast


@dataclass(frozen=True)
class KeywordSearchResult:
    chunk_id: str
    source_element_id: str
    parent_source_element_id: str | None
    document_id: str
    chunk_kind: str
    excerpt: str
    score: float


def rebuild_keyword_index_for_document(
    connection: sqlite3.Connection,
    document_id: str,
    *,
    commit: bool = True,
) -> int:
    """Refresh SQLite FTS rows for all searchable chunks in one document."""

    connection.execute(
        "DELETE FROM keyword_index_fts WHERE document_id = ?",
        (document_id,),
    )
    rows = connection.execute(
        """
        SELECT
            chunks.chunk_id,
            chunks.source_element_id,
            chunks.parent_source_element_id,
            chunks.chunk_kind,
            chunks.searchable_text,
            chunks.metadata_json AS chunk_metadata_json,
            source_elements.label,
            source_elements.source_type,
            source_elements.section_path_json,
            source_elements.metadata_json AS source_metadata_json,
            documents.document_id,
            documents.title
        FROM chunks
        JOIN source_elements USING (source_element_id)
        JOIN documents ON source_elements.document_id = documents.document_id
        WHERE documents.document_id = ?
        ORDER BY chunks.chunk_id
        """,
        (document_id,),
    ).fetchall()
    for row in rows:
        connection.execute(
            """
            INSERT INTO keyword_index_fts (
                chunk_id, source_element_id, parent_source_element_id, document_id,
                chunk_kind, searchable_text, indexed_metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["chunk_id"],
                row["source_element_id"],
                row["parent_source_element_id"],
                row["document_id"],
                row["chunk_kind"],
                row["searchable_text"],
                _build_indexed_metadata(row),
            ),
        )
    if commit:
        connection.commit()
    return len(rows)


def search_keyword_index(
    connection: sqlite3.Connection,
    query: str,
    *,
    limit: int = 10,
) -> list[KeywordSearchResult]:
    """Search indexed chunks and return source-element-mapped keyword hits."""

    match_query = _match_query(query)
    if match_query == "":
        return []

    rows = connection.execute(
        """
        SELECT
            chunk_id,
            source_element_id,
            parent_source_element_id,
            document_id,
            chunk_kind,
            searchable_text,
            bm25(keyword_index_fts) AS rank
        FROM keyword_index_fts
        WHERE keyword_index_fts MATCH ?
        ORDER BY rank, chunk_id
        LIMIT ?
        """,
        (match_query, limit),
    ).fetchall()
    return [
        KeywordSearchResult(
            chunk_id=cast(str, row["chunk_id"]),
            source_element_id=cast(str, row["source_element_id"]),
            parent_source_element_id=cast(str | None, row["parent_source_element_id"]),
            document_id=cast(str, row["document_id"]),
            chunk_kind=cast(str, row["chunk_kind"]),
            excerpt=cast(str, row["searchable_text"]),
            score=_rank_to_score(cast(float, row["rank"])),
        )
        for row in rows
    ]


def _build_indexed_metadata(row: sqlite3.Row) -> str:
    metadata_parts = [
        cast(str, row["title"]),
        cast(str, row["source_type"]),
        cast(str | None, row["label"]) or "",
        *_json_string_values(row["section_path_json"]),
        *_json_string_values(row["source_metadata_json"]),
        *_json_string_values(row["chunk_metadata_json"]),
    ]
    return " ".join(part for part in metadata_parts if part).strip()


def _json_string_values(raw_json: object) -> list[str]:
    parsed = json.loads(cast(str, raw_json))
    values: list[str] = []
    _collect_string_values(parsed, values)
    return values


def _collect_string_values(value: Any, values: list[str]) -> None:
    if isinstance(value, str):
        values.append(value)
        return
    if isinstance(value, list):
        for item in value:
            _collect_string_values(item, values)
        return
    if isinstance(value, dict):
        for item in value.values():
            _collect_string_values(item, values)


def _match_query(query: str) -> str:
    terms = re.findall(r"[\w]+", query)
    return " ".join(f'"{term}"' for term in terms)


def _rank_to_score(rank: float) -> float:
    return 1.0 / (1.0 + max(rank, 0.0))
