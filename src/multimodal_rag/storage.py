import sqlite3
from pathlib import Path


SCHEMA_VERSION = 1


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    provenance_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(provenance_json)),
    ingestion_status TEXT NOT NULL DEFAULT 'discovered',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pages (
    page_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL CHECK (page_number >= 1),
    width_points REAL CHECK (width_points IS NULL OR width_points > 0),
    height_points REAL CHECK (height_points IS NULL OR height_points > 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (document_id, page_number)
);

CREATE TABLE IF NOT EXISTS source_elements (
    source_element_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    page_id TEXT NOT NULL REFERENCES pages(page_id) ON DELETE CASCADE,
    source_type TEXT NOT NULL CHECK (
        source_type IN ('text', 'table', 'table_row_helper', 'figure', 'warning', 'procedure', 'spec')
    ),
    page_number INTEGER NOT NULL CHECK (page_number >= 1),
    citation_key TEXT NOT NULL UNIQUE,
    section_path_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(section_path_json)),
    label TEXT,
    content TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(metadata_json)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    source_element_id TEXT NOT NULL REFERENCES source_elements(source_element_id) ON DELETE CASCADE,
    chunk_kind TEXT NOT NULL CHECK (
        chunk_kind IN ('source_element', 'table_row_helper', 'figure_caption', 'combined_context')
    ),
    searchable_text TEXT NOT NULL CHECK (length(searchable_text) > 0),
    parent_source_element_id TEXT REFERENCES source_elements(source_element_id) ON DELETE CASCADE,
    metadata_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(metadata_json)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS openai_cache_entries (
    cache_key TEXT PRIMARY KEY,
    input_hash TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    response_json TEXT NOT NULL CHECK (json_valid(response_json)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (input_hash, model, prompt_version, schema_version)
);

CREATE TABLE IF NOT EXISTS evaluation_cases (
    case_id TEXT PRIMARY KEY,
    question TEXT NOT NULL CHECK (length(question) > 0),
    expected_status TEXT NOT NULL CHECK (expected_status IN ('grounded', 'partial', 'not_found')),
    fixture_json TEXT NOT NULL CHECK (json_valid(fixture_json)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ask_traces (
    trace_id TEXT PRIMARY KEY,
    question TEXT NOT NULL CHECK (length(question) > 0),
    status TEXT NOT NULL CHECK (status IN ('grounded', 'partial', 'not_found', 'failed')),
    trace_json TEXT NOT NULL CHECK (json_valid(trace_json)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pages_document_id ON pages(document_id);
CREATE INDEX IF NOT EXISTS idx_source_elements_document_id ON source_elements(document_id);
CREATE INDEX IF NOT EXISTS idx_source_elements_page_id ON source_elements(page_id);
CREATE INDEX IF NOT EXISTS idx_chunks_source_element_id ON chunks(source_element_id);
CREATE INDEX IF NOT EXISTS idx_ask_traces_created_at ON ask_traces(created_at);
"""


def connect_sqlite(sqlite_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection with runtime pragmas expected by the application."""

    connection = sqlite3.connect(sqlite_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def initialize_sqlite_database(sqlite_path: Path) -> None:
    """Create the canonical SQLite metadata schema at a configured local path."""

    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    with connect_sqlite(sqlite_path) as connection:
        connection.executescript(SCHEMA_SQL)
        connection.execute(
            "INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)",
            (SCHEMA_VERSION,),
        )
        connection.commit()
