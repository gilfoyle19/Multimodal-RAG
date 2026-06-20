import base64
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

from pydantic import BaseModel, Field, ValidationError

from multimodal_rag.openai_cache import OpenAICache, OpenAICacheKey, hash_openai_input


FIGURE_CAPTION_PROMPT_VERSION = "figure-caption-v1"


class FigureCaptionInput(BaseModel):
    image_bytes: bytes
    mime_type: str
    source_element_id: str
    label: str | None
    page_number: int


class FigureCaptionResponse(BaseModel):
    technical_caption: str = Field(min_length=1)


class FigureCaptionAdapter(Protocol):
    def generate_caption(self, caption_input: FigureCaptionInput) -> dict[str, Any]:
        """Return a structured figure caption response."""


@dataclass(frozen=True)
class FigureCaptionResult:
    source_element_id: str
    caption: str
    input_hash: str
    model: str
    prompt_version: str
    schema_version: str
    cache_hit: bool


class OpenAIFigureCaptionAdapter:
    """OpenAI-backed adapter kept behind the fakeable FigureCaptionAdapter protocol."""

    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self._client: Any = OpenAI(api_key=api_key)
        self._model = model

    def generate_caption(self, caption_input: FigureCaptionInput) -> dict[str, Any]:
        image_base64 = base64.b64encode(caption_input.image_bytes).decode("ascii")
        image_url = f"data:{caption_input.mime_type};base64,{image_base64}"
        response_input: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Describe this technical manual figure in one concise "
                            "searchable caption. Return only JSON with technical_caption."
                        ),
                    },
                    {"type": "input_image", "image_url": image_url},
                ],
            }
        ]
        response = self._client.responses.create(
            model=self._model,
            input=response_input,
        )
        response_text: str = response.output_text
        parsed = json.loads(response_text)
        if not isinstance(parsed, dict):
            raise ValueError("invalid figure caption response")
        return parsed


def generate_figure_caption(
    connection: sqlite3.Connection,
    source_element_id: str,
    artifacts_path: Path,
    adapter: FigureCaptionAdapter,
    *,
    model: str,
    schema_version: str,
    prompt_version: str = FIGURE_CAPTION_PROMPT_VERSION,
    commit: bool = True,
) -> FigureCaptionResult:
    source_row = _load_figure_source(connection, source_element_id)
    caption_input = _build_caption_input(source_row, artifacts_path)
    input_hash = _caption_input_hash(caption_input)
    cache = OpenAICache(connection)
    cache_key = OpenAICacheKey(
        input_hash=input_hash,
        model=model,
        prompt_version=prompt_version,
        schema_version=schema_version,
    )

    cached_response = cache.lookup(cache_key)
    if cached_response is not None:
        caption_response = _validate_caption_response(cached_response)
        cache_hit = True
    else:
        caption_response = _validate_caption_response(adapter.generate_caption(caption_input))
        cache.write(cache_key, caption_response.model_dump(mode="json"))
        cache_hit = False

    _store_caption_chunk(
        connection=connection,
        source_row=source_row,
        caption=caption_response.technical_caption,
        input_hash=input_hash,
        model=model,
        prompt_version=prompt_version,
        schema_version=schema_version,
    )
    if commit:
        connection.commit()
    return FigureCaptionResult(
        source_element_id=source_element_id,
        caption=caption_response.technical_caption,
        input_hash=input_hash,
        model=model,
        prompt_version=prompt_version,
        schema_version=schema_version,
        cache_hit=cache_hit,
    )


def _load_figure_source(connection: sqlite3.Connection, source_element_id: str) -> sqlite3.Row:
    source_row = connection.execute(
        """
        SELECT source_element_id, source_type, page_number, label, metadata_json
        FROM source_elements
        WHERE source_element_id = ?
        """,
        (source_element_id,),
    ).fetchone()
    if source_row is None:
        raise ValueError(f"unknown source_element_id: {source_element_id}")
    if source_row["source_type"] != "figure":
        raise ValueError(f"source element is not a figure: {source_element_id}")
    return cast(sqlite3.Row, source_row)


def _build_caption_input(source_row: sqlite3.Row, artifacts_path: Path) -> FigureCaptionInput:
    metadata = json.loads(cast(str, source_row["metadata_json"]))
    artifact_relative_path = metadata.get("artifact_relative_path")
    if not isinstance(artifact_relative_path, str):
        raise ValueError("figure source is missing artifact_relative_path")

    artifact_path = artifacts_path / artifact_relative_path
    image_bytes = artifact_path.read_bytes()
    return FigureCaptionInput(
        image_bytes=image_bytes,
        mime_type=_mime_type_for_artifact(artifact_path),
        source_element_id=cast(str, source_row["source_element_id"]),
        label=cast(str | None, source_row["label"]),
        page_number=cast(int, source_row["page_number"]),
    )


def _caption_input_hash(caption_input: FigureCaptionInput) -> str:
    hash_input = {
        "image_sha256": hashlib.sha256(caption_input.image_bytes).hexdigest(),
        "label": caption_input.label,
        "mime_type": caption_input.mime_type,
        "page_number": caption_input.page_number,
        "source_element_id": caption_input.source_element_id,
    }
    return hash_openai_input(hash_input)


def _store_caption_chunk(
    connection: sqlite3.Connection,
    *,
    source_row: sqlite3.Row,
    caption: str,
    input_hash: str,
    model: str,
    prompt_version: str,
    schema_version: str,
) -> None:
    source_element_id = cast(str, source_row["source_element_id"])
    chunk_id = source_element_id.replace(":source:figure:", ":chunk:figure-caption:")
    metadata = {
        "caption_role": "generated_search_metadata",
        "citation_source_element_id": source_element_id,
        "input_hash": input_hash,
        "is_primary_citation": "false",
        "model": model,
        "prompt_version": prompt_version,
        "schema_version": schema_version,
    }
    connection.execute(
        """
        INSERT INTO chunks (
            chunk_id, source_element_id, chunk_kind, searchable_text,
            parent_source_element_id, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(chunk_id) DO UPDATE SET
            searchable_text = excluded.searchable_text,
            parent_source_element_id = excluded.parent_source_element_id,
            metadata_json = excluded.metadata_json
        """,
        (
            chunk_id,
            source_element_id,
            "figure_caption",
            caption,
            source_element_id,
            json.dumps(metadata, sort_keys=True),
        ),
    )


def _validate_caption_response(response: dict[str, Any]) -> FigureCaptionResponse:
    try:
        return FigureCaptionResponse.model_validate(response)
    except ValidationError as exc:
        raise ValueError("invalid figure caption response") from exc


def _mime_type_for_artifact(artifact_path: Path) -> str:
    extension = artifact_path.suffix.lower()
    if extension in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if extension == ".webp":
        return "image/webp"
    return "image/png"
