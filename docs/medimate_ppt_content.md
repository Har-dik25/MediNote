# MediMate — PPT Slide Content

> Ready-to-use content for each slide. Copy directly into your PowerPoint.

---

## Slide 1 — Title Slide

**Title:** MediMate: Your AI Medical Copilot

**Subtitle:** A Zero-Cost, Real-Time Clinical Assistant That Transforms Doctor-Patient Conversations into Evidence-Based SOAP Notes

**Presented by:** [Your Name]
**Internship:** B.Tech CSE-AIDE | Segment 5 — LLM Systems & Applied GenAI
**Duration:** 22 June – 26 July 2026

> [!TIP]
> Use the MediMate logo or a stethoscope + AI brain icon. Keep background clean and medical-themed (dark teal or navy blue gradient).

---

## Slide 2 — Problem Statement

**Title:** The Documentation Crisis in Healthcare

**Key Points:**
- Physicians spend **~2 hours on EHR documentation** for every 1 hour of patient care (AMA, 2024)
- **49% of physicians** report symptoms of burnout, with administrative tasks cited as the leading cause
- **Truncated consultations** — patients receive less face-time as doctors rush to catch up on notes
- Existing AI scribing solutions cost **$300–$1,000/month** per provider, locking out small clinics and resource-constrained systems

**Impact Statement:**
> *"Doctors became doctors to heal people, not to fill forms. MediMate gives them their time back — at zero cost."*

**Visual Suggestion:** Split graphic — left side: doctor buried in paperwork; right side: doctor engaging with patient while AI assists.

---

## Slide 3 — Solution Overview

**Title:** What MediMate Does

**Core Capabilities (4 icons in a row):**

| 🎙️ Real-Time Transcription | 📝 SOAP Note Generation | 📚 Evidence-Based RAG | ⚠️ Safety & Interaction Checks |
|---|---|---|---|
| Local Whisper model transcribes audio with full privacy — no data leaves the clinic | Llama 3 70B via Groq generates structured Subjective, Objective, Assessment & Plan notes in <2 seconds | 792 embedded NICE guideline chunks + ICD-10 codes + OpenFDA drug data ground every recommendation | Automatic drug interaction checking via OpenFDA + emergency keyword detection for clinical safety |

**Bottom Tagline:** Fully functional on standard hardware. No GPU required. No API subscriptions. Zero cost.

---

## Slide 4 — Key Features (Deep Dive)

**Title:** Feature Breakdown

**Feature 1 — Audio & Text Input**
- Record live audio directly in the browser or upload .mp3/.wav files
- Alternatively, type or paste an encounter transcript
- Local Whisper engine ensures HIPAA/GDPR-compliant transcription (audio never leaves the device)

**Feature 2 — Automated SOAP Notes with RAG**
- Generates structured notes with: Subjective, Objective, Assessment, Plan
- RAG retrieves relevant NICE clinical guidelines and cites them (e.g., "per NICE NG136")
- Suggests ICD-10 codes with relevance scoring
- Recommends diagnostic tests extracted from guideline text

**Feature 3 — Clinical Safety Tooling**
- 🚨 **Emergency detection:** Flags keywords like "suicidal", "cardiac arrest", "anaphylaxis" — 20+ emergency indicators
- 💊 **Drug interaction checker:** Cross-references prescribed medications against OpenFDA adverse event reports
- 📖 **NICE guideline lookup:** On-demand search of embedded clinical guidelines
- 🔍 **Drug reference lookup:** Instant drug information from local vector store

**Feature 4 — Physician Workflow**
- Rich-text editing of generated notes (ReactQuill WYSIWYG editor)
- Draft → Approve workflow with status tracking
- One-click "Copy to EHR" and Print Note functionality
- AI-generated disclaimer on every note for legal compliance

---

## Slide 5 — System Architecture

**Title:** Architecture — Local-First Hybrid Design

**Diagram Description (use the Mermaid diagram from your repo, or recreate visually):**

