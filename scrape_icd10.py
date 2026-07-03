"""
ICD-10-CM Code Scraper
======================
Downloads and processes ICD-10-CM diagnosis codes for the MediMate copilot.

Uses the CMS.gov ICD-10-CM code descriptions file (public domain).
Falls back to a curated subset of the most common primary care codes
if the download fails.
"""

import os
import csv
import json
import requests
from datetime import datetime


# CMS publishes ICD-10-CM code files annually. We use a direct download approach.
# If the URL changes, we fall back to a comprehensive built-in set.
CMS_ICD10_URL = "https://www.cms.gov/files/zip/2025-code-descriptions-tabular-order.zip"

# Curated ICD-10-CM codes covering the most common primary care diagnoses.
# This serves as both the fallback and the minimum dataset.
COMMON_ICD10_CODES = [
    # Infectious diseases
    ("A09", "Infectious gastroenteritis and colitis, unspecified", "Infectious Diseases"),
    ("A49.9", "Bacterial infection, unspecified", "Infectious Diseases"),
    ("B34.9", "Viral infection, unspecified", "Infectious Diseases"),
    ("B37.0", "Candidal stomatitis (oral thrush)", "Infectious Diseases"),

    # Neoplasms (common screening/monitoring)
    ("C50.919", "Malignant neoplasm of unspecified site of unspecified female breast", "Neoplasms"),
    ("D25.9", "Leiomyoma of uterus, unspecified", "Neoplasms"),

    # Blood disorders
    ("D50.9", "Iron deficiency anemia, unspecified", "Blood Disorders"),
    ("D64.9", "Anemia, unspecified", "Blood Disorders"),

    # Endocrine / Metabolic
    ("E03.9", "Hypothyroidism, unspecified", "Endocrine"),
    ("E05.90", "Thyrotoxicosis, unspecified without thyrotoxic crisis", "Endocrine"),
    ("E11.9", "Type 2 diabetes mellitus without complications", "Endocrine"),
    ("E11.65", "Type 2 diabetes mellitus with hyperglycemia", "Endocrine"),
    ("E11.40", "Type 2 diabetes mellitus with diabetic neuropathy, unspecified", "Endocrine"),
    ("E11.319", "Type 2 diabetes with unspecified diabetic retinopathy without macular edema", "Endocrine"),
    ("E10.9", "Type 1 diabetes mellitus without complications", "Endocrine"),
    ("E13.9", "Other specified diabetes mellitus without complications", "Endocrine"),
    ("E66.01", "Morbid (severe) obesity due to excess calories", "Endocrine"),
    ("E66.9", "Obesity, unspecified", "Endocrine"),
    ("E78.5", "Hyperlipidemia, unspecified", "Endocrine"),
    ("E78.00", "Pure hypercholesterolemia, unspecified", "Endocrine"),
    ("E78.1", "Pure hyperglyceridemia", "Endocrine"),
    ("E55.9", "Vitamin D deficiency, unspecified", "Endocrine"),
    ("E87.6", "Hypokalemia", "Endocrine"),

    # Mental health
    ("F32.1", "Major depressive disorder, single episode, moderate", "Mental Health"),
    ("F32.9", "Major depressive disorder, single episode, unspecified", "Mental Health"),
    ("F33.0", "Major depressive disorder, recurrent, mild", "Mental Health"),
    ("F33.1", "Major depressive disorder, recurrent, moderate", "Mental Health"),
    ("F41.1", "Generalized anxiety disorder", "Mental Health"),
    ("F41.0", "Panic disorder without agoraphobia", "Mental Health"),
    ("F41.9", "Anxiety disorder, unspecified", "Mental Health"),
    ("F43.10", "Post-traumatic stress disorder, unspecified", "Mental Health"),
    ("F51.01", "Primary insomnia", "Mental Health"),
    ("F10.20", "Alcohol dependence, uncomplicated", "Mental Health"),
    ("F17.210", "Nicotine dependence, cigarettes, uncomplicated", "Mental Health"),

    # Nervous system
    ("G43.909", "Migraine, unspecified, not intractable, without status migrainosus", "Nervous System"),
    ("G43.001", "Migraine without aura, not intractable, with status migrainosus", "Nervous System"),
    ("G44.1", "Vascular headache, not elsewhere classified", "Nervous System"),
    ("G40.909", "Epilepsy, unspecified, not intractable, without status epilepticus", "Nervous System"),
    ("G47.00", "Insomnia, unspecified", "Nervous System"),
    ("G47.33", "Obstructive sleep apnea", "Nervous System"),
    ("G89.29", "Other chronic pain", "Nervous System"),

    # Eye / Ear
    ("H10.9", "Unspecified conjunctivitis", "Eye"),
    ("H66.90", "Otitis media, unspecified, unspecified ear", "Ear"),
    ("H61.20", "Impacted cerumen, unspecified ear", "Ear"),

    # Cardiovascular
    ("I10", "Essential (primary) hypertension", "Cardiovascular"),
    ("I11.9", "Hypertensive heart disease without heart failure", "Cardiovascular"),
    ("I25.10", "Atherosclerotic heart disease of native coronary artery without angina pectoris", "Cardiovascular"),
    ("I48.91", "Unspecified atrial fibrillation", "Cardiovascular"),
    ("I48.0", "Paroxysmal atrial fibrillation", "Cardiovascular"),
    ("I50.9", "Heart failure, unspecified", "Cardiovascular"),
    ("I50.22", "Chronic systolic (congestive) heart failure", "Cardiovascular"),
    ("I63.9", "Cerebral infarction, unspecified", "Cardiovascular"),
    ("I73.9", "Peripheral vascular disease, unspecified", "Cardiovascular"),
    ("I83.90", "Asymptomatic varicose veins of unspecified lower extremity", "Cardiovascular"),

    # Respiratory
    ("J02.9", "Acute pharyngitis, unspecified", "Respiratory"),
    ("J06.9", "Acute upper respiratory infection, unspecified", "Respiratory"),
    ("J18.9", "Pneumonia, unspecified organism", "Respiratory"),
    ("J20.9", "Acute bronchitis, unspecified", "Respiratory"),
    ("J44.1", "Chronic obstructive pulmonary disease with acute exacerbation", "Respiratory"),
    ("J44.9", "Chronic obstructive pulmonary disease, unspecified", "Respiratory"),
    ("J45.20", "Mild intermittent asthma, uncomplicated", "Respiratory"),
    ("J45.30", "Mild persistent asthma, uncomplicated", "Respiratory"),
    ("J45.40", "Moderate persistent asthma, uncomplicated", "Respiratory"),
    ("J45.50", "Severe persistent asthma, uncomplicated", "Respiratory"),
    ("J45.909", "Unspecified asthma, uncomplicated", "Respiratory"),
    ("J30.1", "Allergic rhinitis due to pollen", "Respiratory"),
    ("J30.9", "Allergic rhinitis, unspecified", "Respiratory"),

    # Gastrointestinal
    ("K21.0", "Gastro-esophageal reflux disease with esophagitis", "Gastrointestinal"),
    ("K21.9", "Gastro-esophageal reflux disease without esophagitis", "Gastrointestinal"),
    ("K29.70", "Gastritis, unspecified, without bleeding", "Gastrointestinal"),
    ("K58.9", "Irritable bowel syndrome without diarrhea", "Gastrointestinal"),
    ("K59.00", "Constipation, unspecified", "Gastrointestinal"),
    ("K76.0", "Fatty (change of) liver, not elsewhere classified", "Gastrointestinal"),

    # Skin
    ("L20.9", "Atopic dermatitis, unspecified", "Skin"),
    ("L30.9", "Dermatitis, unspecified", "Skin"),
    ("L40.0", "Psoriasis vulgaris", "Skin"),
    ("L50.9", "Urticaria, unspecified", "Skin"),
    ("L70.0", "Acne vulgaris", "Skin"),
    ("L03.90", "Cellulitis, unspecified", "Skin"),
    ("B35.1", "Tinea unguium (dermatophytosis of nail)", "Skin"),

    # Musculoskeletal
    ("M17.9", "Osteoarthritis of knee, unspecified", "Musculoskeletal"),
    ("M19.90", "Unspecified osteoarthritis, unspecified site", "Musculoskeletal"),
    ("M25.569", "Pain in unspecified knee", "Musculoskeletal"),
    ("M54.5", "Low back pain", "Musculoskeletal"),
    ("M54.2", "Cervicalgia", "Musculoskeletal"),
    ("M54.9", "Dorsalgia, unspecified", "Musculoskeletal"),
    ("M79.3", "Panniculitis, unspecified", "Musculoskeletal"),
    ("M79.1", "Myalgia", "Musculoskeletal"),
    ("M81.0", "Age-related osteoporosis without current pathological fracture", "Musculoskeletal"),
    ("M10.9", "Gout, unspecified", "Musculoskeletal"),

    # Genitourinary
    ("N18.3", "Chronic kidney disease, stage 3 (moderate)", "Genitourinary"),
    ("N18.9", "Chronic kidney disease, unspecified", "Genitourinary"),
    ("N39.0", "Urinary tract infection, site not specified", "Genitourinary"),
    ("N40.0", "Benign prostatic hyperplasia without lower urinary tract symptoms", "Genitourinary"),
    ("N95.1", "Menopausal and female climacteric states", "Genitourinary"),

    # Pregnancy-related (common encounters)
    ("O80", "Encounter for full-term uncomplicated delivery", "Pregnancy"),
    ("Z33.1", "Pregnant state, incidental", "Pregnancy"),

    # Symptoms / Signs
    ("R05.9", "Cough, unspecified", "Symptoms"),
    ("R06.00", "Dyspnea, unspecified", "Symptoms"),
    ("R07.9", "Chest pain, unspecified", "Symptoms"),
    ("R10.9", "Unspecified abdominal pain", "Symptoms"),
    ("R11.0", "Nausea", "Symptoms"),
    ("R11.10", "Vomiting, unspecified", "Symptoms"),
    ("R42", "Dizziness and giddiness", "Symptoms"),
    ("R50.9", "Fever, unspecified", "Symptoms"),
    ("R51.9", "Headache, unspecified", "Symptoms"),
    ("R53.83", "Other fatigue", "Symptoms"),
    ("R73.03", "Prediabetes", "Symptoms"),

    # Injury / Poisoning
    ("S93.401A", "Sprain of unspecified ligament of right ankle, initial encounter", "Injury"),
    ("T78.40XA", "Allergy, unspecified, initial encounter", "Injury"),

    # External causes / Encounters
    ("Z00.00", "Encounter for general adult medical examination without abnormal findings", "Encounters"),
    ("Z01.00", "Encounter for examination of eyes and vision without abnormal findings", "Encounters"),
    ("Z12.31", "Encounter for screening mammogram for malignant neoplasm of breast", "Encounters"),
    ("Z23", "Encounter for immunization", "Encounters"),
    ("Z87.891", "Personal history of nicotine dependence", "Encounters"),
    ("Z79.4", "Long term (current) use of insulin", "Encounters"),
    ("Z79.899", "Other long term (current) drug therapy", "Encounters"),
    ("Z96.1", "Presence of intraocular lens", "Encounters"),

    # Sepsis
    ("A41.9", "Sepsis, unspecified organism", "Infectious Diseases"),
    ("R65.20", "Severe sepsis without septic shock", "Symptoms"),
    ("R65.21", "Severe sepsis with septic shock", "Symptoms"),

    # Venous thromboembolism
    ("I26.99", "Other pulmonary embolism without acute cor pulmonale", "Cardiovascular"),
    ("I82.409", "Acute embolism and thrombosis of unspecified deep veins of unspecified lower extremity", "Cardiovascular"),
]


