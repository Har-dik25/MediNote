# Test Report — MediMate Medical Copilot

**Date:** July 2026
**Test Framework:** pytest
**Test Command:** `python -m pytest tests/ -v`

---

## Test Summary

| Test File | Tests | Description |
|-----------|-------|-------------|
| `tests/test_tools.py` | 9 | Drug interaction check, ICD-10 suggestion, test suggestion, guideline lookup, drug info |
| `tests/test_llm_core.py` | 11 | Safety flagging, SOAP generation (mock mode), ICD-10 code suggestion |
| `tests/test_rag_engine.py` | 8 | Vector store search functions, collection stats |
| `tests/test_integration.py` | 3 | End-to-end pipeline: transcript → SOAP → ICD-10 → safety |
| **Total** | **31** | |

---

## What Was Tested

### Unit Tests
1. **Drug Interaction Check (`test_tools.py`)**
   - Interaction found via OpenFDA API (mocked)
   - No interaction found (mocked)
   - FDA 404 response handling
   - Network connection error handling

2. **ICD-10 Suggestion (`test_tools.py`)**
   - Returns a list with correct structure
   - Each suggestion has: code, description, category, relevance_score

3. **Diagnostic Test Suggestion (`test_tools.py`)**
   - Returns a list with correct structure
   - Each suggestion has: test, rationale, source, relevance_score
   - Respects max result limit (≤8)

4. **Safety Flagging (`test_llm_core.py`)**
   - Normal transcript → no flags
   - Suicidal ideation → flagged
   - Chest pain radiating → flagged
   - Anaphylaxis → flagged
   - Multiple keywords → all captured
   - Case insensitive matching

5. **SOAP Note Generation (`test_llm_core.py`)**
   - Mock mode returns correct dict structure
   - AI disclaimer always included
   - SOAP sections present (Subjective, Objective, Assessment, Plan)
   - Safety flags passed through in result

6. **RAG Engine (`test_rag_engine.py`)**
   - Search functions return lists with correct structure
   - `top_k` parameter respected
   - Collection stats return non-negative integers
   - `search_all()` returns dict with three collection keys

### Integration Tests
7. **Full Pipeline (`test_integration.py`)**
   - Normal case: transcript → SOAP note + ICD-10 + tests (no safety flag)
   - Emergency case: transcript → SOAP note + safety flag triggered
   - Disclaimer always present in every output

---

## What's NOT Tested (Known Gaps)
- **Live LLM calls:** Tests run in mock mode (no GROQ_API_KEY). Real LLM output quality is not automatically tested.
- **Audio transcription:** Whisper model download is slow; audio tests are excluded from automated CI.
- **OpenFDA live API:** Drug interaction tests use mocked HTTP responses to avoid network dependency.
- **UI (Streamlit):** No automated UI tests. Verified manually.

---

## How to Run

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1   # Windows
source venv/bin/activate       # macOS/Linux

# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_llm_core.py -v

# Run with coverage (if pytest-cov installed)
python -m pytest tests/ -v --cov=. --cov-report=term-missing
```