```
┌─────────────────────────────────────────────────┐
│                MediMate System                  │
│                                                 │
│  ┌──────────┐    ┌──────────┐    ┌───────────┐  │
│  │ React UI │───▶│ Whisper  │───▶│   RAG     │  │
│  │ (Vite)   │    │ Engine   │    │Orchestrator│  │
│  └──────────┘    │ (Local)  │    │(LangChain)│  │
│       │          └──────────┘    └─────┬─────┘  │
│       │                                │        │
│       ▼                                ▼        │
│  ┌──────────┐                    ┌───────────┐  │
│  │ FastAPI  │                    │ ChromaDB  │  │
│  │ Backend  │                    │(792 docs) │  │
│  └──────────┘                    └───────────┘  │
└─────────────────────────┬───────────────────────┘
                          │
                          ▼
              ┌───────────────────┐
              │  Groq API (Cloud) │
              │  Llama 3.3 70B   │
              │  800+ tok/sec     │
              │  Free Tier        │
              └───────────────────┘
```

**Key Design Decisions:**
1. **Audio transcription runs locally** — raw audio never leaves the clinic's network (privacy by design)
2. **Vector DB is local-only** — ChromaDB with SQLite backend, no external server dependency
3. **Only LLM inference is cloud-based** — Groq's LPU delivers 800+ tokens/sec at zero cost
4. **Graceful degradation** — app works fully in mock mode without any API key

---

## Slide 6 — Technology Stack

**Title:** Technology Stack

| Layer | Technology | Why This Choice |
|-------|-----------|----------------|
| **Frontend** | React 18 + Vite | Fast HMR, component-based UI with Framer Motion animations |
| **Backend API** | FastAPI (Python) | Async endpoints, automatic OpenAPI docs, Pydantic validation |
| **Audio Transcription** | HuggingFace Whisper (Local) | Privacy-preserving, accurate, runs on CPU without GPU |
| **LLM** | Llama 3.3 70B via Groq | 800+ tok/sec inference, highly capable, free tier available |
| **Orchestration** | LangChain | Standardized prompt templating, chain composition, retriever interface |
| **Vector Database** | ChromaDB (Persistent) | Local SQLite-backed storage, cosine similarity, no server needed |
| **Embeddings** | all-MiniLM-L6-v2 | Fast, lightweight (80MB), high-quality dense embeddings, runs locally |
| **Data Sources** | NICE Guidelines, OpenFDA, ICD-10 | Authoritative clinical references for evidence-based outputs |

---

## Slide 7 — RAG Pipeline (Technical Deep Dive)

**Title:** RAG Pipeline — How Evidence-Based Notes are Generated

**Step-by-step flow:**

1. **Data Ingestion (One-time Setup)**
   - Scrape NICE clinical guidelines → chunk into ~500 token passages
   - Fetch ICD-10-CM codes with descriptions and categories
   - Pull drug labels and interaction data from OpenFDA API
   - Total: **792 document chunks** indexed across 3 collections

2. **Embedding & Storage**
   - Each chunk embedded using `all-MiniLM-L6-v2` (384-dim vectors)
   - Stored in ChromaDB with cosine similarity indexing (HNSW)
   - Three collections: `nice_guidelines`, `icd10_codes`, `drug_reference`

3. **Query-Time Retrieval**
   - Transcript → keyword extraction → parallel vector search across all 3 collections
   - Top-k results (3 guidelines, 5 ICD-10, 2 drug refs) retrieved by cosine similarity

4. **Augmented Generation**
   - Retrieved context injected into a structured prompt template
   - Llama 3.3 70B generates SOAP note with explicit guideline citations
   - Safety disclaimer automatically appended

**Key Metric:** Notes cite specific NICE guidelines (e.g., "per NICE NG136") — not hallucinated references.

---

## Slide 8 — Safety & Compliance

**Title:** Built-in Clinical Safety Guardrails

**1. Emergency / Out-of-Scope Detection**
- Automatic scanning for **20+ emergency keywords**: suicidal, cardiac arrest, anaphylaxis, seizure, hemorrhage, etc.
- Triggers a 🚨 **RED ALERT banner** in the UI with escalation guidance
- Explicitly warns: "AI-generated notes should NOT be relied upon for emergency triage"

**2. Mandatory AI Disclaimer**
- Every generated note includes a non-removable disclaimer:
  > *"This SOAP note is AI-generated and intended as a DRAFT for physician review only. It does NOT constitute a medical diagnosis."*

**3. Drug Interaction Checking**
- Real-time query against OpenFDA's adverse event database
- Reports total adverse events + sample co-reported reactions
- Cross-references with local drug reference data for comprehensive safety

