import json
import sqlite3
from pathlib import Path
from typing import Any, cast

from multimodal_rag.contracts import SourceElementType, SourcePreviewType


def load_source_preview(
    connection: sqlite3.Connection,
    source_element_id: str,
    artifacts_path: Path,
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT
            source_elements.source_element_id,
            source_elements.source_type,
            source_elements.page_number,
            source_elements.citation_key,
            source_elements.section_path_json,
            source_elements.label,
            source_elements.content,
            source_elements.metadata_json,
            documents.title AS document_title
        FROM source_elements
        JOIN documents USING (document_id)
        WHERE source_elements.source_element_id = ?
        """,
        (source_element_id,),
    ).fetchone()
    if row is None:
        return None

    source_type = SourceElementType(cast(str, row["source_type"]))
    metadata = _load_json_object(cast(str, row["metadata_json"]))
    preview_type = _preview_type_for_source(source_type, metadata)
    return {
        "source_element_id": row["source_element_id"],
        "preview_type": preview_type.value,
        "label": row["label"],
        "document_title": row["document_title"],
        "page_number": row["page_number"],
        "citation_key": row["citation_key"],
        "section_path": _load_json_array(cast(str, row["section_path_json"])),
        "table": _table_preview(row, metadata) if preview_type is SourcePreviewType.TABLE else None,
        "artifact": _artifact_preview(row, metadata, artifacts_path)
        if preview_type is SourcePreviewType.FIGURE
        else None,
        "page_crop": _page_crop_preview(row, metadata)
        if preview_type is SourcePreviewType.PAGE_CROP
        else None,
    }


def load_source_artifact_path(
    connection: sqlite3.Connection,
    source_element_id: str,
    artifacts_path: Path,
) -> tuple[Path, str] | None:
    row = connection.execute(
        """
        SELECT metadata_json
        FROM source_elements
        WHERE source_element_id = ?
        """,
        (source_element_id,),
    ).fetchone()
    if row is None:
        return None

    metadata = _load_json_object(cast(str, row["metadata_json"]))
    artifact_relative_path = metadata.get("artifact_relative_path")
    if not isinstance(artifact_relative_path, str):
        return None

    artifact_path = _safe_artifact_path(artifacts_path, artifact_relative_path)
    if artifact_path is None or not artifact_path.exists():
        return None

    return artifact_path, _mime_type_for_artifact(artifact_path)


def _preview_type_for_source(
    source_type: SourceElementType,
    metadata: dict[str, Any],
) -> SourcePreviewType:
    preview_type = metadata.get("preview_type")
    if isinstance(preview_type, str):
        return SourcePreviewType(preview_type)
    if source_type is SourceElementType.TABLE:
        return SourcePreviewType.TABLE
    if source_type is SourceElementType.FIGURE:
        return SourcePreviewType.FIGURE
    return SourcePreviewType.PAGE_CROP


def _table_preview(row: sqlite3.Row, metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": row["content"],
        "row_count": _optional_int(metadata.get("row_count")),
        "column_count": _optional_int(metadata.get("column_count")),
    }


def _artifact_preview(
    row: sqlite3.Row,
    metadata: dict[str, Any],
    artifacts_path: Path,
) -> dict[str, str] | None:
    artifact_relative_path = metadata.get("artifact_relative_path")
    if not isinstance(artifact_relative_path, str):
        return None

    artifact_path = _safe_artifact_path(artifacts_path, artifact_relative_path)
    if artifact_path is None:
        return None

    return {
        "url": f"/sources/{row['source_element_id']}/artifact",
        "mime_type": _mime_type_for_artifact(artifact_path),
    }


def _page_crop_preview(row: sqlite3.Row, metadata: dict[str, Any]) -> dict[str, Any]:
    bbox = {}
    bbox_json = metadata.get("bbox_json")
    if isinstance(bbox_json, str):
        bbox = _load_json_object(bbox_json)
    return {
        "url": f"/sources/{row['source_element_id']}/artifact",
        "bbox": bbox,
    }


def _safe_artifact_path(artifacts_path: Path, artifact_relative_path: str) -> Path | None:
    relative_path = Path(artifact_relative_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        return None

    artifacts_root = artifacts_path.resolve()
    artifact_path = (artifacts_root / relative_path).resolve()
    if artifacts_root not in artifact_path.parents and artifact_path != artifacts_root:
        return None
    return artifact_path


def _mime_type_for_artifact(artifact_path: Path) -> str:
    extension = artifact_path.suffix.lower()
    if extension == ".png":
        return "image/png"
    if extension in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if extension == ".webp":
        return "image/webp"
    return "application/octet-stream"


def _load_json_object(raw_json: str) -> dict[str, Any]:
    value = json.loads(raw_json)
    if not isinstance(value, dict):
        return {}
    return value


def _load_json_array(raw_json: str) -> list[Any]:
    value = json.loads(raw_json)
    if not isinstance(value, list):
        return []
    return value


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
