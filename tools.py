"""
MediMate Tools
==============
External tool functions for the MediMate copilot:
  - Drug interaction checking via OpenFDA
  - NICE guideline lookup via RAG
  - ICD-10 code suggestion via RAG
"""

import requests

# --- RAG-based tools ---
try:
    from rag_engine import search_guidelines, search_icd10, search_drugs
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


def check_drug_interaction(drug1: str, drug2: str) -> str:
    """
    Queries the public OpenFDA API to find any reported interactions between two drugs.
    Zero-cost implementation.
    """
    # OpenFDA uses generic names mostly, but we can do a broad search in the adverse events API
    # for reports containing both drugs.
    # A more robust clinical setup would use RxNorm interaction APIs, but OpenFDA is a great free demonstration.
    
    base_url = "https://api.fda.gov/drug/event.json"
    
    # We look for adverse events where BOTH drugs are listed in the patient's drug list.
    query = f'patient.drug.medicinalproduct:"{drug1}" AND patient.drug.medicinalproduct:"{drug2}"'
    
    url = f"{base_url}?search={query}&limit=1"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                # If we have results, it means there are reported adverse events with both drugs.
                # We fetch a sample of the reactions from the first result.
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
                            # Extract just the interaction section if present
                            text = info["text"]
                            if "Drug Interactions:" in text:
                                interaction_text = text.split("Drug Interactions:")[1].split("\n\n")[0]
                                msg += f"\n\n*{drug_name}:* {interaction_text[:300]}"

                return msg
            else:
                return ""
        elif response.status_code == 404:
            # FDA API returns 404 when no results are found.
            return ""
        else:
            return f"OpenFDA API returned status code {response.status_code}."
    except Exception as e:
        return f"Error connecting to OpenFDA: {str(e)}"


def lookup_nice_guideline(condition: str, top_k: int = 3) -> str:
    """
    Retrieves relevant NICE guideline recommendations for a clinical condition
    using the RAG vector store.
    
    Args:
        condition: Clinical condition or query (e.g., "asthma management")
        top_k: Number of guideline chunks to retrieve
        
    Returns:
        Formatted string with relevant guideline excerpts
    """
    if not RAG_AVAILABLE:
        return "⚠️ RAG engine not available. Run setup_data.py to build the vector store."

    results = search_guidelines(condition, top_k=top_k)
    
    if not results:
        return f"No NICE guideline information found for '{condition}'."
    
    output_parts = [f"**📋 NICE Guideline Recommendations for '{condition}':**\n"]
    
    for i, r in enumerate(results, 1):
        source = r["metadata"].get("guideline", "Unknown")
        relevance = round(1.0 - r.get("distance", 0.5), 2)
        
        output_parts.append(f"\n---\n**Source: NICE — {source}** (relevance: {relevance})")
        # Truncate long text for display
        text = r["text"][:500] + "..." if len(r["text"]) > 500 else r["text"]
        output_parts.append(text)
    
    output_parts.append(
        "\n\n*⚠️ Always consult the full NICE guideline and use clinical judgement. "
        "These are AI-retrieved excerpts.*"
    )
    
    return "\n".join(output_parts)


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

    results = search_drugs(drug_name, top_k=1)
    
    if not results:
        return f"No drug reference information found for '{drug_name}'."
    
    r = results[0]
    return f"**💊 Drug Reference: {r['metadata'].get('drug_name', drug_name)}**\n\n{r['text']}"
