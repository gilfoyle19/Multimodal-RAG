from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from multimodal_rag.settings import get_settings
from multimodal_rag.source_previews import load_source_artifact_path, load_source_preview
from multimodal_rag.storage import connect_sqlite

app = FastAPI(title="Multimodal Manual Troubleshooting API")
app.state.settings = get_settings()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/sources/{source_id}")
def source_preview(source_id: str) -> dict[str, object]:
    settings = app.state.settings
    with connect_sqlite(settings.sqlite_path) as connection:
        preview = load_source_preview(connection, source_id, settings.artifacts_path)

    if preview is None:
        raise HTTPException(status_code=404, detail="source preview not found")
    return preview


@app.get("/sources/{source_id}/artifact")
def source_artifact(source_id: str) -> FileResponse:
    settings = app.state.settings
    with connect_sqlite(settings.sqlite_path) as connection:
        artifact = load_source_artifact_path(connection, source_id, settings.artifacts_path)

    if artifact is None:
        raise HTTPException(status_code=404, detail="source artifact not found")

    artifact_path, mime_type = artifact
    return FileResponse(artifact_path, media_type=mime_type)
