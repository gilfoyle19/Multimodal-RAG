from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from multimodal_rag.api.app import app
from multimodal_rag.contracts import (
    ChunkKind,
    CitationIdentity,
    RetrievalCandidate,
    RetrievalResponse,
    RetrievalScores,
    SourceElementType,
)


class FakeRetrievalService:
    def __init__(self, response: RetrievalResponse) -> None:
        self.response = response
        self.queries: list[str] = []

    def retrieve(self, query: str) -> RetrievalResponse:
        self.queries.append(query)
        return self.response


@pytest.fixture
def client() -> Generator[TestClient]:
    original_service = app.state.retrieval_service
    try:
        yield TestClient(app)
    finally:
        app.state.retrieval_service = original_service


def test_retrieve_returns_ranked_inspection_candidates(client: TestClient) -> None:
    source_id = "source-fault-table"
    candidate = RetrievalCandidate(
        rank=1,
        candidate_id="candidate:chunk-fault-row",
        chunk_id="chunk-fault-row",
        source_element_id=source_id,
        chunk_kind=ChunkKind.TABLE_ROW_HELPER,
        parent_source_element_id=source_id,
        citation=CitationIdentity(
            document_id="manual",
            page_id="page-3",
            source_element_id=source_id,
            page_number=3,
            citation_key="manual:p3:table:1",
        ),
        document_title="Pump Manual",
        section_path=["Troubleshooting", "Fault codes"],
        source_type=SourceElementType.TABLE,
        label="Fault table",
        excerpt="E12 | Check coolant flow",
        retrieval_scores=RetrievalScores(vector=0.9, keyword=0.8, rrf=0.03, rerank=0.95),
        relevance_reason="Matched vector and keyword search; local rerank score 0.950.",
    )
    service = FakeRetrievalService(RetrievalResponse(query="fault E12", candidates=[candidate]))
    app.state.retrieval_service = service

    response = client.post("/retrieve", json={"query": "fault E12"})

    assert response.status_code == 200
    assert service.queries == ["fault E12"]
    body = response.json()
    assert body["query"] == "fault E12"
    assert body["candidates"][0]["rank"] == 1
    assert body["candidates"][0]["source_element_id"] == source_id
    assert body["candidates"][0]["document_title"] == "Pump Manual"
    assert body["candidates"][0]["source_type"] == "table"
    assert body["candidates"][0]["retrieval_scores"] == {
        "vector": 0.9,
        "keyword": 0.8,
        "rrf": 0.03,
        "rerank": 0.95,
    }
    assert body["candidates"][0]["relevance_reason"].startswith("Matched vector")


def test_retrieve_returns_empty_candidate_list(client: TestClient) -> None:
    service = FakeRetrievalService(RetrievalResponse(query="unknown fault", candidates=[]))
    app.state.retrieval_service = service

    response = client.post("/retrieve", json={"query": "unknown fault"})

    assert response.status_code == 200
    assert response.json() == {"query": "unknown fault", "candidates": []}


@pytest.mark.parametrize(
    "payload",
    [{}, {"query": ""}, {"query": "   "}, {"query": "fault", "unexpected": True}],
)
def test_retrieve_rejects_invalid_request_payloads(
    client: TestClient,
    payload: dict[str, object],
) -> None:
    response = client.post("/retrieve", json=payload)

    assert response.status_code == 422
