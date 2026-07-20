"""
MediMate Tools
==============
External tool functions for the MediMate copilot:
  - Drug interaction checking via OpenFDA
  - Clinical guideline lookup via RAG (NICE, WHO, CDC, EMA — region-filtered)
  - ICD-10 code suggestion via RAG
  - Drug information lookup via RAG
  - Diagnostic test suggestion via RAG
"""

import requests
from logger import setup_logger, log_request, log_response
import time

logger = setup_logger(__name__)

# --- RAG-based tools ---
try:
    from rag_engine import search_guidelines, search_icd10, search_drugs
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logger.warning("RAG engine not available. Tool functions will return empty results.")


def check_drug_interaction(drug1: str, drug2: str) -> str:
    """
    Queries the public OpenFDA API to find any reported interactions between two drugs.
    Zero-cost implementation.
    """
    start_time = time.time()
    log_request(logger, "check_drug_interaction", f"{drug1}+{drug2}")
    
    base_url = "https://api.fda.gov/drug/event.json"
    query = f'patient.drug.medicinalproduct:"{drug1}" AND patient.drug.medicinalproduct:"{drug2}"'
    url = f"{base_url}?search={query}&limit=1"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                reactions = data["results"][0].get("patient", {}).get("reaction", [])
                reaction_list = [r.get("reactionmeddrapt", "") for r in reactions]
                
                msg = f"Found {data['meta']['results']['total']} adverse event reports involving both '{drug1}' and '{drug2}'.\n\n"
                if reaction_list:
                    msg += f"**Sample Co-reported Reactions:** {', '.join(reaction_list[:5])}"
                
                # Also check our local drug reference for additional context
                if RAG_AVAILABLE:
                    drug1_info = search_drugs(f"{drug1} interactions", top_k=1)
                    drug2_info = search_drugs(f"{drug2} interactions", top_k=1)
                    if drug1_info or drug2_info:
                        msg += "\n\n**📋 Additional Drug Reference Info:**"
                        for info in drug1_info + drug2_info:
                            drug_name = info["metadata"].get("drug_name", "Unknown")
                            text = info["text"]
                            if "Drug Interactions:" in text:
                                interaction_text = text.split("Drug Interactions:")[1].split("\n\n")[0]
                                msg += f"\n\n*{drug_name}:* {interaction_text[:300]}"

                elapsed = (time.time() - start_time) * 1000
                log_response(logger, "check_drug_interaction", elapsed, success=True, found=True)
                return msg
            else:
                elapsed = (time.time() - start_time) * 1000
                log_response(logger, "check_drug_interaction", elapsed, success=True, found=False)
                return ""
        elif response.status_code == 404:
            elapsed = (time.time() - start_time) * 1000
            log_response(logger, "check_drug_interaction", elapsed, success=True, found=False)
            return ""
        else:
            elapsed = (time.time() - start_time) * 1000
            log_response(logger, "check_drug_interaction", elapsed, success=False, status=response.status_code)
            return f"OpenFDA API returned status code {response.status_code}."
    except requests.exceptions.Timeout:
        elapsed = (time.time() - start_time) * 1000
        log_response(logger, "check_drug_interaction", elapsed, success=False, error="timeout")
        logger.error("OpenFDA API request timed out")
        return "Error: OpenFDA API request timed out. Please try again."
    except requests.exceptions.ConnectionError as e:
        elapsed = (time.time() - start_time) * 1000
        log_response(logger, "check_drug_interaction", elapsed, success=False, error="connection_error")
        logger.error(f"OpenFDA connection error: {e}")
        return f"Error connecting to OpenFDA: {str(e)}"
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        log_response(logger, "check_drug_interaction", elapsed, success=False, error=str(e))
        logger.error(f"Unexpected error in drug interaction check: {e}", exc_info=True)
        return f"Error checking drug interaction: {str(e)}"


def lookup_guideline(condition: str, top_k: int = 3, region: str = None) -> str:
    """
    Retrieves relevant clinical guideline recommendations for a condition
    using the RAG vector store, filtered by the user's selected region.

    Args:
        condition: Clinical condition or query (e.g., "asthma management")
        top_k: Number of guideline chunks to retrieve
        region: Region filter — e.g. 'UK', 'Europe', 'North America', 'Global'.
                If None, searches all regions.

    Returns:
        Formatted string with relevant guideline excerpts
    """
    if not RAG_AVAILABLE:
        return "⚠️ RAG engine not available. Run setup_data.py to build the vector store."

    log_request(logger, "lookup_guideline", condition)
    results = search_guidelines(condition, top_k=top_k, region=region)

    if not results:
        region_label = f" ({region})" if region else ""
        return f"No guideline information found for '{condition}'{region_label}."

    # Determine the header label from the first result's source
    output_parts = [f"**📋 Clinical Guideline Recommendations for '{condition}':**\n"]

    for i, r in enumerate(results, 1):
        source = r["metadata"].get("source", "Unknown")
        guideline_name = r["metadata"].get("guideline", "Unknown")
        result_region = r["metadata"].get("region", "?")
        relevance = round(1.0 - r.get("distance", 0.5), 2)

        output_parts.append(f"\n---\n**Source: {source} — {guideline_name}** (region: {result_region}, relevance: {relevance})")
        # Truncate long text for display
        text = r["text"][:500] + "..." if len(r["text"]) > 500 else r["text"]
        output_parts.append(text)

    output_parts.append(
        "\n\n*⚠️ Always consult the full guideline and use clinical judgement. "
        "These are AI-retrieved excerpts.*"
    )

    return "\n".join(output_parts)


