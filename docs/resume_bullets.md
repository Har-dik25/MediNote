# Resume Bullets — MediMate: Medical Copilot

Use these 4 bullets on your resume under the project section. Format: **Action verb + Technology + Quantified outcome**.

---

1. **Engineered a zero-cost medical copilot** using Llama 3 (via Groq), LangChain, and ChromaDB that generates evidence-based SOAP notes from doctor-patient transcripts in <2 seconds, with RAG over 1,680 indexed clinical documents.

2. **Built a RAG pipeline** ingesting 20 NICE clinical guidelines, 765 OpenFDA drug reference chunks, and 123 ICD-10 codes into a local ChromaDB vector store, enabling the LLM to cite specific guidelines (e.g., "per NICE NG80") in generated notes.

3. **Implemented safety-first design** including emergency/out-of-scope detection (17 clinical red-flag keywords), mandatory AI disclaimers, and a human-in-the-loop approval workflow to ensure physician oversight before note finalization.

4. **Developed 5 clinical tool functions** — drug interaction checking (OpenFDA API), ICD-10 code suggestion, diagnostic test recommendation, guideline lookup, and drug reference search — with structured logging, 31 automated tests (pytest), and proper error handling across all critical paths.