**4. Draft → Approve Workflow**
- Notes are generated as "Draft" status — cannot be exported until a physician explicitly clicks "Approve and Save"
- Full audit trail with timestamps

---

## Slide 9 — Frontend UI Walkthrough

**Title:** User Interface — Clinician-First Design

**Pages in the Application:**

| Page | Purpose |
|------|---------|
| **Login / Signup** | Secure authentication with form validation |
| **Encounter Page** | Main workspace — audio recording, text input, SOAP note generation |
| **Patient List** | Browse and manage patient records |
| **Patient Profile** | Individual patient details and encounter history |
| **Note History** | View all past generated notes with status tracking |
| **Settings** | Application preferences and configuration |

**Encounter Page Highlights:**
- **Left panel:** Audio recorder / text input with tab switching
- **Right panel:** Generated SOAP note with inline rich-text editing (ReactQuill)
- **Clinical tools accordion:** Drug interactions, NICE guidelines, Drug lookup — auto-populated from the note
- **ICD-10 & Test suggestions** displayed as animated chip cards with relevance scores
- **Dashboard stats:** Patients seen today, pending drafts, time saved

> [!TIP]
> Include 2-3 screenshots of the actual running application here.

---

## Slide 10 — API Design

**Title:** RESTful API Design (FastAPI)

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check + RAG database status |
| `POST` | `/api/generate-soap/text` | Generate SOAP note from text transcript |
| `POST` | `/api/generate-soap/audio` | Transcribe audio + generate SOAP note |
| `POST` | `/api/tools/drug-interaction` | Check drug interaction via OpenFDA |
| `GET` | `/api/tools/guidelines` | Search NICE guidelines |
| `GET` | `/api/tools/drug-info` | Look up drug information |
| `POST` | `/api/tools/icd10` | Suggest ICD-10 codes |
| `POST` | `/api/tools/tests` | Suggest diagnostic tests |

**Design Principles:**
- CORS-enabled for frontend-backend communication
- Pydantic models for request validation
- Structured JSON responses with error handling
- Auto-generated OpenAPI/Swagger documentation at `/docs`

---

## Slide 11 — Clinical Entity Extraction

**Title:** Automatic Clinical Entity Extraction

**How it works:**
- After generating the SOAP note, a **secondary LLM call** (Llama 3.3 70B in JSON mode) extracts:
  - **Drugs** mentioned in the transcript + note (up to 2)
  - **Primary condition** / diagnosis

**Why it matters:**
- Extracted entities **auto-populate the clinical tools** in the sidebar:
  - Drug 1 + Drug 2 → auto-checked for interactions
  - Condition → auto-searched in NICE guidelines
  - Drug 1 → auto-looked up in drug reference

**Result:** A single "Generate" click triggers a **cascade of clinical intelligence** — SOAP note + ICD-10 codes + diagnostic tests + drug interactions + guideline lookup — all in under 5 seconds.

---

## Slide 12 — Zero-Cost Architecture

**Title:** Zero-Cost Design Philosophy

| Component | Cost | Alternative (Market Rate) |
|-----------|------|--------------------------|
| Groq API (Llama 3.3 70B) | **Free** (free tier) | GPT-4 API: ~$30/1M tokens |
| Whisper (local CPU) | **Free** | Cloud speech APIs: $0.006–$0.024/min |
| ChromaDB (local) | **Free** | Pinecone: $70+/month |
| all-MiniLM-L6-v2 embeddings | **Free** (local) | OpenAI embeddings: $0.13/1M tokens |
| NICE Guidelines data | **Free** (public) | Clinical NLP APIs: $500+/month |
| OpenFDA API | **Free** (public) | Drug interaction databases: $200+/month |
| FastAPI + React hosting | **Free** (local / free tier) | Cloud hosting: $20+/month |

**Total running cost: $0/month**
**Equivalent commercial solution: $800–$1,500+/month**

**Graceful Degradation:** Even without the Groq API key, the app runs fully in mock mode with all UI features functional.

---

## Slide 13 — Data Pipeline

**Title:** Knowledge Base Construction Pipeline

**One-time setup (`setup_data.py` → ~8 minutes):**

