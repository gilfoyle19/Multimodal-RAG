import hashlib
import json
import sqlite3
from dataclasses import dataclass
from typing import Any, cast


@dataclass(frozen=True)
class OpenAICacheKey:
    input_hash: str
    model: str
    prompt_version: str
    schema_version: str


class OpenAICache:
    """Reusable SQLite cache for structured model-mediated responses."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def lookup(self, key: OpenAICacheKey) -> dict[str, Any] | None:
        row = self._connection.execute(
            """
            SELECT response_json
            FROM openai_cache_entries
            WHERE input_hash = ?
              AND model = ?
              AND prompt_version = ?
              AND schema_version = ?
            """,
            (key.input_hash, key.model, key.prompt_version, key.schema_version),
        ).fetchone()
        if row is None:
            return None
        response = json.loads(cast(str, row["response_json"]))
        if not isinstance(response, dict):
            raise ValueError("cached OpenAI response must be a JSON object")
        return cast(dict[str, Any], response)

    def write(self, key: OpenAICacheKey, response: dict[str, Any]) -> None:
        self._connection.execute(
            """
            INSERT INTO openai_cache_entries (
                cache_key, input_hash, model, prompt_version, schema_version, response_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(input_hash, model, prompt_version, schema_version) DO UPDATE SET
                response_json = excluded.response_json
            """,
            (
                _cache_key(key),
                key.input_hash,
                key.model,
                key.prompt_version,
                key.schema_version,
                json.dumps(response, sort_keys=True, separators=(",", ":")),
            ),
        )


def hash_openai_input(payload: Any) -> str:
    """Hash a JSON-serializable model input using canonical object-key ordering."""

    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(serialized).hexdigest()}"


def _cache_key(key: OpenAICacheKey) -> str:
    dimensions = {
        "input_hash": key.input_hash,
        "model": key.model,
        "prompt_version": key.prompt_version,
        "schema_version": key.schema_version,
    }
    payload = json.dumps(dimensions, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"
