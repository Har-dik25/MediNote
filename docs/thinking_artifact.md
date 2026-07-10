# Building a Zero-Cost Medical Copilot with RAG: Why I Chose Local-First Over Cloud APIs

## The Problem Nobody Talks About

Doctors spend an average of 2 hours per day on clinical documentation. That's 2 hours not spent with patients. The electronic health record (EHR) was supposed to fix this, but instead it created a new problem: structured data entry that feels like filling out tax forms after every patient visit.

The idea behind MediMate is simple: **what if an AI could listen to the doctor-patient conversation and draft the clinical note automatically?** The doctor reviews, edits, and approves — but the grunt work of structuring a SOAP note, looking up ICD-10 codes, and cross-referencing drug interactions is handled by the AI.

This is not a new idea. Companies like Suki, Abridge, Nabla, and DeepScribe are building exactly this. But they charge $300-500/month per physician, require cloud infrastructure, and raise serious questions about patient data privacy.

I wanted to build the same thing for **zero dollars**, running entirely on a developer's laptop.

---

## The Architecture Decision That Shaped Everything

The first and most consequential decision was: **where does the LLM run?**

### Option 1: OpenAI / Anthropic APIs
The obvious choice. GPT-4o is excellent at medical reasoning. But:
- **Cost:** Even at $0.005/1K tokens, iterating on prompts during development would cost $20-50. For a student project, that matters.
- **Privacy:** Sending patient transcripts (even synthetic ones) to OpenAI's servers sets a bad precedent. If I'm building a medical tool, I should design it as if real PHI (Protected Health Information) could flow through it.
- **Vendor lock-in:** My prompts, my RAG pipeline, my entire architecture would be coupled to OpenAI's API surface.

### Option 2: Local LLM (Ollama)
The privacy-first choice. But:
- **Speed:** Llama 3 8B on a MacBook Air M1 generates ~15 tokens/second. A typical SOAP note is 400-600 tokens. That's a 30-40 second wait. Doctors won't wait that long.
- **Memory:** The 8B model needs ~5GB RAM. Fine for a developer, but the Whisper model also needs memory, plus ChromaDB, plus Streamlit. It gets tight.

### Option 3: Groq (the decision I made)
Groq runs open models (Llama 3) on custom hardware (LPUs) at ~500 tokens/second. The free tier gives 30 requests/minute. This means:
- **Zero cost** for development and demo
- **Near-instant** SOAP generation (< 2 seconds for a full note)
- **Open model** — I can switch to self-hosted Llama 3 in production without changing my prompts
- **Privacy-ready** — the production path is self-hosted, not cloud-locked

The trade-off? Llama 3 8B is less capable than GPT-4o on complex medical reasoning. But for structured SOAP note generation with RAG context, it's good enough. The guidelines do the heavy lifting; the LLM just organizes them.

---

## RAG: The Part That Actually Matters

Here's a dirty secret about medical AI: **the model doesn't matter as much as the data you feed it.**

A GPT-4o without clinical guidelines will hallucinate drug dosages. A Llama 3 8B with the right NICE guideline chunk in context will cite "per NICE NG80, offer lifestyle advice before pharmacological treatment for hypertension." The RAG context is doing the real work.

### Building the Knowledge Base

I built three data pipelines:

1. **NICE Guidelines Scraper** (`scrape_nice.py`): Downloads 20 key clinical guidelines as PDFs, extracts text, and chunks them into ~500-token segments. Each chunk preserves the guideline source in metadata so the LLM can cite it.

2. **OpenFDA Drug Scraper** (`scrape_drug_data.py`): Fetches drug monographs from the FDA's public API — indications, interactions, warnings, dosages. This powers both the RAG context and the standalone drug interaction checker.

3. **ICD-10 Code Generator** (`scrape_icd10.py`): Generates 123 commonly-used diagnostic codes with descriptions and categories. These are embedded so the system can suggest billing codes based on semantic similarity to the assessment.

The total knowledge base: **1,680 documents** in ChromaDB, embedded with `all-MiniLM-L6-v2`.

### Why ChromaDB?

I needed a vector store that:
- Runs locally (no Docker, no cloud)
- Has persistent storage (survives restarts)
- Is simple to set up (`pip install chromadb`)

ChromaDB fits all three. Is it production-grade? No. Qdrant or pgvector would be the upgrade path. But for a prototype, ChromaDB is the right tool.

---

## Safety: The Non-Negotiable Feature

Medical AI has a unique constraint: **it can kill people if it's wrong.**

I built three safety layers:

1. **Emergency/Out-of-Scope Detection:** A keyword-based scanner that flags transcripts mentioning suicidal ideation, cardiac arrest, anaphylaxis, stroke symptoms, and other emergencies. When triggered, a prominent red banner warns the physician that AI-generated notes should not be used for emergency triage.

2. **Mandatory Disclaimer:** Every SOAP note — whether from the real LLM or the mock fallback — includes an unmovable disclaimer: "AI-GENERATED — NOT A MEDICAL DIAGNOSIS." This cannot be edited out by the physician in the current UI.

3. **Human-in-the-Loop (HITL):** The generated note appears in an editable text area. The physician must explicitly click "Approve & Save" before the note is considered final. There is no auto-save, no background submission.

Is this sufficient for production? No. A real system would need audit logging, role-based access, and integration with the EHR's approval workflow. But for a prototype, these three layers demonstrate that I understand the stakes.

---

## What I'd Do Differently With More Time

1. **Domain-specific embeddings:** Replace `all-MiniLM-L6-v2` with a medical embedding model like `PubMedBERT` or `BioLord`. This would improve RAG retrieval precision for clinical queries.

2. **Hybrid search:** Add BM25 (keyword) search alongside dense retrieval. Drug names and ICD-10 codes are exact-match queries — dense search alone misses them sometimes.

3. **Evaluation framework:** Build a proper eval pipeline with 50 curated transcripts, measuring SOAP completeness, ICD-10 accuracy, and hallucination rate. Use LLM-as-judge for scalable evaluation.

4. **Streaming output:** Use Groq's streaming API to show the SOAP note generating in real-time, token by token. This dramatically improves perceived speed.

5. **Fine-tuning:** QLoRA fine-tune Llama 3 8B on a dataset of real SOAP notes (using synthetic data bootstrapped from GPT-4o). This would make the model natively understand SOAP formatting without relying on prompt engineering.

---

## The Takeaway

Building a medical copilot is 20% LLM and 80% everything else: data pipelines, RAG architecture, safety guardrails, UX design, and the boring-but-critical work of making it actually runnable by someone who isn't you.

The zero-cost constraint forced better engineering decisions: local-first architecture, open models, public data sources. These aren't compromises — they're the foundation of a system that could actually be deployed in a hospital without a $10,000/month cloud bill.

**MediMate is not a product. It's a proof of architecture.** And that architecture — RAG over clinical guidelines, open LLM inference, local vector store, safety-first design — is exactly what production medical AI looks like, minus the compliance team.
