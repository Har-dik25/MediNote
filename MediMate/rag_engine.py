"""
RAG Engine
==========
Retrieval-Augmented Generation engine for MediMate.

Uses ChromaDB for persistent local vector storage and
sentence-transformers for free, local embeddings.

Collections:
  - nice_guidelines: NICE clinical guideline recommendations
  - icd10_codes: ICD-10-CM diagnosis codes
  - drug_reference: Drug labels from OpenFDA
"""

import os
from typing import List, Dict, Optional

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from data_processor import process_all_data


# --- Configuration ---
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Small, fast, free, good quality
CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "data", "chroma_db")

# Collection names
COLLECTION_NICE = "nice_guidelines"
COLLECTION_ICD10 = "icd10_codes"
COLLECTION_DRUGS = "drug_reference"

# Singleton instances
_embedding_model = None
_chroma_client = None


def _get_embedding_model():
    """Lazy-load the embedding model (singleton)."""
    global _embedding_model
    if _embedding_model is None:
        if SentenceTransformer is None:
            raise ImportError(
                "sentence-transformers is required. Install with: pip install sentence-transformers"
            )
        print("Loading embedding model (first time only)...")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def _get_chroma_client():
    """Lazy-load the ChromaDB client (singleton)."""
    global _chroma_client
    if _chroma_client is None:
        if chromadb is None:
            raise ImportError(
                "chromadb is required. Install with: pip install chromadb"
            )
        os.makedirs(CHROMA_DB_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    return _chroma_client


try:
    from chromadb import EmbeddingFunction as ChromaEmbeddingFunction
except ImportError:
    ChromaEmbeddingFunction = object

class EmbeddingFunction(ChromaEmbeddingFunction):
    """Custom embedding function for ChromaDB using sentence-transformers."""

    def __init__(self):
        self.model = _get_embedding_model()

    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(input, show_progress_bar=False)
        return embeddings.tolist()


def _get_or_create_collection(name: str):
    """Get or create a ChromaDB collection with our embedding function."""
    client = _get_chroma_client()
    ef = EmbeddingFunction()
    return client.get_or_create_collection(
        name=name,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )


def build_vector_store(data_dir: str = None, force_rebuild: bool = False):
    """
    Build the ChromaDB vector store from processed data.
    
    Args:
        data_dir: Path to the data directory (defaults to ./data)
        force_rebuild: If True, delete existing collections and rebuild from scratch
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data")

    client = _get_chroma_client()

    # Check if collections already exist with data
    if not force_rebuild:
        try:
            nice_col = client.get_collection(COLLECTION_NICE)
            if nice_col.count() > 0:
                print(f"Vector store already populated ({nice_col.count()} NICE docs). "
                      "Use force_rebuild=True to rebuild.")
                return
        except Exception:
            pass  # Collection doesn't exist yet

    # Delete existing collections if rebuilding
    if force_rebuild:
        for name in [COLLECTION_NICE, COLLECTION_ICD10, COLLECTION_DRUGS]:
            try:
                client.delete_collection(name)
                print(f"  🗑️  Deleted existing collection: {name}")
            except Exception:
                pass

    # Process all data
    all_docs = process_all_data(data_dir)

    # Build each collection
    _build_collection(COLLECTION_NICE, all_docs.get("nice_guidelines", []))
    _build_collection(COLLECTION_ICD10, all_docs.get("icd10_codes", []))
    _build_collection(COLLECTION_DRUGS, all_docs.get("drug_reference", []))

    print("\n✅ Vector store built successfully!")


def _build_collection(name: str, documents: List[Dict]):
    """Build a single ChromaDB collection from document dicts."""
    if not documents:
        print(f"  ⚠️  No documents for collection '{name}'. Skipping.")
        return

    print(f"\n  📦 Building collection '{name}' with {len(documents)} documents...")

    collection = _get_or_create_collection(name)

    # ChromaDB has batch size limits, process in batches
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        ids = [doc["metadata"]["chunk_id"] for doc in batch]
        texts = [doc["text"] for doc in batch]
        metadatas = [doc["metadata"] for doc in batch]

        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
        )
        print(f"    Added batch {i // batch_size + 1} ({len(batch)} docs)")

    print(f"  ✅ Collection '{name}': {collection.count()} documents indexed.")


# --- Search Functions ---

def search_guidelines(query: str, top_k: int = 3) -> List[Dict]:
    """
    Search NICE guidelines for relevant clinical recommendations.
    
    Args:
        query: Clinical question or condition description
        top_k: Number of results to return
        
    Returns:
        List of dicts with 'text', 'metadata', and 'distance' keys
    """
    try:
        collection = _get_or_create_collection(COLLECTION_NICE)
        if collection.count() == 0:
            return []

        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, collection.count()),
        )

        return _format_results(results)
    except Exception as e:
        print(f"Error searching guidelines: {e}")
        return []


def search_icd10(query: str, top_k: int = 5) -> List[Dict]:
    """
    Search ICD-10 codes matching a clinical description.
    
    Args:
        query: Clinical condition or symptom description
        top_k: Number of results to return
        
    Returns:
        List of dicts with ICD-10 code info
    """
    try:
        collection = _get_or_create_collection(COLLECTION_ICD10)
        if collection.count() == 0:
            return []

        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, collection.count()),
        )

        return _format_results(results)
    except Exception as e:
        print(f"Error searching ICD-10: {e}")
        return []


def search_drugs(query: str, top_k: int = 3) -> List[Dict]:
    """
    Search drug reference data.
    
    Args:
        query: Drug name, condition, or interaction query
        top_k: Number of results to return
        
    Returns:
        List of dicts with drug information
    """
    try:
        collection = _get_or_create_collection(COLLECTION_DRUGS)
        if collection.count() == 0:
            return []

        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, collection.count()),
        )

        return _format_results(results)
    except Exception as e:
        print(f"Error searching drugs: {e}")
        return []


def search_all(query: str, top_k: int = 3) -> Dict[str, List[Dict]]:
    """
    Search across all collections and return combined results.
    
    Args:
        query: Clinical question
        top_k: Number of results per collection
        
    Returns:
        Dict with results from each collection
    """
    return {
        "guidelines": search_guidelines(query, top_k),
        "icd10_codes": search_icd10(query, top_k),
        "drugs": search_drugs(query, top_k),
    }


def _format_results(results) -> List[Dict]:
    """Format ChromaDB query results into a clean list of dicts."""
    formatted = []
    if results and results.get("documents"):
        for i, doc in enumerate(results["documents"][0]):
            entry = {
                "text": doc,
                "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                "distance": results["distances"][0][i] if results.get("distances") else None,
            }
            formatted.append(entry)
    return formatted


def get_collection_stats() -> Dict:
    """Return statistics about the vector store collections."""
    try:
        client = _get_chroma_client()
        stats = {}
        for name in [COLLECTION_NICE, COLLECTION_ICD10, COLLECTION_DRUGS]:
            try:
                col = client.get_collection(name)
                stats[name] = col.count()
            except Exception:
                stats[name] = 0
        return stats
    except Exception:
        return {COLLECTION_NICE: 0, COLLECTION_ICD10: 0, COLLECTION_DRUGS: 0}


if __name__ == "__main__":
    print("Building vector store...\n")
    build_vector_store(force_rebuild=True)

    print("\n\n--- Testing Search ---\n")

    print("🔍 Searching guidelines for 'asthma management':")
    for r in search_guidelines("asthma management", top_k=2):
        print(f"  [{r['metadata'].get('guideline', '?')}] (dist={r['distance']:.3f})")
        print(f"  {r['text'][:150]}...\n")

    print("🔍 Searching ICD-10 for 'type 2 diabetes':")
    for r in search_icd10("type 2 diabetes", top_k=3):
        print(f"  {r['metadata'].get('code', '?')}: {r['text'][:100]}\n")

    print("🔍 Searching drugs for 'metformin':")
    for r in search_drugs("metformin", top_k=1):
        print(f"  {r['text'][:200]}...\n")
