# ADR-003: Choosing Groq LPU (Llama 3) over Local LLMs

## Context
After transcribing audio and retrieving guidelines via RAG, the system must synthesize a structured SOAP note. Medical synthesis requires a highly capable reasoning model (70B+ parameters). Running a 70B model locally requires multiple high-end GPUs, which contradicts the goal of making this accessible to standard clinics.

## Decision
We chose to use **Llama 3.3 70B hosted on Groq's API** (Free Tier).

## Consequences
**Positive:**
- **Incredible Speed:** Groq's LPU architecture delivers over 800 tokens per second. The entire SOAP note generates almost instantly (< 2 seconds), minimizing physician wait time.
- **High Reasoning Capability:** Llama 3 70B is capable of complex medical reasoning, entity extraction, and formatting JSON structures reliably.
- **Zero Cost:** The free tier easily supports a single physician's daily documentation load.

**Negative:**
- **Cloud Dependency:** Unlike the Whisper transcription, the transcript text *is* sent to a cloud provider. While faster, this requires a stable internet connection and implies trust in Groq's data retention policies.
- **Rate Limits:** Free tier APIs are subject to rate limiting during high traffic.

## Alternatives considered
- **Local Ollama (Llama 3 8B):** Rejected for the primary pipeline because 8B models struggle with complex multi-step JSON extraction and RAG synthesis compared to 70B models. However, this is retained on the roadmap as a fallback.
- **OpenAI GPT-4o API:** Rejected due to cost. While highly capable, relying on GPT-4 breaks the zero-cost requirement and introduces recurring API expenses for the clinic.
