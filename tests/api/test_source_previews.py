import json
import shutil
import sqlite3
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from multimodal_rag.api.app import app
from multimodal_rag.settings import AppSettings
from multimodal_rag.storage import connect_sqlite, initialize_sqlite_database


@pytest.fixture
def local_runtime_path() -> Generator[Path]:
    runtime_path = Path("data") / "test-source-previews" / uuid.uuid4().hex
    runtime_path.mkdir(parents=True, exist_ok=True)
    try:
        yield runtime_path
    finally:
        shutil.rmtree(runtime_path, ignore_errors=True)


@pytest.fixture
def client(local_runtime_path: Path) -> Generator[TestClient]:
    original_settings = app.state.settings
    sqlite_path = local_runtime_path / "data" / "app.sqlite3"
    artifacts_path = local_runtime_path / "data" / "artifacts"
    initialize_sqlite_database(sqlite_path)
    _insert_preview_sources(sqlite_path, artifacts_path)
    app.state.settings = AppSettings(
        sqlite_path=sqlite_path,
        artifacts_path=artifacts_path,
    )
    try:
        yield TestClient(app)
    finally:
        app.state.settings = original_settings


def test_source_preview_endpoint_returns_table_figure_and_page_crop_previews(
    client: TestClient,
) -> None:
    table_response = client.get("/sources/doc_pump:source:table:0001:0001")
    figure_response = client.get("/sources/doc_pump:source:figure:0001:0001")
    text_response = client.get("/sources/doc_pump:source:text:0001:0001")

    assert table_response.status_code == 200
    assert table_response.json() == {
        "source_element_id": "doc_pump:source:table:0001:0001",
        "preview_type": "table",
        "label": "Page 1 Table 1",
        "document_title": "Pump Manual",
        "page_number": 1,
        "citation_key": "doc_pump:p1:table:0001",
        "section_path": [],
        "table": {
            "content": "Code | Action\nE12 | Check coolant",
            "row_count": 2,
            "column_count": 2,
        },
        "artifact": None,
        "page_crop": None,
    }

    figure_body = figure_response.json()
    assert figure_response.status_code == 200
    assert figure_body["preview_type"] == "figure"
    assert figure_body["artifact"] == {
        "url": "/sources/doc_pump:source:figure:0001:0001/artifact",
        "mime_type": "image/png",
    }
    assert "data/" not in figure_body["artifact"]["url"]
    assert "doc_pump/figures" not in figure_body["artifact"]["url"]
    assert figure_body["table"] is None
    artifact_response = client.get(figure_body["artifact"]["url"])
    assert artifact_response.status_code == 200
    assert artifact_response.headers["content-type"] == "image/png"
    assert artifact_response.content.startswith(b"\x89PNG")

    assert text_response.status_code == 200
    assert text_response.json()["preview_type"] == "page_crop"
    assert text_response.json()["page_crop"] == {
        "url": "/sources/doc_pump:source:text:0001:0001/artifact",
        "bbox": {"x0": "1.0", "x1": "2.0", "y0": "3.0", "y1": "4.0"},
    }


def test_source_preview_endpoint_returns_404_for_missing_source(client: TestClient) -> None:
    response = client.get("/sources/missing-source")

    assert response.status_code == 404
    assert response.json() == {"detail": "source preview not found"}


def _insert_preview_sources(sqlite_path: Path, artifacts_path: Path) -> None:
    figure_artifact = artifacts_path / "doc_pump" / "figures" / "page-0001-figure-0001.png"
    figure_artifact.parent.mkdir(parents=True, exist_ok=True)
    figure_artifact.write_bytes(b"\x89PNG\r\n\x1a\nfigure")

    with connect_sqlite(sqlite_path) as connection:
        connection.execute(
            """
            INSERT INTO documents (
                document_id, title, source_path, content_hash, ingestion_status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ("doc_pump", "Pump Manual", "database/pump.pdf", "sha256:pump", "indexed"),
        )
        connection.execute(
            """
            INSERT INTO pages (page_id, document_id, page_number, width_points, height_points)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("doc_pump:page:0001", "doc_pump", 1, 300.0, 400.0),
        )
        _insert_source_element(
            connection,
            source_element_id="doc_pump:source:table:0001:0001",
            source_type="table",
            citation_key="doc_pump:p1:table:0001",
            label="Page 1 Table 1",
            content="Code | Action\nE12 | Check coolant",
            metadata={"column_count": "2", "row_count": "2"},
        )
        _insert_source_element(
            connection,
            source_element_id="doc_pump:source:figure:0001:0001",
            source_type="figure",
            citation_key="doc_pump:p1:figure:0001",
            label="Page 1 Figure 1",
            content="",
            metadata={
                "artifact_relative_path": "doc_pump/figures/page-0001-figure-0001.png",
                "image_extension": "png",
                "preview_type": "figure",
            },
        )
        _insert_source_element(
            connection,
            source_element_id="doc_pump:source:text:0001:0001",
            source_type="text",
            citation_key="doc_pump:p1:text:0001",
            label="Page 1 Text 1",
            content="Disconnect power before service.",
            metadata={
                "bbox_json": json.dumps(
                    {"x0": "1.0", "x1": "2.0", "y0": "3.0", "y1": "4.0"},
                    sort_keys=True,
                )
            },
        )
        connection.commit()


def _insert_source_element(
    connection: sqlite3.Connection,
    *,
    source_element_id: str,
    source_type: str,
    citation_key: str,
    label: str,
    content: str,
    metadata: dict[str, str],
) -> None:
    connection.execute(
        """
        INSERT INTO source_elements (
            source_element_id, document_id, page_id, source_type, page_number,
            citation_key, section_path_json, label, content, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_element_id,
            "doc_pump",
            "doc_pump:page:0001",
            source_type,
            1,
            citation_key,
            json.dumps([], sort_keys=True),
            label,
            content,
            json.dumps(metadata, sort_keys=True),
        ),
    )