```
1. NICE Guidelines Scraper (scrape_nice.py)
   └─ Scrapes NICE clinical guideline recommendations
   └─ Chunks into ~500 token passages with metadata

2. ICD-10 Scraper (scrape_icd10.py)
   └─ Fetches ICD-10-CM diagnosis codes
   └─ Structures code + description + category

3. Drug Data Scraper (scrape_drug_data.py)
   └─ Pulls drug labels from OpenFDA API
   └─ Extracts indications, warnings, interactions

4. Data Processor (data_processor.py)
   └─ Normalizes, deduplicates, assigns chunk IDs
   └─ Prepares metadata for vector indexing

5. RAG Engine (rag_engine.py)
   └─ Embeds all documents using all-MiniLM-L6-v2
   └─ Indexes into ChromaDB (3 collections)
   └─ Total: 792 document chunks
```

---

## Slide 14 — Engineering Practices

**Title:** Production-Grade Engineering

**Code Quality:**
- ✅ Structured logging with `logger.py` — request/response timing, success/failure tracking
- ✅ Comprehensive error handling — graceful degradation at every layer
- ✅ Type hints and docstrings on all public functions
- ✅ Pydantic models for API request validation

**Testing:**
- ✅ Automated test suite with `pytest`
- ✅ Unit tests for core modules (RAG, LLM, tools)
- ✅ Run: `python -m pytest tests/ -v`

**Developer Experience:**
- ✅ Clean Git history with meaningful commits
- ✅ Comprehensive README with quickstart guide
- ✅ Environment variable management via `.env` + `python-dotenv`
- ✅ Architecture Decision Records (ADRs)

**Observability:**
- ✅ Every API call logged with: function name, input preview, elapsed time (ms), success/failure, mode (mock/llm/rag)
- ✅ Health check endpoint (`/api/health`) reports RAG availability and collection statistics

---

## Slide 15 — Demo Flow

**Title:** Live Demo Walkthrough

**Step 1:** Open MediMate → Login

**Step 2:** Navigate to "New Encounter" page

**Step 3:** Choose input method:
- **Option A:** Click Record → Speak a sample doctor-patient conversation → Stop recording
- **Option B:** Paste a sample transcript into the text box

**Step 4:** Click **"Generate SOAP Note"** → Watch the magic happen:
- SOAP note appears with animated sections (Subjective → Objective → Assessment → Plan)
- ICD-10 code suggestions populate with relevance scores
- Diagnostic test recommendations appear
- Clinical tools auto-expand with pre-filled drug interactions & guideline lookups

**Step 5:** Review the note → Click **"Edit note"** → Make physician modifications → Save

**Step 6:** Click **"Approve and save"** → Status changes from Draft → Approved

**Step 7:** Click **"Copy to EHR"** or **"Print Note"**

> [!IMPORTANT]
> Keep a sample transcript ready for the demo. Suggested: "Patient presents with persistent cough for three weeks, mild fever of 100.2°F, no shortness of breath. History of Type 2 diabetes managed with Metformin 500mg. Currently also taking Lisinopril 10mg for hypertension."

---

## Slide 16 — Challenges & Solutions

**Title:** Challenges Faced & How I Solved Them

| Challenge | Solution |
|-----------|----------|
| **LLM hallucinating medical facts** | Implemented RAG with 792 authoritative NICE guideline chunks — forces citations like "per NICE NG136" |
| **Audio privacy concerns (HIPAA/GDPR)** | Runs Whisper locally on CPU — raw audio never leaves the device |
| **Expensive API costs** | Zero-cost stack: Groq free tier + local embeddings + ChromaDB + public APIs |
| **Slow LLM inference** | Groq's LPU architecture delivers 800+ tokens/sec — notes generate in <2 seconds |
| **Ensuring clinical safety** | Multi-layer safety: emergency keyword detection, mandatory AI disclaimers, draft-approve workflow |
| **Extracting structured data from notes** | Secondary LLM call in JSON mode for entity extraction, auto-populating clinical tools |

---

## Slide 17 — Future Roadmap

**Title:** Future Roadmap

**Short-term (Next 2 Weeks):**
- 🔌 **FHIR / HL7 Integration** — Export SOAP notes directly into standard EHR systems (Epic, Cerner)
- 🏠 **Local LLM (Ollama)** — Run 4-bit quantized Llama 3 on-device, eliminating all cloud dependency
- 🗣️ **Multi-Speaker Diarization** — Attribute transcript text to "Doctor" vs "Patient" automatically

