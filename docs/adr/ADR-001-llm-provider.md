# ADR-001: LLM Provider — Groq (Llama 3) over OpenAI / Anthropic

## Context
MediMate needs a large language model to convert doctor-patient conversation transcripts into structured SOAP notes. The LLM must produce accurate, well-formatted medical documentation and incorporate clinical guidelines from the RAG context. We needed to choose between commercial API providers (OpenAI GPT-4, Anthropic Claude) and open-model providers (Groq, Together, Ollama).

## Decision
We chose **Groq** running **Llama 3 8B (llama3-8b-8192)** as the inference provider.

## Consequences

### Positive
- **Zero cost:** Groq's free tier provides generous rate limits (30 req/min, 14,400 req/day) — more than enough for a medical copilot prototype.
- **Blazing fast:** Groq's LPU hardware delivers ~500 tokens/second, making the SOAP note generation feel near-instant. This is critical for physician UX — doctors will not wait 15 seconds for a note.
- **Open model:** Llama 3 is open-weight, meaning we are not vendor-locked. We can switch to self-hosted inference (vLLM, Ollama) in production without changing the prompt or output format.
- **Privacy-friendly:** For a production deployment in healthcare (HIPAA/GDPR), open models can be self-hosted behind a firewall. Starting with Llama 3 makes this migration path clean.

### Negative
- **Smaller model:** Llama 3 8B is less capable than GPT-4o or Claude 3.5 on complex medical reasoning. For edge cases (rare diseases, ambiguous presentations), it may produce less nuanced assessments.
- **No function calling (native):** Unlike OpenAI, Groq's Llama 3 endpoint doesn't natively support function calling. We use LangChain's prompt-based approach instead, which is slightly less structured.
- **Rate limits on free tier:** 30 requests/minute is fine for a single-doctor prototype but would need upgrading for multi-tenant production use.

## Alternatives Considered

| Provider | Why rejected |
|----------|-------------|
| **OpenAI GPT-4o** | Costs $0.005-0.015/1K tokens. For a zero-cost internship project, this adds up. Also, PHI (Protected Health Information) concerns with sending patient data to OpenAI's servers. |
| **Anthropic Claude** | Similar cost and privacy concerns as OpenAI. Claude is excellent at medical reasoning, but the free tier is too restrictive for iterative development. |
| **Ollama (local)** | Truly zero-cost and private, but requires a GPU for reasonable speed. Most developer laptops would see 10-30 second generation times, which ruins the demo experience. |
| **Together AI** | Competitive free tier, but Groq's inference speed is 5-10x faster on benchmarks. Speed matters for UX. |
