"""
Drug Reference Data Scraper
============================
Fetches commonly prescribed drug data from the OpenFDA Drug Label API.

Extracts: generic name, brand name, indications, contraindications,
warnings, adverse reactions, and drug interactions.
"""

import os
import json
import time
import requests
from datetime import datetime


# Top ~100 commonly prescribed drugs in primary care
# (generic names, as used by OpenFDA)
COMMON_DRUGS = [
    # Cardiovascular
    "Amlodipine", "Lisinopril", "Losartan", "Metoprolol", "Atenolol",
    "Ramipril", "Enalapril", "Valsartan", "Hydrochlorothiazide", "Furosemide",
    "Spironolactone", "Digoxin", "Diltiazem", "Nifedipine", "Candesartan",
    "Bisoprolol", "Doxazosin", "Indapamide", "Bendroflumethiazide",

    # Statins / Lipid lowering
    "Atorvastatin", "Rosuvastatin", "Simvastatin", "Pravastatin",
    "Ezetimibe", "Fenofibrate",

    # Anticoagulants / Antiplatelets
    "Warfarin", "Aspirin", "Clopidogrel", "Apixaban", "Rivaroxaban",
    "Edoxaban", "Dabigatran", "Enoxaparin",

    # Diabetes
    "Metformin", "Gliclazide", "Glimepiride", "Sitagliptin", "Empagliflozin",
    "Dapagliflozin", "Canagliflozin", "Liraglutide", "Semaglutide",
    "Insulin Glargine", "Pioglitazone",

    # Respiratory
    "Salbutamol", "Montelukast", "Budesonide", "Fluticasone",
    "Tiotropium", "Ipratropium", "Theophylline", "Prednisolone",
    "Beclomethasone",

    # Mental Health
    "Sertraline", "Fluoxetine", "Citalopram", "Escitalopram", "Paroxetine",
    "Venlafaxine", "Duloxetine", "Mirtazapine", "Amitriptyline",
    "Diazepam", "Lorazepam", "Alprazolam", "Quetiapine", "Olanzapine",
    "Lithium", "Aripiprazole",

    # Pain / Anti-inflammatory
    "Paracetamol", "Ibuprofen", "Naproxen", "Diclofenac", "Codeine",
    "Tramadol", "Morphine", "Gabapentin", "Pregabalin", "Celecoxib",
    "Colchicine", "Allopurinol",

    # Antibiotics
    "Amoxicillin", "Co-amoxiclav", "Doxycycline", "Azithromycin",
    "Ciprofloxacin", "Trimethoprim", "Nitrofurantoin", "Flucloxacillin",
    "Clarithromycin", "Metronidazole", "Cefalexin",

    # GI
    "Omeprazole", "Lansoprazole", "Pantoprazole", "Ranitidine",
    "Domperidone", "Loperamide", "Lactulose",

    # Thyroid
    "Levothyroxine", "Carbimazole",

    # Epilepsy
    "Levetiracetam", "Sodium Valproate", "Carbamazepine", "Lamotrigine",
    "Phenytoin",

    # Other
    "Folic Acid", "Ferrous Sulfate", "Cholecalciferol", "Alendronic Acid",
]


def _fetch_drug_label(drug_name):
    """
    Fetch drug label data from OpenFDA's drug label endpoint.
    Returns a dict with structured drug information, or None on failure.
    """
    base_url = "https://api.fda.gov/drug/label.json"
    # Search by generic name OR brand name
    query = f'openfda.generic_name:"{drug_name}" OR openfda.brand_name:"{drug_name}"'
    url = f"{base_url}?search={query}&limit=1"

    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("results"):
                result = data["results"][0]
                openfda = result.get("openfda", {})

                drug_info = {
                    "generic_name": _first_or_default(openfda.get("generic_name", []), drug_name),
                    "brand_name": _first_or_default(openfda.get("brand_name", []), "N/A"),
                    "manufacturer": _first_or_default(openfda.get("manufacturer_name", []), "N/A"),
                    "route": _first_or_default(openfda.get("route", []), "N/A"),
                    "substance_name": _first_or_default(openfda.get("substance_name", []), "N/A"),
                    "pharm_class": openfda.get("pharm_class_epc", []),
                    "indications_and_usage": _truncate_field(result.get("indications_and_usage", ["N/A"])),
                    "contraindications": _truncate_field(result.get("contraindications", ["N/A"])),
                    "warnings": _truncate_field(result.get("warnings", ["N/A"])),
                    "adverse_reactions": _truncate_field(result.get("adverse_reactions", ["N/A"])),
                    "drug_interactions": _truncate_field(result.get("drug_interactions", ["N/A"])),
                    "dosage_and_administration": _truncate_field(result.get("dosage_and_administration", ["N/A"])),
                }
                return drug_info
        elif resp.status_code == 404:
            return None
    except Exception as e:
        print(f"    ⚠️  API error for {drug_name}: {e}")
    return None


def _first_or_default(lst, default="N/A"):
    """Return first element of list or default."""
    return lst[0] if lst else default


def _truncate_field(field_list, max_chars=2000):
    """
    OpenFDA label fields can be very long. Truncate to keep
    the dataset manageable while preserving key information.
    """
    if not field_list:
        return "N/A"
    text = field_list[0] if isinstance(field_list, list) else str(field_list)
    if len(text) > max_chars:
        return text[:max_chars] + "... [truncated]"
    return text


def download_drug_data(data_dir=None):
    """
    Fetch drug reference data for common medications from OpenFDA.
    Saves a comprehensive JSON file with drug information.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)

    print(f"Fetching drug data for {len(COMMON_DRUGS)} medications from OpenFDA...")
    print("(This may take a few minutes due to API rate limiting)\n")

    drugs = []
    failed = []
    total = len(COMMON_DRUGS)

    for idx, drug_name in enumerate(COMMON_DRUGS, 1):
        print(f"  [{idx}/{total}] {drug_name}...", end=" ")
        drug_info = _fetch_drug_label(drug_name)
        if drug_info:
            drugs.append(drug_info)
            print("✅")
        else:
            failed.append(drug_name)
            print("❌ (not found)")

        # Rate limit: OpenFDA allows ~240 requests/minute without an API key
        # We add a small delay to be safe
        time.sleep(0.3)

    # Save results
    output = {
        "source": "OpenFDA Drug Label API",
        "generated_at": datetime.now().isoformat(),
        "total_drugs": len(drugs),
        "failed_lookups": failed,
        "drugs": drugs,
    }

    json_path = os.path.join(data_dir, "drug_reference.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 50}")
    print(f"SUMMARY: {len(drugs)}/{total} drugs fetched, {len(failed)} failed.")
    if failed:
        print(f"Failed: {', '.join(failed[:10])}{'...' if len(failed) > 10 else ''}")
    print(f"Saved to: {json_path}")
    print(f"{'=' * 50}")

    return json_path


if __name__ == "__main__":
    download_drug_data()
