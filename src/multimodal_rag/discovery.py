import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from multimodal_rag.contracts import DocumentIngestionStatus


@dataclass(frozen=True)
class DiscoveredDocumentCandidate:
    document_id: str
    title: str
    source_path: str
    content_hash: str
    provenance: dict[str, Any]
    ingestion_status: str


@dataclass(frozen=True)
class ExistingDocumentState:
    content_hash: str
    ingestion_status: str


def discover_document_candidates(
    database_path: Path,
    connection: sqlite3.Connection,
) -> list[DiscoveredDocumentCandidate]:
    """Find local PDFs and persist discovered document candidates."""

    existing_documents = _load_existing_documents(connection)
    candidates = [
        _build_candidate(pdf_path, database_path, existing_documents)
        for pdf_path in sorted(database_path.rglob("*"))
        if pdf_path.is_file() and pdf_path.suffix.lower() == ".pdf"
    ]

    for candidate in candidates:
        _clear_stale_index_records(connection, candidate, existing_documents)
        connection.execute(
            """
            INSERT INTO documents (
                document_id, title, source_path, content_hash,
                provenance_json, ingestion_status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(document_id) DO UPDATE SET
                title = excluded.title,
                source_path = excluded.source_path,
                content_hash = excluded.content_hash,
                provenance_json = excluded.provenance_json,
                ingestion_status = excluded.ingestion_status,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                candidate.document_id,
                candidate.title,
                candidate.source_path,
                candidate.content_hash,
                json.dumps(candidate.provenance, sort_keys=True),
                candidate.ingestion_status,
            ),
        )
    connection.commit()
    return candidates


def _build_candidate(
    pdf_path: Path,
    database_path: Path,
    existing_documents: dict[str, ExistingDocumentState],
) -> DiscoveredDocumentCandidate:
    provenance = _load_sidecar(pdf_path)
    title = provenance.get("title")
    if not isinstance(title, str) or not title.strip():
        title = pdf_path.stem
    document_id = _document_id(pdf_path, database_path)
    content_hash = _content_hash(pdf_path)

    return DiscoveredDocumentCandidate(
        document_id=document_id,
        title=title,
        source_path=str(pdf_path),
        content_hash=content_hash,
        provenance=provenance,
        ingestion_status=_next_discovery_status(document_id, content_hash, existing_documents),
    )


def _load_existing_documents(connection: sqlite3.Connection) -> dict[str, ExistingDocumentState]:
    rows = connection.execute(
        "SELECT document_id, content_hash, ingestion_status FROM documents"
    ).fetchall()
    return {
        row["document_id"]: ExistingDocumentState(
            content_hash=row["content_hash"],
            ingestion_status=row["ingestion_status"],
        )
        for row in rows
    }


def _next_discovery_status(
    document_id: str,
    content_hash: str,
    existing_documents: dict[str, ExistingDocumentState],
) -> str:
    existing = existing_documents.get(document_id)
    if existing is None:
        return DocumentIngestionStatus.DISCOVERED.value
    if existing.content_hash != content_hash:
        return DocumentIngestionStatus.DISCOVERED.value
    if existing.ingestion_status in {
        DocumentIngestionStatus.INDEXED.value,
        DocumentIngestionStatus.SKIPPED.value,
    }:
        return DocumentIngestionStatus.SKIPPED.value
    return existing.ingestion_status


def _clear_stale_index_records(
    connection: sqlite3.Connection,
    candidate: DiscoveredDocumentCandidate,
    existing_documents: dict[str, ExistingDocumentState],
) -> None:
    existing = existing_documents.get(candidate.document_id)
    if existing is None or existing.content_hash == candidate.content_hash:
        return

    connection.execute(
        "DELETE FROM pages WHERE document_id = ?",
        (candidate.document_id,),
    )


def _load_sidecar(pdf_path: Path) -> dict[str, Any]:
    sidecar_path = pdf_path.with_suffix(".json")
    if not sidecar_path.exists():
        return {}

    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    if not isinstance(sidecar, dict):
        raise ValueError(f"metadata sidecar must contain a JSON object: {sidecar_path}")
    return sidecar


def _document_id(pdf_path: Path, database_path: Path) -> str:
    relative_path = pdf_path.relative_to(database_path).as_posix().lower()
    digest = hashlib.sha256(relative_path.encode("utf-8")).hexdigest()[:16]
    return f"doc_{digest}"


def _content_hash(pdf_path: Path) -> str:
    digest = hashlib.sha256()
    with pdf_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"
