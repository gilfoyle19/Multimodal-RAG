import sqlite3

from multimodal_rag.contracts import DocumentIngestionStatus


QUERYABLE_DOCUMENT_STATUSES = (
    DocumentIngestionStatus.INDEXED.value,
    DocumentIngestionStatus.SKIPPED.value,
)


def mark_document_ingestion_indexing(
    connection: sqlite3.Connection,
    document_id: str,
) -> None:
    """Record that a discovered document is actively being ingested."""

    _set_document_ingestion_status(connection, document_id, DocumentIngestionStatus.INDEXING)


def mark_document_ingestion_indexed(
    connection: sqlite3.Connection,
    document_id: str,
) -> None:
    """Record that a document has a complete usable index."""

    _set_document_ingestion_status(connection, document_id, DocumentIngestionStatus.INDEXED)


def mark_document_ingestion_failed(
    connection: sqlite3.Connection,
    document_id: str,
) -> None:
    """Record that ingestion failed or produced an incomplete index."""

    _set_document_ingestion_status(connection, document_id, DocumentIngestionStatus.FAILED)


def list_queryable_document_ids(connection: sqlite3.Connection) -> list[str]:
    """Return documents whose stored status represents a complete usable index."""

    rows = connection.execute(
        """
        SELECT document_id
        FROM documents
        WHERE ingestion_status IN (?, ?)
        ORDER BY document_id
        """,
        QUERYABLE_DOCUMENT_STATUSES,
    ).fetchall()
    return [row["document_id"] for row in rows]


def _set_document_ingestion_status(
    connection: sqlite3.Connection,
    document_id: str,
    status: DocumentIngestionStatus,
) -> None:
    cursor = connection.execute(
        """
        UPDATE documents
        SET ingestion_status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE document_id = ?
        """,
        (status.value, document_id),
    )
    if cursor.rowcount != 1:
        raise ValueError(f"unknown document_id: {document_id}")
    connection.commit()
