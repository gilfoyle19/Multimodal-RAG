import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

import chromadb


VECTOR_COLLECTION_NAME = "searchable_chunks"


@dataclass(frozen=True)
class VectorEmbeddingInput:
    chunk_id: str
    text: str


class VectorEmbeddingAdapter(Protocol):
    def embed_texts(self, inputs: list[VectorEmbeddingInput]) -> list[list[float]]:
        """Return one embedding per input text in the same order."""


@dataclass(frozen=True)
class VectorSearchResult:
    chunk_id: str
    source_element_id: str
    parent_source_element_id: str | None
    document_id: str
    chunk_kind: str
    excerpt: str
    score: float


class OpenAIEmbeddingAdapter:
    """OpenAI-backed embedding adapter kept behind a fakeable protocol."""

    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self._client: Any = OpenAI(api_key=api_key)
        self._model = model

    def embed_texts(self, inputs: list[VectorEmbeddingInput]) -> list[list[float]]:
        if not inputs:
            return []
        response = self._client.embeddings.create(
            model=self._model,
            input=[input_.text for input_ in inputs],
        )
        return [list(item.embedding) for item in response.data]


def rebuild_vector_index_for_document(
    connection: sqlite3.Connection,
    document_id: str,
    chroma_path: Path,
    embedding_adapter: VectorEmbeddingAdapter,
) -> int:
    """Refresh persistent Chroma vectors for all searchable chunks in one document."""

    rows = connection.execute(
        """
        SELECT
            chunks.chunk_id,
            chunks.source_element_id,
            chunks.parent_source_element_id,
            chunks.chunk_kind,
            chunks.searchable_text,
            source_elements.document_id
        FROM chunks
        JOIN source_elements USING (source_element_id)
        WHERE source_elements.document_id = ?
        ORDER BY chunks.chunk_id
        """,
        (document_id,),
    ).fetchall()

    collection = _get_collection(chroma_path)
    collection.delete(where={"document_id": document_id})
    if not rows:
        return 0

    inputs = [
        VectorEmbeddingInput(
            chunk_id=cast(str, row["chunk_id"]),
            text=cast(str, row["searchable_text"]),
        )
        for row in rows
    ]
    embeddings = embedding_adapter.embed_texts(inputs)
    if len(embeddings) != len(inputs):
        raise ValueError("embedding adapter returned the wrong number of vectors")

    collection.upsert(
        ids=[input_.chunk_id for input_ in inputs],
        embeddings=embeddings,
        documents=[input_.text for input_ in inputs],
        metadatas=[
            {
                "chunk_id": cast(str, row["chunk_id"]),
                "source_element_id": cast(str, row["source_element_id"]),
                "parent_source_element_id": cast(str | None, row["parent_source_element_id"]) or "",
                "document_id": cast(str, row["document_id"]),
                "chunk_kind": cast(str, row["chunk_kind"]),
            }
            for row in rows
        ],
    )
    return len(rows)


def search_vector_index(
    chroma_path: Path,
    embedding_adapter: VectorEmbeddingAdapter,
    query: str,
    *,
    limit: int = 10,
) -> list[VectorSearchResult]:
    """Search persisted chunk vectors and return source-element-mapped hits."""

    query_text = query.strip()
    if query_text == "":
        return []

    query_embeddings = embedding_adapter.embed_texts(
        [VectorEmbeddingInput(chunk_id="__query__", text=query_text)]
    )
    if len(query_embeddings) != 1:
        raise ValueError("embedding adapter returned the wrong number of query vectors")

    collection = _get_collection(chroma_path)
    result = collection.query(
        query_embeddings=query_embeddings,
        n_results=limit,
        include=["documents", "distances", "metadatas"],
    )
    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    distances = result.get("distances", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]

    search_results = [
        _build_search_result(
            chunk_id=cast(str, ids[index]),
            document=cast(str, documents[index]),
            distance=cast(float, distances[index]),
            metadata=cast(dict[str, Any], metadatas[index]),
        )
        for index in range(len(ids))
    ]
    return sorted(search_results, key=lambda result_: (-result_.score, result_.chunk_id))


def _get_collection(chroma_path: Path) -> Any:
    chroma_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_path))
    return client.get_or_create_collection(
        name=VECTOR_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _build_search_result(
    *,
    chunk_id: str,
    document: str,
    distance: float,
    metadata: dict[str, Any],
) -> VectorSearchResult:
    parent_source_element_id = cast(str | None, metadata.get("parent_source_element_id"))
    if parent_source_element_id == "":
        parent_source_element_id = None
    return VectorSearchResult(
        chunk_id=chunk_id,
        source_element_id=cast(str, metadata["source_element_id"]),
        parent_source_element_id=parent_source_element_id,
        document_id=cast(str, metadata["document_id"]),
        chunk_kind=cast(str, metadata["chunk_kind"]),
        excerpt=document,
        score=_distance_to_score(distance),
    )


def _distance_to_score(distance: float) -> float:
    return 1.0 / (1.0 + max(distance, 0.0))
