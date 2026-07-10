# ADR-002: Vector Store — ChromaDB over Qdrant / Pinecone / pgvector

## Context
MediMate uses Retrieval-Augmented Generation (RAG) to ground SOAP note generation in real clinical evidence. We need a vector database to store and query embeddings for ~1,700 documents across three collections: NICE clinical guidelines (792 chunks), ICD-10 codes (123 entries), and drug reference data (765 chunks). The vector store must support semantic similarity search, persistent storage, and be runnable on a developer laptop with zero infrastructure.

## Decision
We chose **ChromaDB** with **persistent local storage** and the **sentence-transformers `all-MiniLM-L6-v2`** embedding model.

## Consequences

### Positive
- **Zero infrastructure:** ChromaDB runs as a Python library with SQLite-backed persistence. No server process, no Docker container, no cloud account needed. `pip install chromadb` and you're done.
- **Zero cost:** No cloud vector-DB bills. Everything runs locally. The embedding model (`all-MiniLM-L6-v2`, 22M params) runs on CPU in ~50ms per query.
- **Simple API:** ChromaDB's `collection.query()` returns documents, metadata, and distances in a single call. No complex query DSL.
- **Persistence:** Data survives application restarts via `PersistentClient`. Once `setup_data.py` runs, the vector store is available immediately on the next `streamlit run app.py`.
- **Good enough for our scale:** 1,700 documents is well within ChromaDB's sweet spot. Query latency is <100ms.

### Negative
- **Not production-scale:** ChromaDB is not designed for millions of documents or concurrent multi-user access. A production medical platform would need Qdrant, Weaviate, or pgvector behind an API.
- **No hybrid search:** ChromaDB does dense-only retrieval. It doesn't support BM25 (keyword) search. For medical queries where exact drug names or ICD-10 codes matter, keyword matching would improve recall.
- **No built-in re-ranking:** We rely on raw cosine similarity. A cross-encoder re-ranker (e.g., `bge-reranker`) would improve precision but adds complexity.
- **Embedding model is general-purpose:** `all-MiniLM-L6-v2` is not trained on medical text. A domain-specific embedding model (e.g., `PubMedBERT`) would likely perform better for clinical queries.

## Alternatives Considered

| Option | Why rejected |
|--------|-------------|
| **Qdrant** | Excellent production vector DB with hybrid search. Requires running a Docker container or using their cloud. Overkill for a prototype with 1,700 docs. Would be the upgrade path for production. |
| **Pinecone** | Managed cloud vector DB. Free tier exists but requires network access for every query, adding latency. Also introduces a cloud dependency for what should be a local-first tool. |
| **pgvector (Postgres)** | Great if we already had a Postgres DB. Adds unnecessary infrastructure complexity for a Streamlit prototype. Would consider for a Django/FastAPI production backend. |
| **FAISS** | Facebook's vector library. Very fast but no built-in persistence, no metadata filtering, requires more boilerplate code. ChromaDB wraps similar functionality with a cleaner API. |
