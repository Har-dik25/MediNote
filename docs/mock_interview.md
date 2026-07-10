# Mock Interview Q&A — MediMate: Medical Copilot

10 questions a technical interviewer might ask about this project, with detailed answers.

---

## Q1: Walk me through the architecture. How does a doctor's voice recording become a SOAP note?

**A:** The pipeline has four stages:
1. **Audio → Text:** The uploaded audio file (MP3/WAV) is transcribed locally using HuggingFace's Whisper model (`whisper-tiny`). This runs on CPU, zero cost.
2. **Text → RAG Context:** The transcript is used as a query against three ChromaDB collections (NICE guidelines, ICD-10 codes, drug reference). We retrieve the top 3 guideline chunks, top 5 ICD-10 codes, and top 2 drug information chunks. This gives the LLM evidence to cite.
3. **Transcript + Context → SOAP Note:** Both are injected into a structured prompt template and sent to Llama 3 8B via Groq's API. The prompt instructs the model to format the output as Subjective/Objective/Assessment/Plan with guideline citations.
4. **SOAP Note → HITL Review:** The generated note appears in an editable text area in the Streamlit UI. The doctor reviews, edits, and clicks "Approve & Save."

---

## Q2: Why did you choose Groq over OpenAI or running Llama locally?

**A:** Three reasons:
- **Cost:** Groq's free tier gives 30 req/min. OpenAI would cost $20-50 over a development cycle. For a student project, that matters.
- **Speed:** Groq's LPU hardware delivers ~500 tokens/sec, making SOAP generation feel instant (<2s). Local Llama on CPU takes 30-40 seconds — doctors won't wait.
- **Privacy path:** Since we're using an open model (Llama 3), the production path is self-hosted inference behind a hospital firewall. If we'd built on GPT-4, we'd be locked into sending PHI to OpenAI forever.

---

## Q3: How does your RAG pipeline work? What's the chunking strategy?

**A:** The data processor (`data_processor.py`) handles chunking differently per source:
- **NICE Guidelines:** Semantic chunking at ~500 tokens, preserving paragraph boundaries and section headers. Each chunk carries metadata (`guideline` name, `chunk_id`).
- **Drug Reference:** Structured by drug — each drug's monograph is split into sections (indications, interactions, warnings, dosage). Each section is a chunk.
- **ICD-10 Codes:** Each code is a single document with the code, description, and category as both text and metadata.

All chunks are embedded using `all-MiniLM-L6-v2` (22M params, runs on CPU in ~50ms/query) and stored in ChromaDB with `PersistentClient`.

---

## Q4: How do you handle patient safety? What if the AI hallucinates a drug dosage?

**A:** Three layers:
1. **Emergency detection:** A keyword scanner checks for 17 clinical red flags (suicidal ideation, cardiac arrest, anaphylaxis, etc.). If triggered, a red banner warns the doctor that AI notes should not be used for emergency triage.
2. **Mandatory disclaimer:** Every output includes an unremovable "AI-GENERATED — NOT A MEDICAL DIAGNOSIS" disclaimer. The LLM is explicitly instructed to refuse to finalize any diagnosis.
3. **HITL checkpoint:** The note is placed in an editable text area. The doctor must click "Approve & Save" — there's no auto-save. This is the critical safety gate.

Is this sufficient for production? No — we'd need audit logging, per-note provenance tracking, and EHR integration. But it demonstrates awareness of the stakes.

---

## Q5: What would you change if you had to make this production-ready for a hospital?

**A:** Five things:
1. **Self-hosted LLM:** Move from Groq's API to vLLM or TGI running Llama 3 behind the hospital's firewall. PHI can never leave the network.
2. **Domain-specific embeddings:** Replace `all-MiniLM-L6-v2` with PubMedBERT or BioLord for better clinical retrieval.
3. **Hybrid search:** Add BM25 keyword search alongside dense retrieval. Drug names and ICD-10 codes need exact matching.
4. **Audit trail:** Every generated note logged with: timestamp, input hash, RAG context used, model version, physician approval timestamp.
5. **EHR integration:** FHIR (HL7) API integration to push approved notes directly into the patient's chart.

---

## Q6: How did you evaluate the quality of the generated SOAP notes?

**A:** In the current version, evaluation is primarily manual — I review generated notes against the source transcript for completeness and accuracy. The system also has built-in quality signals: RAG status (was guideline context used?), ICD-10 relevance scores, and safety flags.

For a more rigorous evaluation, I'd build: (a) a dataset of 50 curated transcripts with gold-standard SOAP notes, (b) automated metrics for SOAP section completeness, ICD-10 accuracy, and hallucination detection, and (c) LLM-as-judge for overall note quality.

---

## Q7: Why ChromaDB instead of Qdrant, Pinecone, or pgvector?

**A:** ChromaDB was the right tool for this scope:
- **Zero infrastructure:** It's a Python library, not a server. `pip install chromadb` and you're done.
- **Persistent storage:** Data survives restarts via SQLite backend.
- **1,700 documents:** This is ChromaDB's sweet spot. We don't need Qdrant's millions-of-vectors performance.

For production, I'd move to Qdrant (supports hybrid search, scales horizontally, has built-in filtering) or pgvector (if we already have a Postgres database for the application).

---

## Q8: How do you handle the case where the RAG context is empty or irrelevant?

**A:** Graceful degradation:
- If ChromaDB is empty (setup hasn't run), the app shows a sidebar warning and generates notes using `SOAP_PROMPT_BASIC` (no guideline context).
- If ChromaDB is populated but no relevant results are found for a query, the LLM gets the basic prompt and generates based on its own training knowledge.
- The UI explicitly tells the doctor whether RAG was used: "📚 RAG-Augmented" (green) vs "ℹ️ Generated without guideline context" (grey).

This way the app never crashes — it just produces a less evidence-based note and tells the user.

---

## Q9: What's the most interesting bug you encountered?

**A:** The LangChain import breakage. The project was built with `langchain`, but the library restructured its packages — `PromptTemplate` moved from `langchain.prompts` to `langchain_core.prompts`. The app would crash on startup with `ModuleNotFoundError: No module named 'langchain.prompts'`.

The fix was a one-line import change, but the lesson was bigger: **pin your dependencies**. In production, `requirements.txt` should use exact versions (`langchain-core==1.4.9`) not just package names. I also learned to check the library's migration guide before upgrading.

---

## Q10: If you were interviewing a candidate who built this project, what would you look for?

**A:** Four things:
1. **Do they understand RAG deeply?** Not just "I used LangChain." Can they explain chunking strategies, embedding model trade-offs, retrieval vs generation quality?
2. **Do they understand safety?** Medical AI without safety guardrails is dangerous. I'd want to hear about disclaimers, HITL, emergency detection, and the limits of AI-generated clinical content.
3. **Can they justify their architecture decisions?** Why Groq over OpenAI? Why ChromaDB over Pinecone? The ADRs should tell a coherent story.
4. **Can they talk about what's missing?** A good engineer knows what they didn't build and why. Hybrid search, domain-specific embeddings, proper eval — these are honest gaps, not failures.
