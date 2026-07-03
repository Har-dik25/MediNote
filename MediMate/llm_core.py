"""
LLM Core — RAG-Augmented SOAP Note Generator
=============================================
Generates structured SOAP notes from doctor-patient transcripts
using Llama-3 via Groq (Free Tier), augmented with evidence from
NICE clinical guidelines, ICD-10 codes, and drug reference data.
"""

import os
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

# We check for a Groq API Key. If not present, we use a fallback mock generator 
# so the app remains fully functional (zero cost) for demonstration without setup.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- RAG Integration ---
# Import the RAG engine; if it fails (e.g., chromadb not installed), we proceed without it.
try:
    from rag_engine import search_guidelines, search_icd10, search_drugs
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("⚠️  RAG engine not available. SOAP notes will be generated without guideline context.")


def _retrieve_context(transcript: str) -> str:
    """
    Query the RAG vector store for relevant clinical context.
    Returns a formatted string of relevant guidelines, ICD-10 codes, and drug info.
    """
    if not RAG_AVAILABLE:
        return ""

    context_parts = []

    # 1. Search for relevant NICE guidelines
    try:
        guideline_results = search_guidelines(transcript, top_k=3)
        if guideline_results:
            context_parts.append("=== RELEVANT NICE GUIDELINES ===")
            for r in guideline_results:
                source = r["metadata"].get("guideline", "Unknown")
                context_parts.append(f"\n[Source: NICE - {source}]\n{r['text'][:800]}")
    except Exception:
        pass

    # 2. Search for relevant ICD-10 codes
    try:
        icd10_results = search_icd10(transcript, top_k=5)
        if icd10_results:
            context_parts.append("\n\n=== SUGGESTED ICD-10 CODES ===")
            for r in icd10_results:
                context_parts.append(r["text"])
    except Exception:
        pass

    # 3. Search for relevant drug information
    try:
        drug_results = search_drugs(transcript, top_k=2)
        if drug_results:
            context_parts.append("\n\n=== RELEVANT DRUG INFORMATION ===")
            for r in drug_results:
                drug_name = r["metadata"].get("drug_name", "Unknown")
                context_parts.append(f"\n[Drug: {drug_name}]\n{r['text'][:600]}")
    except Exception:
        pass

    return "\n".join(context_parts) if context_parts else ""


# --- Prompt Templates ---

SOAP_PROMPT_WITH_RAG = """
You are a highly skilled medical AI copilot.
Convert the following doctor-patient conversation transcript into a structured SOAP note.

Use the clinical guidelines and reference data provided below to ensure evidence-based recommendations.
Cite specific guidelines when making recommendations (e.g., "per NICE NG136").

--- CLINICAL REFERENCE CONTEXT ---
{context}
--- END CONTEXT ---

Transcript:
{transcript}

Format your response strictly as:
**Subjective:** (Patient's symptoms, complaints, history as described)
**Objective:** (Vital signs, physical exam findings, lab results if mentioned)
**Assessment:** (Diagnosis or differential diagnosis, supported by evidence where available)
**Plan:** (Treatment plan, medications, tests — reference NICE guidelines where applicable)
**ICD-10 Suggestions:** (List 1-3 highly probable ICD-10 codes with descriptions, based on the assessment)
**Guidelines Referenced:** (List any NICE guidelines or clinical references used)

⚠️ IMPORTANT: This is AI-generated and requires physician approval. Do NOT finalize any diagnosis.
"""

SOAP_PROMPT_BASIC = """
You are a highly skilled medical AI copilot. 
Convert the following doctor-patient conversation transcript into a structured SOAP note.

Transcript:
{transcript}

Format your response strictly as:
**Subjective:** (Patient's symptoms, complaints)
**Objective:** (Vital signs, physical exam findings, if mentioned)
**Assessment:** (Diagnosis or differential diagnosis)
**Plan:** (Treatment, medications, tests)
**ICD-10 Suggestions:** (List 1-3 highly probable ICD-10 codes based on the assessment)

Remember to explicitly refuse to finalize any diagnosis and remind the user that this is AI-generated and requires physician approval.
"""


def generate_soap_note(transcript: str) -> dict:
    """
    Generates a structured SOAP note from a transcript using Llama-3 via Groq (Free Tier).
    Falls back to a mocked response if no API key is provided.
    
    Returns a dict with:
      - "soap_note": The generated SOAP note text
      - "context_used": The RAG context that was injected (for UI display)
      - "rag_enabled": Whether RAG was used
    """
    # Retrieve clinical context from vector store
    context = _retrieve_context(transcript)
    rag_enabled = bool(context)

    if not GROQ_API_KEY or GROQ_API_KEY.strip() == "":
        # Mock zero-cost fallback
        mock_note = """
**Subjective:** Patient complains of symptoms described in the transcript.
**Objective:** Pending clinical examination.
**Assessment:** AI Assessment pending physician review.
**Plan:** Recommend reviewing the patient history.
**ICD-10 Suggestions:** R50.9 (Fever, unspecified), R51.9 (Headache, unspecified)
**Guidelines Referenced:** None (mock mode)

*⚠️ Note: This is a mocked response because no GROQ_API_KEY was found in the environment. Get a free key at groq.com.*
        """
        return {
            "soap_note": mock_note.strip(),
            "context_used": context,
            "rag_enabled": rag_enabled,
        }

    try:
        # Use Llama 3 8b as it is extremely fast and free on Groq
        llm = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model_name="llama3-8b-8192")

        if context:
            prompt = PromptTemplate(
                template=SOAP_PROMPT_WITH_RAG,
                input_variables=["transcript", "context"],
            )
            chain = prompt | llm
            response = chain.invoke({"transcript": transcript, "context": context})
        else:
            prompt = PromptTemplate(
                template=SOAP_PROMPT_BASIC,
                input_variables=["transcript"],
            )
            chain = prompt | llm
            response = chain.invoke({"transcript": transcript})

        return {
            "soap_note": response.content,
            "context_used": context,
            "rag_enabled": rag_enabled,
        }
    except Exception as e:
        return {
            "soap_note": f"Error generating SOAP note: {str(e)}",
            "context_used": context,
            "rag_enabled": rag_enabled,
        }


def suggest_icd10_codes(assessment: str) -> list:
    """
    Suggest ICD-10 codes based on a clinical assessment using RAG.
    
    Args:
        assessment: The assessment/diagnosis text
        
    Returns:
        List of dicts with 'code', 'description', 'category', and 'relevance_score'
    """
    if not RAG_AVAILABLE:
        return []

    try:
        results = search_icd10(assessment, top_k=5)
        suggestions = []
        for r in results:
            suggestions.append({
                "code": r["metadata"].get("code", "?"),
                "description": r["text"].split("\n")[1].replace("Description: ", "") if "\n" in r["text"] else r["text"],
                "category": r["metadata"].get("category", "Unknown"),
                "relevance_score": round(1.0 - r.get("distance", 0.5), 3),
            })
        return suggestions
    except Exception:
        return []