**Medium-term:**
- 🌍 **Expanded Knowledge Base** — Integrate CDC, WHO, and NHS guidelines alongside NICE
- 📊 **Analytics Dashboard** — Track documentation time saved, note quality metrics, usage patterns
- 🔒 **Role-Based Access Control** — Differentiate permissions for doctors, nurses, and admin staff

**Long-term Vision:**
- 🧠 **Specialty-Specific Models** — Fine-tuned models for Cardiology, Dermatology, Pediatrics
- 📱 **Mobile Application** — Point-of-care documentation on tablets and phones
- 🏥 **Multi-Clinic Deployment** — Shared knowledge base across practice locations

---

## Slide 18 — Impact & Results

**Title:** Impact & Key Metrics

| Metric | Value |
|--------|-------|
| **Documentation time reduction** | ~15 minutes/encounter → ~2 minutes (est. **87% reduction**) |
| **SOAP note generation speed** | < 2 seconds (800+ tok/sec via Groq LPU) |
| **Knowledge base coverage** | 792 clinical document chunks across NICE guidelines, ICD-10, OpenFDA |
| **Monthly operating cost** | **$0** (all free-tier / local infrastructure) |
| **Emergency detection coverage** | 20+ critical keyword categories |
| **Equivalent commercial cost** | $800–$1,500+/month per provider |
| **API endpoints** | 8 RESTful endpoints with full OpenAPI documentation |
| **Frontend pages** | 8 pages with responsive, animated UI |

---

## Slide 19 — Learnings

**Title:** Key Learnings from This Internship

1. **RAG > Fine-tuning for medical AI** — Retrieval-Augmented Generation provides traceable, citable sources. Fine-tuning a medical LLM risks embedding outdated knowledge and is impossible to audit.

2. **Privacy is a feature, not a constraint** — Running Whisper locally isn't a limitation; it's a competitive advantage. Clinics won't adopt tools that send patient audio to the cloud.

3. **Zero-cost doesn't mean zero-quality** — By combining Groq's free LPU inference, local embeddings, and public APIs (OpenFDA, NICE), we achieved commercial-grade output at no cost.

4. **Safety guardrails are non-negotiable in healthcare AI** — Emergency detection, mandatory disclaimers, and a draft-approve workflow aren't optional features. They're the minimum bar for responsible AI.

5. **Full-stack thinking > isolated ML models** — The value isn't in the LLM call alone. It's in the pipeline: audio → transcription → entity extraction → RAG retrieval → structured generation → safety checks → physician review.

---

## Slide 20 — Thank You

**Title:** Thank You

**Project Links:**
- 🔗 GitHub: `github.com/Har-dik25/MediNote`
- 📹 Demo Video: [Loom link]
- 📝 Blog Post: [Blog link]

**Contact:**
- [Your Name]
- [Your Email]
- [LinkedIn Profile]

**Tagline:**
> *"Built with ❤️ to give doctors their time back."*

---

## Bonus: Sample Talking Points for Q&A

**Q: Why not use GPT-4 instead of Llama 3?**
> GPT-4 costs ~$30/1M tokens and sends patient data to OpenAI's servers. Groq's Llama 3.3 70B is free, 3x faster (800+ tok/sec vs ~50 tok/sec), and we can migrate to local Ollama deployment for complete data sovereignty.

**Q: How do you ensure the SOAP notes are accurate?**
> Three layers: (1) RAG grounds every note in authoritative NICE guidelines with explicit citations, (2) every note carries a mandatory AI disclaimer, and (3) the draft-approve workflow ensures a physician reviews before any note becomes official.

**Q: What if the knowledge base becomes outdated?**
> The data pipeline is modular. Running `setup_data.py` re-scrapes NICE, OpenFDA, and ICD-10 sources, rebuilds the vector index, and picks up any updates. This can be scheduled as a weekly cron job.

**Q: How does this compare to existing medical scribes?**
> Commercial AI scribes (Nuance DAX, Abridge) cost $300-$1,000/month per provider. MediMate delivers comparable core functionality — transcription, SOAP generation, coding assistance — at zero cost, with the added advantage of local transcription for privacy.

**Q: Can this handle multiple languages?**
> Whisper supports 99+ languages out of the box. The limitation is currently in the LLM prompt (English) and the knowledge base (English NICE guidelines). Multilingual support is on the roadmap.
