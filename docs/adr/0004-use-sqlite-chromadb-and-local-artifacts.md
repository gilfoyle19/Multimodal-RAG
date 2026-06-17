# Use SQLite, ChromaDB, and Local Artifacts

SQLite will be the canonical metadata store, SQLite FTS will provide keyword retrieval, ChromaDB will provide persistent vector search, and the filesystem will store original PDFs and extracted previews. This keeps the under-10-PDF prototype simple to run locally while preserving clear ownership between canonical metadata, search indexes, and artifacts.
