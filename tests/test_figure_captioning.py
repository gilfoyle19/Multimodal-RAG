import json
import shutil
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from multimodal_rag.figure_captioning import (
    FIGURE_CAPTION_PROMPT_VERSION,
    FigureCaptionInput,
    generate_figure_caption,
)
from multimodal_rag.storage import connect_sqlite, initialize_sqlite_database


class FakeCaptionAdapter:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[FigureCaptionInput] = []

    def generate_caption(self, caption_input: FigureCaptionInput) -> dict[str, Any]:
        self.calls.append(caption_input)
        return self.response


@pytest.fixture
def local_runtime_path() -> Generator[Path]:
    runtime_path = Path("data") / "test-figure-captioning" / uuid.uuid4().hex
    runtime_path.mkdir(parents=True, exist_ok=True)
    try:
        yield runtime_path
    finally:
        shutil.rmtree(runtime_path, ignore_errors=True)


def _insert_figure_source(connection: Any, artifacts_path: Path) -> None:
    artifact_relative_path = Path("doc_figures") / "figures" / "page-0001-figure-0001.png"
    artifact_path = artifacts_path / artifact_relative_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(b"figure-bytes")

    connection.execute(
        """
        INSERT INTO documents (
            document_id, title, source_path, content_hash, ingestion_status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("doc_figures", "Figure Manual", "database/figures.pdf", "sha256:figures", "indexing"),
    )
    connection.execute(
        """
        INSERT INTO pages (page_id, document_id, page_number, width_points, height_points)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("doc_figures:page:0001", "doc_figures", 1, 320.0, 240.0),
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
            "doc_figures:source:figure:0001:0001",
            "doc_figures",
            "doc_figures:page:0001",
            "figure",
            1,
            "doc_figures:p1:figure:0001",
            json.dumps([], sort_keys=True),
            "Page 1 Figure 1",
            "",
            json.dumps(
                {
                    "artifact_kind": "original_figure",
                    "artifact_relative_path": artifact_relative_path.as_posix(),
                    "preview_type": "figure",
                },
                sort_keys=True,
            ),
        ),
    )
    connection.commit()


def test_figure_caption_cache_hit_skips_adapter(local_runtime_path: Path) -> None:
    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    artifacts_path = local_runtime_path / "data" / "artifacts"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        _insert_figure_source(connection, artifacts_path)
        caption_input_hash = generate_figure_caption(
            connection,
            "doc_figures:source:figure:0001:0001",
            artifacts_path,
            FakeCaptionAdapter({"technical_caption": "Initial caption."}),
            model="gpt-test-caption",
            schema_version="caption-schema-v1",
        ).input_hash
        connection.execute("DELETE FROM chunks")
        connection.commit()
        uncached_adapter = FakeCaptionAdapter({"technical_caption": "Should not be called."})

        result = generate_figure_caption(
            connection,
            "doc_figures:source:figure:0001:0001",
            artifacts_path,
            uncached_adapter,
            model="gpt-test-caption",
            schema_version="caption-schema-v1",
        )
        cache_rows = connection.execute("SELECT input_hash, model, prompt_version, schema_version FROM openai_cache_entries").fetchall()
        caption_chunk = connection.execute(
            "SELECT searchable_text FROM chunks WHERE chunk_kind = 'figure_caption'"
        ).fetchone()

    assert result.caption == "Initial caption."
    assert result.input_hash == caption_input_hash
    assert uncached_adapter.calls == []
    assert [tuple(row) for row in cache_rows] == [
        (
            caption_input_hash,
            "gpt-test-caption",
            FIGURE_CAPTION_PROMPT_VERSION,
            "caption-schema-v1",
        )
    ]
    assert caption_chunk["searchable_text"] == "Initial caption."


def test_figure_caption_cache_miss_calls_adapter_and_stores_searchable_caption(
    local_runtime_path: Path,
) -> None:
    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    artifacts_path = local_runtime_path / "data" / "artifacts"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        _insert_figure_source(connection, artifacts_path)
        adapter = FakeCaptionAdapter(
            {"technical_caption": "Pump seal orientation diagram with keyed alignment marks."}
        )

        result = generate_figure_caption(
            connection,
            "doc_figures:source:figure:0001:0001",
            artifacts_path,
            adapter,
            model="gpt-test-caption",
            schema_version="caption-schema-v1",
        )
        cache_row = connection.execute(
            """
            SELECT input_hash, model, prompt_version, schema_version, response_json
            FROM openai_cache_entries
            """
        ).fetchone()
        caption_chunk = connection.execute(
            """
            SELECT chunk_id, source_element_id, chunk_kind, searchable_text,
                   parent_source_element_id, metadata_json
            FROM chunks
            WHERE chunk_kind = 'figure_caption'
            """
        ).fetchone()

    assert result.caption == "Pump seal orientation diagram with keyed alignment marks."
    assert len(adapter.calls) == 1
    assert adapter.calls[0].image_bytes == b"figure-bytes"
    assert cache_row["input_hash"] == result.input_hash
    assert cache_row["model"] == "gpt-test-caption"
    assert cache_row["prompt_version"] == FIGURE_CAPTION_PROMPT_VERSION
    assert cache_row["schema_version"] == "caption-schema-v1"
    assert json.loads(cache_row["response_json"]) == {
        "technical_caption": "Pump seal orientation diagram with keyed alignment marks."
    }
    assert caption_chunk["chunk_id"] == "doc_figures:chunk:figure-caption:0001:0001"
    assert caption_chunk["source_element_id"] == "doc_figures:source:figure:0001:0001"
    assert caption_chunk["chunk_kind"] == "figure_caption"
    assert caption_chunk["searchable_text"] == result.caption
    assert caption_chunk["parent_source_element_id"] == "doc_figures:source:figure:0001:0001"
    assert json.loads(caption_chunk["metadata_json"]) == {
        "caption_role": "generated_search_metadata",
        "citation_source_element_id": "doc_figures:source:figure:0001:0001",
        "input_hash": result.input_hash,
        "is_primary_citation": "false",
        "model": "gpt-test-caption",
        "prompt_version": FIGURE_CAPTION_PROMPT_VERSION,
        "schema_version": "caption-schema-v1",
    }


def test_invalid_figure_caption_adapter_response_is_not_cached(
    local_runtime_path: Path,
) -> None:
    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    artifacts_path = local_runtime_path / "data" / "artifacts"
    initialize_sqlite_database(sqlite_path)

    with connect_sqlite(sqlite_path) as connection:
        _insert_figure_source(connection, artifacts_path)
        adapter = FakeCaptionAdapter({"technical_caption": ""})

        with pytest.raises(ValueError, match="invalid figure caption response"):
            generate_figure_caption(
                connection,
                "doc_figures:source:figure:0001:0001",
                artifacts_path,
                adapter,
                model="gpt-test-caption",
                schema_version="caption-schema-v1",
            )

        cache_count = connection.execute("SELECT COUNT(*) FROM openai_cache_entries").fetchone()[0]
        caption_chunk_count = connection.execute(
            "SELECT COUNT(*) FROM chunks WHERE chunk_kind = 'figure_caption'"
        ).fetchone()[0]

    assert len(adapter.calls) == 1
    assert cache_count == 0
    assert caption_chunk_count == 0
