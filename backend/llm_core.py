"""
LLM Core — RAG-Augmented SOAP Note Generator
=============================================
Generates structured SOAP notes from doctor-patient transcripts
using Llama-3 via Groq (Free Tier), augmented with evidence from
NICE clinical guidelines, ICD-10 codes, and drug reference data.

Includes safety features:
  - Explicit refusal on diagnosis statements
  - Out-of-scope/emergency flagging
  - Suggested diagnostic tests
"""

import os
import re
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv, find_dotenv
import time
from logger import setup_logger, log_request, log_response

load_dotenv(find_dotenv(usecwd=True))

logger = setup_logger(__name__)

# We check for a Groq API Key. If not present, we use a fallback mock generator 
# so the app remains fully functional (zero cost) for demonstration without setup.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- Safety: Emergency / Out-of-Scope Detection ---
# Keywords that indicate the case may require immediate emergency attention
# or is outside the scope of an AI copilot.
EMERGENCY_KEYWORDS = [
    "suicidal", "suicide", "self-harm", "overdose",
    "chest pain radiating", "crushing chest pain", "cardiac arrest",
    "stroke symptoms", "sudden weakness", "facial droop",
    "anaphylaxis", "anaphylactic", "severe allergic reaction",
    "seizure", "status epilepticus", "unresponsive",
    "severe bleeding", "hemorrhage", "massive haemorrhage",
    "breathing stopped", "not breathing", "choking",
]

SAFETY_DISCLAIMER = (
    "\n\n---\n"
    "⚠️ **AI-GENERATED — NOT A MEDICAL DIAGNOSIS**\n\n"
    "This SOAP note is produced by an AI copilot and is intended as a **draft** "
    "for physician review only. It does **not** constitute a medical diagnosis, "
    "treatment recommendation, or clinical decision. The attending physician must "
    "review, edit, and approve this note before it becomes part of the patient record.\n\n"
    "*MediMate v1.0 — Evidence-based, physician-approved.*"
)


def flag_out_of_scope(transcript: str) -> dict:
    """
    Checks the transcript for emergency/out-of-scope indicators.
    
    Returns:
        dict with:
          - "is_emergency": bool
          - "flags": list of matched keywords
          - "warning": formatted warning string (empty if no flags)
    """
    transcript_lower = transcript.lower()
    matched = [kw for kw in EMERGENCY_KEYWORDS if kw in transcript_lower]
    
    if matched:
        warning = (
            "🚨 **EMERGENCY / OUT-OF-SCOPE ALERT**\n\n"
            "The following indicators were detected in this transcript:\n"
            + "\n".join(f"- ⚠️ `{flag}`" for flag in matched)
            + "\n\n**This case may require immediate clinical attention. "
            "AI-generated notes should NOT be relied upon for emergency triage. "
            "Please escalate to an attending physician immediately.**"
        )
        logger.warning(f"SAFETY_FLAG | flags={matched}")
        return {"is_emergency": True, "flags": matched, "warning": warning}
    
    return {"is_emergency": False, "flags": [], "warning": ""}

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

