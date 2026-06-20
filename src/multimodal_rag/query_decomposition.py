import json
import sqlite3
from typing import Any, Protocol

from pydantic import BaseModel, Field, ValidationError, field_validator

from multimodal_rag.contracts import QueryDecomposition
from multimodal_rag.openai_cache import OpenAICache, OpenAICacheKey, hash_openai_input


QUERY_DECOMPOSITION_PROMPT_VERSION = "query-decomposition-v1"


class QueryDecompositionInput(BaseModel):
    question: str = Field(min_length=1)
    validation_feedback: str | None = None

    @field_validator("question")
    @classmethod
    def reject_blank_question(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("question must contain non-whitespace characters")
        return question


class QueryDecompositionAdapter(Protocol):
    def decompose(self, decomposition_input: QueryDecompositionInput) -> dict[str, Any]:
        """Return a structured query decomposition response."""


class OpenAIQueryDecompositionAdapter:
    """OpenAI-backed adapter behind the fakeable decomposition boundary."""

    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self._client: Any = OpenAI(api_key=api_key)
        self._model = model

    def decompose(self, decomposition_input: QueryDecompositionInput) -> dict[str, Any]:
        instruction = (
            "Decompose the troubleshooting question into every required sub-question and "
            "extract exact equipment, component, fault-code, and specification entities. "
            "Use deterministic IDs sq_1, sq_2, and so on. Return only JSON with "
            "sub_questions and entities. Do not omit a part because it may be unsupported."
        )
        if decomposition_input.validation_feedback is not None:
            instruction += (
                " The previous response was invalid. Correct these validation errors: "
                f"{decomposition_input.validation_feedback}"
            )
        response = self._client.responses.create(
            model=self._model,
            input=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": decomposition_input.question},
            ],
        )
        parsed = json.loads(response.output_text)
        if not isinstance(parsed, dict):
            raise ValueError("invalid query decomposition response")
        return parsed


def decompose_query(
    question: str,
    adapter: QueryDecompositionAdapter,
    *,
    connection: sqlite3.Connection | None = None,
    model: str | None = None,
    schema_version: str | None = None,
    prompt_version: str = QUERY_DECOMPOSITION_PROMPT_VERSION,
) -> QueryDecomposition:
    """Turn one troubleshooting question into validated retrieval sub-questions."""

    initial_input = QueryDecompositionInput(question=question)
    cache_key: OpenAICacheKey | None = None
    cache: OpenAICache | None = None
    if connection is not None:
        if model is None or schema_version is None:
            raise ValueError("model and schema_version are required when caching decomposition")
        cache = OpenAICache(connection)
        cache_key = OpenAICacheKey(
            input_hash=hash_openai_input({"question": initial_input.question}),
            model=model,
            prompt_version=prompt_version,
            schema_version=schema_version,
        )
        cached_response = cache.lookup(cache_key)
        if cached_response is not None:
            return QueryDecomposition.model_validate(cached_response)

    response = adapter.decompose(initial_input)
    try:
        result = QueryDecomposition.model_validate(response)
    except ValidationError as error:
        feedback = json.dumps(
            [
                {
                    "location": [str(part) for part in detail["loc"]],
                    "message": detail["msg"],
                    "error_type": detail["type"],
                }
                for detail in error.errors(include_url=False, include_input=False)
            ],
            sort_keys=True,
            separators=(",", ":"),
        )
        retry_response = adapter.decompose(
            QueryDecompositionInput(question=question, validation_feedback=feedback)
        )
        try:
            result = QueryDecomposition.model_validate(retry_response)
        except ValidationError:
            return QueryDecomposition.model_validate(
                {
                    "sub_questions": [
                        {"subquestion_id": "sq_1", "question": question}
                    ],
                    "entities": [],
                    "fallback_used": True,
                }
            )
    if cache is not None and cache_key is not None:
        cache.write(cache_key, result.model_dump(mode="json"))
    return result
