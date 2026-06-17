from fastapi import FastAPI

from multimodal_rag.settings import get_settings

app = FastAPI(title="Multimodal Manual Troubleshooting API")
app.state.settings = get_settings()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
