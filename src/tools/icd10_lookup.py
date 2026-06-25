"""
ICD-10 Code Lookup Tool.

Provides ICD-10-CM diagnosis code suggestions based on clinical descriptions.
Uses a local CSV database of ICD-10 codes with fuzzy matching.

This tool is invoked by the LangGraph agent when it needs to suggest
diagnosis codes for a patient encounter.
"""

import csv
import httpx
import logging
from pathlib import Path

from src.config import ICD10_DIR, LOG_LEVEL

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# ─── Stub ICD-10 database (used when no CSV is available) ──
STUB_ICD10_DB = {
    "hypertension": {"code": "I10", "description": "Essential (primary) hypertension"},
    "type 2 diabetes": {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications"},
    "diabetes mellitus": {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications"},
    "type 1 diabetes": {"code": "E10.9", "description": "Type 1 diabetes mellitus without complications"},
    "asthma": {"code": "J45.20", "description": "Mild intermittent asthma, uncomplicated"},
    "pneumonia": {"code": "J18.9", "description": "Pneumonia, unspecified organism"},
    "copd": {"code": "J44.1", "description": "Chronic obstructive pulmonary disease with acute exacerbation"},
    "acute myocardial infarction": {"code": "I21.9", "description": "Acute myocardial infarction, unspecified"},
    "stemi": {"code": "I21.3", "description": "ST elevation myocardial infarction of unspecified site"},
    "inferior stemi": {"code": "I21.1", "description": "ST elevation myocardial infarction of inferior wall"},
    "heart failure": {"code": "I50.9", "description": "Heart failure, unspecified"},
    "atrial fibrillation": {"code": "I48.91", "description": "Unspecified atrial fibrillation"},
    "urinary tract infection": {"code": "N39.0", "description": "Urinary tract infection, site not specified"},
    "appendicitis": {"code": "K35.80", "description": "Unspecified acute appendicitis"},
    "hypothyroidism": {"code": "E03.9", "description": "Hypothyroidism, unspecified"},
    "hyperthyroidism": {"code": "E05.90", "description": "Thyrotoxicosis, unspecified"},
    "depression": {"code": "F32.9", "description": "Major depressive disorder, single episode, unspecified"},
    "anxiety": {"code": "F41.9", "description": "Anxiety disorder, unspecified"},
    "migraine": {"code": "G43.909", "description": "Migraine, unspecified, not intractable"},
    "back pain": {"code": "M54.5", "description": "Low back pain"},
    "chest pain": {"code": "R07.9", "description": "Chest pain, unspecified"},
    "anemia": {"code": "D64.9", "description": "Anemia, unspecified"},
    "chronic kidney disease": {"code": "N18.9", "description": "Chronic kidney disease, unspecified"},
    "obesity": {"code": "E66.9", "description": "Obesity, unspecified"},
    "dvt": {"code": "I82.40", "description": "Acute embolism and thrombosis of unspecified deep veins of lower extremity"},
    "pulmonary embolism": {"code": "I26.99", "description": "Other pulmonary embolism without acute cor pulmonale"},
}


def _load_icd10_csv() -> dict:
    """Attempt to load ICD-10 codes from CSV file."""
    csv_files = list(ICD10_DIR.glob("*.csv"))
    if not csv_files:
        return {}

    codes = {}
    for csv_file in csv_files:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Adapt column names to your CSV format
                code = row.get("code", row.get("Code", ""))
                desc = row.get("description", row.get("Description", row.get("long_description", "")))
                if code and desc:
                    codes[desc.lower()] = {"code": code, "description": desc}
    return codes


def lookup_icd10(clinical_description: str) -> list[dict]:
    """Look up ICD-10 codes matching a clinical description.

    Args:
        clinical_description: Free-text clinical description (e.g., "type 2 diabetes")

    Returns:
        List of matching ICD-10 codes with descriptions.
    """
    query = clinical_description.lower().strip()
    matches = []

    # Use NIH Clinical Tables API for real-time ICD-10 CM coding
    base_url = "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"
    params = {
        "terms": query,
        "sf": "code,name",
        "maxList": 5
    }
    
    try:
        response = httpx.get(base_url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        # NIH API format: [count, [codes], None, [[code, description], ...]]
        if len(data) >= 4 and isinstance(data[3], list):
            results = data[3]
            for item in results:
                if len(item) >= 2:
                    matches.append(
                        {
                            "code": item[0],
                            "description": item[1],
                            "match_term": query,
                        }
                    )
    except httpx.RequestError as e:
        logger.warning(f"NIH Clinical Tables API request failed for '{query}': {e}")
        # Fall back to CSV/Stub if API fails
        db = _load_icd10_csv() or STUB_ICD10_DB
        for term, entry in db.items():
            if query in term or term in query:
                matches.append(
                    {
                        "code": entry["code"],
                        "description": entry["description"],
                        "match_term": term,
                    }
                )

    if not matches:
        # Partial word matching as fallback (only on local DB)
        db = _load_icd10_csv() or STUB_ICD10_DB
        query_words = set(query.split())
        for term, entry in db.items():
            term_words = set(term.split())
            overlap = query_words & term_words
            if len(overlap) >= 1 and len(overlap) / len(query_words) >= 0.3:
                matches.append(
                    {
                        "code": entry["code"],
                        "description": entry["description"],
                        "match_term": term,
                        "confidence": len(overlap) / len(query_words),
                    }
                )

    logger.info(f"ICD-10 lookup for '{clinical_description}': {len(matches)} matches")
    return matches


# ─── LangChain tool wrapper ──────────────────────────────
def icd10_tool(query: str) -> str:
    """LangChain-compatible tool function for ICD-10 lookup.

    Args:
        query: Clinical condition or diagnosis description.

    Returns:
        Formatted string of matching ICD-10 codes.
    """
    results = lookup_icd10(query)
    if not results:
        return f"No ICD-10 codes found for: {query}"

    lines = [f"ICD-10 codes for '{query}':"]
    for r in results:
        lines.append(f"  • {r['code']} — {r['description']}")
    return "\n".join(lines)


if __name__ == "__main__":
    # Quick test
    test_queries = ["type 2 diabetes", "hypertension", "chest pain", "asthma"]
    for q in test_queries:
        print(f"\n{icd10_tool(q)}")
