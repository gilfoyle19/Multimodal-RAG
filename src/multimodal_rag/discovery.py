import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DiscoveredDocumentCandidate:
    document_id: str
    title: str
    source_path: str
    content_hash: str
    provenance: dict[str, Any]
    ingestion_status: str


def discover_document_candidates(
    database_path: Path,
    connection: sqlite3.Connection,
) -> list[DiscoveredDocumentCandidate]:
    """Find local PDFs and persist discovered document candidates."""

    candidates = [
        _build_candidate(pdf_path, database_path)
        for pdf_path in sorted(database_path.rglob("*"))
        if pdf_path.is_file() and pdf_path.suffix.lower() == ".pdf"
    ]

    for candidate in candidates:
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


def _build_candidate(pdf_path: Path, database_path: Path) -> DiscoveredDocumentCandidate:
    provenance = _load_sidecar(pdf_path)
    title = provenance.get("title")
    if not isinstance(title, str) or not title.strip():
        title = pdf_path.stem

    return DiscoveredDocumentCandidate(
        document_id=_document_id(pdf_path, database_path),
        title=title,
        source_path=str(pdf_path),
        content_hash=_content_hash(pdf_path),
        provenance=provenance,
        ingestion_status="discovered",
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