def extract_clinical_entities(transcript: str) -> dict:
    """
    Extracts drugs and conditions from the transcript using a fast JSON-mode LLM call.
    This powers the automatic execution of the Clinical Tools in the sidebar.
    
    Returns a dict with:
      - "drugs": list of up to 2 drugs
      - "condition": primary condition or diagnosis (string)
    """
    if not GROQ_API_KEY or GROQ_API_KEY.strip() == "" or GROQ_API_KEY == "your_groq_api_key_here":
        # Mock zero-cost fallback
        return {
            "drugs": ["Lisinopril", "Metformin"],
            "condition": "Type 2 diabetes"
        }
    
    try:
        start_time = time.time()
        log_request(logger, "extract_clinical_entities", transcript[:100] + "...")
        
        # Use a highly capable free model
        llm = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile")
        
        prompt_template = """
        Extract the drugs and medical conditions mentioned in the following clinical text (transcript and SOAP note).
        Return the result strictly as a valid JSON object with the following schema:
        {
            "drugs": ["drug1", "drug2"], // list of up to 2 medications mentioned. Empty list if none.
            "condition": "primary condition" // a single primary medical condition mentioned, or empty string if none.
        }
        
        Clinical Text:
        {transcript}
        """
        prompt = PromptTemplate(template=prompt_template, input_variables=["transcript"])
        
        # Llama 3 via Groq supports JSON mode if the prompt asks for it and we bind response_format
        chain = prompt | llm.bind(response_format={"type": "json_object"})
        
        response = chain.invoke({"transcript": transcript})
        result_json = json.loads(response.content)
        
        # Validate output schema safely
        drugs = result_json.get("drugs", [])
        if not isinstance(drugs, list):
            drugs = []
        condition = result_json.get("condition", "")
        if not isinstance(condition, str):
            condition = str(condition)
            
        elapsed = (time.time() - start_time) * 1000
        log_response(logger, "extract_clinical_entities", elapsed, success=True)
        
        return {
            "drugs": drugs[:2],  # Limit to 2 for the interaction checker
            "condition": condition
        }
    except Exception as e:
        logger.error(f"Failed to extract clinical entities: {e}", exc_info=True)
        return {"drugs": [], "condition": ""}


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
    
    Includes:
      - Safety flagging for emergency/out-of-scope cases
      - RAG-augmented evidence from NICE guidelines
      - Mandatory AI disclaimer
    
    Returns a dict with:
      - "soap_note": The generated SOAP note text
      - "context_used": The RAG context that was injected (for UI display)
      - "rag_enabled": Whether RAG was used
      - "safety": Safety flag dict (is_emergency, flags, warning)
    """
    start_time = time.time()
    log_request(logger, "generate_soap", transcript)
    
    # 1. Run safety check
    safety = flag_out_of_scope(transcript)
    
    # 2. Retrieve clinical context from vector store
    context = _retrieve_context(transcript)
    rag_enabled = bool(context)

    if not GROQ_API_KEY or GROQ_API_KEY.strip() == "" or GROQ_API_KEY == "your_groq_api_key_here":
        # Mock zero-cost fallback
        logger.info("Using mock mode — no GROQ_API_KEY found")
        mock_note = """
**Subjective:** Patient complains of symptoms described in the transcript.
**Objective:** Pending clinical examination.
**Assessment:** AI Assessment pending physician review.
**Plan:** Recommend reviewing the patient history.
**ICD-10 Suggestions:** R50.9 (Fever, unspecified), R51.9 (Headache, unspecified)
**Guidelines Referenced:** None (mock mode)

*⚠️ Note: This is a mocked response because no GROQ_API_KEY was found in the environment. Get a free key at [console.groq.com](https://console.groq.com).*
        """
        elapsed = (time.time() - start_time) * 1000
        log_response(logger, "generate_soap", elapsed, success=True, mode="mock")
        return {
            "soap_note": mock_note.strip() + SAFETY_DISCLAIMER,
            "context_used": context,
            "rag_enabled": rag_enabled,
            "safety": safety,
        }

    try:
        # Use Llama 3 70b as it is highly capable and free on Groq
        llm = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile")

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

        elapsed = (time.time() - start_time) * 1000
        log_response(logger, "generate_soap", elapsed, success=True, mode="llm", rag=rag_enabled)
        return {
            "soap_note": response.content + SAFETY_DISCLAIMER,
            "context_used": context,
            "rag_enabled": rag_enabled,
            "safety": safety,
        }
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        log_response(logger, "generate_soap", elapsed, success=False, error=str(e))
        logger.error(f"SOAP generation failed: {e}", exc_info=True)
        return {
            "soap_note": f"Error generating SOAP note: {str(e)}",
            "context_used": context,
            "rag_enabled": rag_enabled,
            "safety": safety,
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
