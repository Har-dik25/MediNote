<div align="center">
  <img src="https://img.icons8.com/color/96/000000/medical-doctor.png" alt="MediMate Logo">
  <h1>MediMate: Your AI Medical Copilot</h1>
  <p>
    <strong>A zero-cost, real-time clinical assistant that transforms doctor-patient conversations into evidence-based SOAP notes using RAG and local vector search.</strong>
  </p>
  
  <p>
    <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white" alt="Python"></a>
    <a href="https://streamlit.io"><img src="https://img.shields.io/badge/Streamlit-FF4B4B.svg?logo=streamlit&logoColor=white" alt="Streamlit"></a>
    <a href="https://groq.com"><img src="https://img.shields.io/badge/Groq-Llama_3-f5533d.svg?logo=meta&logoColor=white" alt="Groq"></a>
    <a href="https://huggingface.co"><img src="https://img.shields.io/badge/HuggingFace-Whisper-yellow.svg?logo=huggingface&logoColor=black" alt="Whisper"></a>
    <a href="https://www.trychroma.com/"><img src="https://img.shields.io/badge/Vector_DB-Chroma-4479A1.svg?logo=chroma&logoColor=white" alt="ChromaDB"></a>
  </p>
</div>

---

## 📖 Overview

Medical professionals spend over 2 hours a day on documentation, leading to burnout and reduced patient face-time. **MediMate** is an open-source, zero-cost AI copilot designed to eliminate this administrative burden. It listens to doctor-patient interactions and automatically synthesizes structured **SOAP notes**, suggests appropriate **ICD-10 codes**, recommends diagnostic tests, and flags potential drug interactions. 

### 🛑 Problem Statement
Doctors are overwhelmed by the administrative burden of clinical documentation. The average physician spends nearly 2 hours on Electronic Health Records (EHR) and desk work for every 1 hour of direct patient care. This leads to severe burnout, truncated patient consultations, and degraded quality of care. Existing AI scribing solutions are often prohibitively expensive or lock clinics into proprietary ecosystems, making them inaccessible to smaller practices or resource-constrained healthcare systems.

Crucially, MediMate relies on **Retrieval-Augmented Generation (RAG)** referencing authoritative NICE clinical guidelines, ensuring all outputs are evidence-based. It runs entirely on local infrastructure or free-tier APIs, making it a zero-cost solution for practitioners.

## ✨ Features

- 🎙️ **Real-time Transcription:** Powered by local HuggingFace Whisper models for privacy-preserving, accurate medical transcription.
- 📝 **Automated SOAP Notes:** Generates structured Subjective, Objective, Assessment, and Plan notes instantly using Llama 3.
- 📚 **Evidence-Based RAG:** Grounds recommendations using 792 chunks of NICE Guidelines and OpenFDA drug data.
- ⚠️ **Safety & Interaction Checks:** Automatically cross-references prescribed medications against known OpenFDA drug interactions.
- 💻 **Zero-Cost & Local-First:** Designed to run on standard hardware without expensive API subscriptions or GPU requirements.

---

## 🏗️ Architecture

### C4 Level 2 (Container) Diagram

```mermaid
C4Context
title System Context & Container Diagram for MediMate

Person(doctor, "Medical Professional", "Doctor using the system to transcribe patient interactions.")

System_Boundary(medimate, "MediMate Copilot") {
    Container(streamlit, "Streamlit UI", "Python", "Provides the user interface for audio recording, text input, and viewing SOAP notes.")
    Container(whisper, "Whisper Engine", "Transformers / PyTorch", "Locally processes audio chunks and translates them to text.")
    Container(rag_engine, "RAG Orchestrator", "LangChain", "Chains the retrieved context with the LLM prompt.")
    ContainerDb(chroma, "ChromaDB", "Vector Database", "Stores embedded NICE guidelines, ICD-10 codes, and OpenFDA data locally.")
}

System_Ext(groq, "Groq API (Llama 3)", "Cloud LLM Provider", "Executes lightning-fast inference for SOAP note generation.")
System_Ext(nice, "NICE API / Scraper", "External Data", "Source of clinical guidelines.")
System_Ext(openfda, "OpenFDA API", "External Data", "Source of drug interactions and safety info.")

Rel(doctor, streamlit, "Speaks into / Reviews notes via", "HTTPS")
Rel(streamlit, whisper, "Sends raw audio bytes to", "In-memory")
Rel(whisper, rag_engine, "Passes transcribed text to", "In-memory")
Rel(rag_engine, chroma, "Queries vector similarities", "Local File I/O")
Rel(rag_engine, groq, "Sends context + prompt", "REST/HTTPS")
Rel(chroma, nice, "Initially populated from", "Scraping")
Rel(chroma, openfda, "Initially populated from", "REST API")
```

### Architecture Narrative

MediMate is designed to prioritize **data privacy, minimal latency, and zero infrastructure costs**. The architecture centers around a "local-first" hybrid approach where the most sensitive operation—audio transcription—happens entirely on the host machine, while the cognitively heavy operation—synthesizing the note—is outsourced to an ultra-fast, free-tier cloud provider.

