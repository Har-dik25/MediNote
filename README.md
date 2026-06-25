# MediNote 🏥

> **From conversation to clinical note in seconds — so doctors can focus on patients, not paperwork.**
> 
> 🚧 **Status: In Progress** - Currently integrating real-time data APIs (OpenFDA, NIH Clinical Tables).

MediNotes is an AI-powered medical documentation copilot that transforms doctor-patient conversation summaries into structured SOAP notes with ICD-10 codes, diagnostic test suggestions, and drug interaction alerts.

## 🚀 Features

- **SOAP Note Generation** — Structured Subjective, Objective, Assessment, Plan notes
- **ICD-10 Coding** — Automated diagnosis code suggestions via tool-use
- **Drug Interaction Alerts** — Real-time checks via OpenFDA / local DB
- **Diagnostic Test Recommendations** — Evidence-based suggestions from clinical guidelines
- **RAG over Clinical Guidelines** — Hybrid BM25 + dense retrieval over NICE guidelines
- **Human-in-the-Loop** — Mandatory doctor review before note finalization
- **Evaluation Suite** — 50-case benchmark for SOAP completeness, ICD-10 accuracy, hallucination rate

## 📁 Project Structure

```
medinote/
├── data/                      # Raw data & stubs
│   ├── guidelines/            # Clinical guideline PDFs (NICE)
│   ├── icd10/                 # ICD-10 code database
│   ├── drug_interactions/     # Drug interaction stub data
│   └── samples/               # 50 sample conversation summaries
├── src/
│   ├── ingestion/             # PDF/text loading & chunking
│   ├── embeddings/            # Embedding generation & ChromaDB setup
│   ├── retrieval/             # Hybrid RAG retrieval (BM25 + dense)
│   ├── agents/                # LangGraph agent graph definition
│   ├── tools/                 # Tool implementations (ICD-10, drugs, tests)
│   ├── eval/                  # Evaluation harness
│   └── app/                   # Streamlit frontend
├── docs/                      # Design docs, ADRs, architecture
├── tests/                     # Unit & integration tests
├── .env.example               # API key template
├── requirements.txt           # Python dependencies
├── Makefile                   # Dev commands
├── Dockerfile                 # Container setup
├── docker-compose.yml         # Multi-service orchestration
└── pyproject.toml             # Project metadata & tool config
```

## ⚡ Quick Start

```bash
# 1. Clone
git clone https://github.com/<your-username>/medinote.git
cd medinote

# 2. Setup environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt

# 3. Configure API keys
cp .env.example .env
# Edit .env with your actual keys

# 4. Run the app
make run
```

## 🧪 Testing

```bash
make test       # Run all tests
make lint       # Run linter
```

## 🏗️ Tech Stack

| Component         | Choice                         |
| ----------------- | ------------------------------ |
| LLM               | OpenAI GPT-4o-mini             |
| Agent Framework   | LangGraph                      |
| Vector DB         | ChromaDB                       |
| Embeddings        | text-embedding-3-small         |
| RAG Strategy      | Hybrid (BM25 + Dense)          |
| Frontend          | Streamlit                      |
| Observability     | LangSmith                      |
| Eval              | Custom + RAGAS                 |

## 📄 License

MIT

## 👤 Author

Built as a B.Tech internship project (22 Jun – 26 Jul 2026).
