# ADR-002: Choosing ChromaDB as the Vector Database

## Context
To power the Retrieval-Augmented Generation (RAG) pipeline with NICE guidelines and ICD-10 codes, we needed a vector database to store and query dense embeddings. The system requires low-latency cosine similarity search across ~800 documents.

## Decision
We chose **ChromaDB running in local persistent mode** (SQLite backend).

## Consequences
**Positive:**
- **Zero Infrastructure:** No need to spin up a Docker container, provision a cloud database, or manage API keys.
- **Portability:** The entire knowledge base lives in a local `/data` folder, making the repository easy to clone and run immediately.
- **Free:** Completely open-source with no usage tiers.

**Negative:**
- **Scalability Limitations:** SQLite-backed ChromaDB is not designed for massive concurrency or billion-vector scale.
- **Tightly Coupled:** The database state is tied to the local filesystem, making multi-node deployments harder without migrating to a client/server model.

## Alternatives considered
- **Pinecone / Weaviate Cloud:** Rejected because they introduce an external dependency and potential costs for the end user, breaking the "zero-cost, local-first" project philosophy.
- **pgvector (PostgreSQL):** Rejected because it requires the user to have PostgreSQL installed and configured, adding significant friction to the setup process.
