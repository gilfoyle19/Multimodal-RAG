# Use OpenAI Selectively for High-Value Tasks

The prototype will use OpenAI for embeddings, figure captioning, query decomposition, final evidence verification, and structured answer generation, while keeping PDF parsing, table extraction, hybrid retrieval, RRF, and broad reranking local. This balances answer quality and cost by reserving hosted model calls for the steps that require stronger language or vision judgment.