# Backward-compatible alias
def lookup_nice_guideline(condition: str, top_k: int = 3) -> str:
    """Legacy wrapper — searches UK (NICE) guidelines only."""
    return lookup_guideline(condition, top_k=top_k, region="UK")


def suggest_icd10(description: str, top_k: int = 5) -> list:
    """
    Suggests ICD-10 codes matching a clinical description using the RAG vector store.
    
    Args:
        description: Clinical condition, symptom, or diagnosis description
        top_k: Number of code suggestions to return
        
    Returns:
        List of dicts with 'code', 'description', 'category', 'relevance_score'
    """
    if not RAG_AVAILABLE:
        return []
    
    log_request(logger, "suggest_icd10", description)
    results = search_icd10(description, top_k=top_k)
    
    suggestions = []
    for r in results:
        code = r["metadata"].get("code", "?")
        # Parse description from the text
        text_lines = r["text"].split("\n")
        desc = ""
        category = r["metadata"].get("category", "Unknown")
        for line in text_lines:
            if line.startswith("Description:"):
                desc = line.replace("Description: ", "")
                break
        
        suggestions.append({
            "code": code,
            "description": desc or r["text"][:100],
            "category": category,
            "relevance_score": round(1.0 - r.get("distance", 0.5), 3),
        })
    
    return suggestions


def suggest_tests(transcript: str, top_k: int = 5, region: str = None) -> list:
    """
    Suggests diagnostic tests based on the clinical transcript using RAG.
    
    Searches the clinical guidelines for recommended investigations and tests
    relevant to the symptoms and conditions described in the transcript.
    
    Args:
        transcript: The doctor-patient conversation transcript
        top_k: Number of guideline results to search
        region: Optional region filter for guidelines
        
    Returns:
        List of dicts with 'test', 'rationale', 'source', 'relevance_score'
    """
    if not RAG_AVAILABLE:
        return []
    
    log_request(logger, "suggest_tests", transcript)
    
    # Search guidelines specifically for test/investigation recommendations
    test_query = f"recommended investigations tests diagnostics for: {transcript[:200]}"
    results = search_guidelines(test_query, top_k=top_k, region=region)
    
    if not results:
        return []
    
    # Common diagnostic test keywords to extract from guideline text
    TEST_KEYWORDS = [
        "blood test", "blood count", "full blood count", "FBC",
        "chest x-ray", "chest X-ray", "CXR", "X-ray",
        "ECG", "electrocardiogram", "echocardiogram",
        "CT scan", "MRI", "ultrasound", "imaging",
        "spirometry", "peak flow", "lung function",
        "urinalysis", "urine test", "urine culture",
        "blood glucose", "HbA1c", "glucose tolerance",
        "lipid profile", "cholesterol",
        "liver function", "LFT", "renal function", "eGFR", "creatinine",
        "thyroid function", "TSH",
        "blood pressure", "ambulatory BP",
        "biopsy", "endoscopy", "colonoscopy",
        "sputum culture", "culture and sensitivity",
        "PSA", "mammogram", "cervical screening",
        "bone density", "DEXA",
        "allergy testing", "skin prick test",
        "mental health assessment", "PHQ-9", "GAD-7",
    ]
    
    suggestions = []
    seen_tests = set()
    
    for r in results:
        text = r["text"]
        source = r["metadata"].get("guideline", "Unknown")
        relevance = round(1.0 - r.get("distance", 0.5), 3)
        
        # Extract test mentions from the guideline text
        for test in TEST_KEYWORDS:
            if test.lower() in text.lower() and test.lower() not in seen_tests:
                seen_tests.add(test.lower())
                # Extract a short rationale (the sentence containing the test)
                sentences = text.replace("\n", " ").split(".")
                rationale = ""
                for sentence in sentences:
                    if test.lower() in sentence.lower():
                        rationale = sentence.strip() + "."
                        break
                
                suggestions.append({
                    "test": test,
                    "rationale": rationale[:200] if rationale else f"Recommended per {source}",
                    "source": source,
                    "relevance_score": relevance,
                })
    
    # Sort by relevance and limit
    suggestions.sort(key=lambda x: x["relevance_score"], reverse=True)
    return suggestions[:8]


def lookup_drug_info(drug_name: str) -> str:
    """
    Looks up drug information from the local RAG vector store.
    
    Args:
        drug_name: Name of the drug to look up
        
    Returns:
        Formatted string with drug information
    """
    if not RAG_AVAILABLE:
        return "⚠️ RAG engine not available. Run setup_data.py to build the vector store."

    log_request(logger, "lookup_drug", drug_name)
    results = search_drugs(drug_name, top_k=1)
    
    if not results:
        return f"No drug reference information found for '{drug_name}'."
    
    r = results[0]
    return f"**💊 Drug Reference: {r['metadata'].get('drug_name', drug_name)}**\n\n{r['text']}"