#### The Containers
1. **Streamlit UI**: We chose Streamlit because clinical prototypes require rapid iteration on the frontend while deeply integrating with Python backend libraries like `sounddevice` or `pyaudio`. It handles the real-time audio capture and presents the final SOAP note layout.
2. **Whisper Engine**: Transcribing patient audio in the cloud poses HIPAA/GDPR risks. By running HuggingFace's Whisper model locally (via CPU), we guarantee that raw audio never leaves the clinic's network.
3. **RAG Orchestrator (LangChain)**: The "brain" of the application. It receives the raw transcript, extracts keywords, and queries the local vector database. LangChain then formats a strict system prompt combining the transcript and the retrieved medical context.
4. **ChromaDB**: A local-only vector store. Using SQLite under the hood, it persists our embedded clinical guidelines without needing a dedicated server (like Pinecone or Qdrant), keeping the deployment completely stateless and portable.

#### External Interactions
- **Groq API**: To generate a high-quality SOAP note, we need a large model (Llama 3 8B). Running this locally requires a heavy GPU, which most doctors don't have. Groq provides LPU-accelerated inference at over 800 tokens/second, making the note generation feel instantaneous and free of charge.
- **Data Scrapers**: Run offline during setup, these modules reach out to NICE and OpenFDA to download authoritative medical facts, ensuring the LLM is grounded in real clinical truth rather than hallucinated internet data.

## 🛠️ Technology Stack

| Component | Choice | Why |
| :--- | :--- | :--- |
| **Frontend Interface** | [Streamlit](https://streamlit.io/) | Rapid prototyping of Python data apps, easy audio integration |
| **Audio Processing** | [Whisper](https://huggingface.co/) (Local) | Privacy-preserving, accurate, runs without GPU |
| **Large Language Model** | Llama 3 8B via [Groq](https://groq.com/) | Lightning-fast inference (800+ tokens/sec), cost-effective |
| **Orchestration** | [LangChain](https://www.langchain.com/) | Standardized interfaces for chaining LLM calls and retrievers |
| **Vector Database** | [ChromaDB](https://www.trychroma.com/) | Persistent local storage, no external dependency required |
| **Embeddings** | `all-MiniLM-L6-v2` | Fast, lightweight dense embedding model running locally |

---

## 🚀 Quickstart Guide

### Prerequisites
- Python 3.10 or higher
- At least 2GB of free disk space
- A free API key from [Groq](https://console.groq.com)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Har-dik25/MediNote.git
   cd MediNote
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   
   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration:**
   Create a `.env` file in the root directory and add your Groq API key:
   ```ini
   GROQ_API_KEY=your_groq_api_key_here
   ```

### Running the Application

1. **Initialize the Knowledge Base (One-time setup, ~8 mins):**
   ```bash
   python setup_data.py
   ```
   *This script fetches NICE guidelines, OpenFDA data, and builds the local ChromaDB vector index.*

2. **Launch the Copilot:**
   ```bash
   python -m streamlit run app.py
   ```
   *Navigate to `http://localhost:8501` in your web browser.*

### Running Tests
Ensure system stability by running the test suite:
```bash
python -m pytest tests/ -v
```

---

## 📂 Project Structure

```
MediMate/
├── app.py                  # Main Streamlit application
├── backend/                # Core logic, LLM integrations, RAG engines
├── docs/                   # Architectural decisions and data docs
├── data/                   # Downloaded guidelines and vector db (generated)
├── tests/                  # Automated pytest suite
├── setup_data.py           # Knowledge base initialization script
└── requirements.txt        # Dependency management
```

## 🗺️ Roadmap (Next 2 Weeks)

If given an additional two weeks, the following features would be prioritized:
1. **FHIR / HL7 Integration:** Exporting generated SOAP notes directly into standard EHR systems (Epic, Cerner).
2. **Local LLM Execution (Ollama):** Removing the Groq API dependency entirely by running a 4-bit quantized Llama 3 model directly on-device using Ollama.
3. **Multi-Speaker Diarization:** Accurately attributing transcribed text to "Doctor" or "Patient".
4. **Expanded Knowledge Base:** Integrating CDC and WHO guidelines in addition to NICE.

---

## ⚠️ Important Disclaimers

- **Not for Clinical Use:** MediMate is a prototype and proof-of-concept. All AI-generated outputs MUST be reviewed by a qualified healthcare professional.
- **Regional Guidelines:** The current vector database uses UK-centric NICE guidelines.
- **General Embeddings:** The embedding model (`all-MiniLM-L6-v2`) is a general-purpose model, not specifically trained on clinical corpora.

## 🤝 Contributing

Contributions are welcome! If you'd like to improve MediMate, please fork the repository, make your changes, and submit a Pull Request. For major changes, please open an issue first to discuss your proposed updates.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---
<div align="center">
  <i>Built with ❤️ to give doctors their time back.</i>
</div>