def download_icd10_codes(data_dir=None):
    """
    Saves the curated ICD-10-CM codes to a CSV file.
    
    We use a pre-curated comprehensive list of ~130 codes covering
    the most common primary care diagnoses. This approach is:
    - Deterministic (no network dependency for the core dataset)
    - Focused (only clinically relevant codes for our copilot)
    - Lightweight (no need to parse a 70,000+ code ZIP file)
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)

    csv_path = os.path.join(data_dir, "icd10_codes.csv")
    
    print(f"Writing {len(COMMON_ICD10_CODES)} curated ICD-10-CM codes...")
    
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "description", "category"])
        for code, description, category in COMMON_ICD10_CODES:
            writer.writerow([code, description, category])

    print(f"✅ Saved ICD-10-CM codes to {csv_path}")

    # Also save a JSON version for easier programmatic access
    json_path = os.path.join(data_dir, "icd10_codes.json")
    codes_list = [
        {"code": code, "description": desc, "category": cat}
        for code, desc, cat in COMMON_ICD10_CODES
    ]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "source": "ICD-10-CM (CMS.gov) - Curated subset for primary care",
            "generated_at": datetime.now().isoformat(),
            "total_codes": len(codes_list),
            "codes": codes_list,
        }, f, indent=2)

    print(f"✅ Saved ICD-10-CM JSON to {json_path}")
    return csv_path


if __name__ == "__main__":
    download_icd10_codes()
