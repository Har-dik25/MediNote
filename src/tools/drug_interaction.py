"""
Drug Interaction Checker Tool.

Checks for drug-drug interactions using:
1. Local stub database (data/drug_interactions/interactions_db.json)
2. OpenFDA API (fallback / enrichment)

This tool is invoked by the LangGraph agent when it needs to check
for interactions between prescribed medications.
"""

import json
import logging
from pathlib import Path

import httpx

from src.config import DRUG_INTERACTIONS_DIR, LOG_LEVEL, OPENFDA_API_KEY

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


def _load_local_db() -> list[dict]:
    """Load the local drug interaction stub database."""
    db_path = DRUG_INTERACTIONS_DIR / "interactions_db.json"
    if not db_path.exists():
        logger.warning(f"Drug interaction DB not found: {db_path}")
        return []

    with open(db_path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_interactions_local(drugs: list[str]) -> list[dict]:
    """Check drug interactions against the local database.

    Args:
        drugs: List of drug names to check pairwise.

    Returns:
        List of interaction dicts with severity, description, and recommendation.
    """
    db = _load_local_db()
    if not db:
        return []

    interactions = []
    drug_names = [d.lower().strip() for d in drugs]

    for entry in db:
        a = entry["drug_a"].lower()
        b = entry["drug_b"].lower()
        if a in drug_names and b in drug_names:
            interactions.append(entry)
        elif a in drug_names or b in drug_names:
            # Check if any drug partially matches
            for drug in drug_names:
                if drug in a or a in drug or drug in b or b in drug:
                    interactions.append(entry)
                    break

    return interactions


def check_interactions_openfda(drug_name: str) -> list[dict]:
    """Query OpenFDA for drug interaction information.

    Args:
        drug_name: Name of the drug to look up.

    Returns:
        List of interaction warnings from FDA labeling.
    """
    base_url = "https://api.fda.gov/drug/label.json"
    params = {
        "search": f'drug_interactions:"{drug_name}"',
        "limit": 3,
    }
    if OPENFDA_API_KEY:
        params["api_key"] = OPENFDA_API_KEY

    try:
        response = httpx.get(base_url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()

        warnings = []
        for result in data.get("results", []):
            interactions = result.get("drug_interactions", [])
            brand = result.get("openfda", {}).get("brand_name", ["Unknown"])[0]
            for interaction_text in interactions:
                warnings.append(
                    {
                        "drug": brand,
                        "interaction_warning": interaction_text[:500],
                        "source": "OpenFDA",
                    }
                )
        return warnings

    except httpx.HTTPStatusError as e:
        logger.warning(f"OpenFDA API error for '{drug_name}': {e}")
        return []
    except httpx.RequestError as e:
        logger.warning(f"OpenFDA request failed for '{drug_name}': {e}")
        return []


def check_drug_interactions(drugs: list[str]) -> dict:
    """Full drug interaction check — local DB + OpenFDA.

    Args:
        drugs: List of drug names to check.

    Returns:
        Dict with 'interactions' list and 'warnings' list.
    """
    local_results = check_interactions_local(drugs)
    # OpenFDA check for each drug (optional enrichment)
    openfda_results = []
    # Fetch OpenFDA lookups for real-time interactions
    for drug in drugs:
        openfda_results.extend(check_interactions_openfda(drug))

    return {
        "drugs_checked": drugs,
        "interactions": local_results,
        "openfda_warnings": openfda_results,
        "total_flags": len(local_results) + len(openfda_results),
    }


# ─── LangChain tool wrapper ──────────────────────────────
def drug_interaction_tool(drugs_csv: str) -> str:
    """LangChain-compatible tool function for drug interaction checking.

    Args:
        drugs_csv: Comma-separated list of drug names.

    Returns:
        Formatted string of drug interaction results.
    """
    drugs = [d.strip() for d in drugs_csv.split(",") if d.strip()]
    if len(drugs) < 2:
        return "Please provide at least 2 drugs (comma-separated) to check interactions."

    result = check_drug_interactions(drugs)

    lines = [f"Drug interaction check for: {', '.join(drugs)}"]
    lines.append(f"Total flags: {result['total_flags']}")

    if result["interactions"]:
        lines.append("\n⚠️  Local DB Interactions:")
        for ix in result["interactions"]:
            lines.append(f"  • [{ix['severity'].upper()}] {ix['drug_a']} ↔ {ix['drug_b']}")
            lines.append(f"    {ix['description']}")
            lines.append(f"    → {ix['recommendation']}")
    else:
        lines.append("\n✅ No interactions found in local database.")

    if result["openfda_warnings"]:
        lines.append("\n📋 OpenFDA Warnings:")
        for w in result["openfda_warnings"]:
            lines.append(f"  • {w['drug']}: {w['interaction_warning'][:200]}")

    return "\n".join(lines)


if __name__ == "__main__":
    print(drug_interaction_tool("warfarin, aspirin"))
    print("\n" + "=" * 60)
    print(drug_interaction_tool("metformin, lisinopril"))
