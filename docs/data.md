# MediMate: Data Sources & Knowledge Base

This document outlines the external data sources used to populate MediMate's local ChromaDB vector store, providing the foundational knowledge for our Retrieval-Augmented Generation (RAG) pipeline and clinical tools.

## 1. Overview of Data Pipeline

MediMate relies on authoritative, evidence-based medical data rather than the innate (and potentially hallucinated) knowledge of the LLM. During the initialization phase (`setup_data.py`), the system ingests data from three primary public sources, chunks it, embeds it using `all-MiniLM-L6-v2`, and stores it in three distinct ChromaDB collections:
1. `nice_guidelines`
2. `icd10_codes`
3. `drug_reference`

Total Indexed Documents: **792 chunks**

---

## 2. Primary Data Sources

### A. NICE Clinical Guidelines
- **Source:** National Institute for Health and Care Excellence (UK)
- **Purpose:** Provides evidence-based recommendations for health and care. Used by the RAG orchestrator to ground the "Plan" section of the SOAP note and suggest diagnostic tests.
- **Data Extracted:** Condition name, diagnostic criteria, treatment pathways, prescribing guidelines.
- **License/Usage:** Public sector information licensed under the Open Government Licence v3.0. Acknowledged as public domain reference material for prototyping.
- **Update Frequency:** Static snapshot taken at initialization. In production, this would be synced via a monthly cron job.

### B. OpenFDA (Food and Drug Administration)
- **Source:** [openFDA API](https://open.fda.gov/apis/) (`https://api.fda.gov/drug/`)
- **Purpose:** Used primarily by the Drug Interaction Checker tool. When the LLM extracts two or more medications from the transcript, the backend queries OpenFDA for known adverse events and interactions.
- **Data Extracted:** Drug labels, active ingredients, boxed warnings, adverse event reports.
- **License/Usage:** Public domain data provided by the US Government. 
- **API Limits:** Free tier allows 240 requests/minute (sufficient for local copilot usage).

### C. ICD-10-CM Database
- **Source:** Centers for Disease Control and Prevention (CDC) / World Health Organization (WHO)
- **Purpose:** Powers the automated billing and diagnostic coding suggestions. The RAG pipeline matches extracted symptoms/conditions to the closest semantic ICD-10 description.
- **Data Extracted:** ICD-10 Code (e.g., `E11.9`), Short Description, Category.
- **License/Usage:** Public domain classification system.

---

## 3. Data Schema & Processing

### Chunking Strategy
To ensure optimal retrieval quality without exceeding the LLM context window, data is processed as follows:
- **NICE Guidelines:** Split into ~500 token chunks with a 50-token overlap.
- **ICD-10:** Treated as single-sentence semantic units (Code + Description).
- **Drug Labels:** Summarized into indication and interaction paragraphs before embedding.

### Vector Schema (ChromaDB)
Each document inserted into ChromaDB follows this metadata schema:
```json
{
  "id": "guideline_ng136_chunk2",
  "text": "For adults with hypertension, offer step 1 treatment with an ACE inhibitor...",
  "metadata": {
    "source": "NICE NG136",
    "category": "Cardiovascular",
    "last_updated": "2023-08-15"
  }
}
```

## 4. Privacy & Data Handling
- **No Patient Data Stored:** The vector database contains *only* medical reference material. No patient transcripts, PII, or PHI are ever inserted into the RAG database.
- **Local Persistence:** The ChromaDB instance uses SQLite persistence locally in the `/data` folder. No medical reference data is sent to external cloud vector databases (e.g., Pinecone), ensuring zero-cost operation and offline availability.
