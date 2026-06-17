from fastapi import FastAPI

app = FastAPI(title="Multimodal Manual Troubleshooting API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
