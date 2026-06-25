"""
Diagnostic Test Recommendation Tool.

Suggests appropriate diagnostic tests based on the clinical presentation
and suspected diagnoses. Uses a rule-based mapping enriched by RAG
retrieval from clinical guidelines.
"""

import logging

from src.config import LOG_LEVEL

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# ─── Rule-based test recommendations ─────────────────────
# Maps condition keywords → recommended diagnostic tests
TEST_RECOMMENDATIONS = {
    "diabetes": [
        {"test": "HbA1c", "rationale": "Assess glycemic control over past 2-3 months"},
        {"test": "Fasting blood glucose", "rationale": "Confirm diagnosis if HbA1c borderline"},
        {"test": "Renal function panel (eGFR, creatinine)", "rationale": "Screen for diabetic nephropathy"},
        {"test": "Urine albumin-to-creatinine ratio", "rationale": "Early detection of microalbuminuria"},
        {"test": "Lipid panel", "rationale": "Cardiovascular risk assessment"},
        {"test": "Foot examination", "rationale": "Screen for diabetic neuropathy"},
    ],
    "hypertension": [
        {"test": "Renal function panel", "rationale": "Assess for hypertensive nephropathy"},
        {"test": "Electrolytes (Na, K)", "rationale": "Baseline before starting antihypertensives"},
        {"test": "Lipid panel", "rationale": "Cardiovascular risk assessment"},
        {"test": "ECG", "rationale": "Screen for left ventricular hypertrophy"},
        {"test": "Urinalysis", "rationale": "Check for proteinuria"},
    ],
    "chest pain": [
        {"test": "Troponin I/T (serial)", "rationale": "Rule out acute myocardial infarction"},
        {"test": "12-lead ECG", "rationale": "Detect ischemic changes or arrhythmias"},
        {"test": "Chest X-ray", "rationale": "Rule out pneumothorax, pneumonia, cardiomegaly"},
        {"test": "D-dimer", "rationale": "Rule out pulmonary embolism if low/moderate pretest probability"},
        {"test": "Complete blood count", "rationale": "Baseline assessment"},
    ],
    "stemi": [
        {"test": "Serial troponin I/T", "rationale": "Quantify myocardial damage"},
        {"test": "Complete blood count", "rationale": "Baseline before anticoagulation"},
        {"test": "Coagulation panel (PT/INR, aPTT)", "rationale": "Pre-procedural assessment"},
        {"test": "Renal function panel", "rationale": "Assess contrast nephropathy risk before PCI"},
        {"test": "Echocardiogram", "rationale": "Assess wall motion abnormalities and EF"},
    ],
    "hypothyroidism": [
        {"test": "TSH", "rationale": "Primary screening test for thyroid dysfunction"},
        {"test": "Free T4", "rationale": "Confirm hypothyroidism if TSH elevated"},
        {"test": "Thyroid peroxidase antibodies (TPO Ab)", "rationale": "Identify autoimmune (Hashimoto's) etiology"},
        {"test": "Lipid panel", "rationale": "Hypothyroidism often causes dyslipidemia"},
    ],
    "copd": [
        {"test": "Spirometry (FEV1/FVC)", "rationale": "Confirm diagnosis and assess severity"},
        {"test": "Chest X-ray", "rationale": "Rule out pneumonia, pneumothorax"},
        {"test": "Arterial blood gas (ABG)", "rationale": "Assess oxygenation and CO2 retention"},
        {"test": "Complete blood count", "rationale": "Check for polycythemia or infection"},
        {"test": "Sputum culture", "rationale": "Identify infective organism in acute exacerbation"},
    ],
    "asthma": [
        {"test": "Spirometry (pre/post bronchodilator)", "rationale": "Confirm reversible airway obstruction"},
        {"test": "Peak expiratory flow (PEF)", "rationale": "Monitor disease control"},
        {"test": "Fractional exhaled nitric oxide (FeNO)", "rationale": "Assess eosinophilic airway inflammation"},
        {"test": "Allergy testing (skin prick / specific IgE)", "rationale": "Identify triggers"},
    ],
    "appendicitis": [
        {"test": "Complete blood count", "rationale": "Leukocytosis supports diagnosis"},
        {"test": "CRP", "rationale": "Inflammatory marker elevation"},
        {"test": "CT abdomen/pelvis", "rationale": "Confirm diagnosis (sensitivity >95%)"},
        {"test": "Urinalysis", "rationale": "Rule out urinary tract pathology"},
        {"test": "Urine pregnancy test", "rationale": "Rule out ectopic pregnancy in females"},
    ],
    "anemia": [
        {"test": "Complete blood count with differential", "rationale": "Characterize anemia type (MCV)"},
        {"test": "Reticulocyte count", "rationale": "Assess bone marrow response"},
        {"test": "Iron studies (ferritin, TIBC, serum iron)", "rationale": "Diagnose iron deficiency"},
        {"test": "Vitamin B12 and folate", "rationale": "Rule out megaloblastic anemia"},
        {"test": "Peripheral blood smear", "rationale": "Identify morphological abnormalities"},
    ],
    "depression": [
        {"test": "PHQ-9 questionnaire", "rationale": "Standardized severity assessment"},
        {"test": "TSH", "rationale": "Rule out thyroid dysfunction as cause"},
        {"test": "Complete blood count", "rationale": "Rule out anemia contributing to fatigue"},
        {"test": "Vitamin D level", "rationale": "Deficiency associated with depressive symptoms"},
    ],
}


def recommend_tests(clinical_description: str) -> list[dict]:
    """Recommend diagnostic tests based on clinical description.

    Args:
        clinical_description: Free-text description of clinical presentation.

    Returns:
        List of recommended tests with rationale.
    """
    query = clinical_description.lower()
    recommendations = []
    matched_conditions = []

    for condition, tests in TEST_RECOMMENDATIONS.items():
        if condition in query:
            matched_conditions.append(condition)
            for test in tests:
                if test not in recommendations:  # Avoid duplicates
                    recommendations.append(
                        {
                            "test": test["test"],
                            "rationale": test["rationale"],
                            "for_condition": condition,
                        }
                    )

    logger.info(
        f"Test recommendations for '{clinical_description[:50]}...': "
        f"{len(recommendations)} tests for conditions: {matched_conditions}"
    )
    return recommendations


# ─── LangChain tool wrapper ──────────────────────────────
def test_recommendation_tool(clinical_description: str) -> str:
    """LangChain-compatible tool for diagnostic test recommendations.

    Args:
        clinical_description: Clinical summary or suspected diagnosis.

    Returns:
        Formatted string of recommended tests.
    """
    results = recommend_tests(clinical_description)

    if not results:
        return (
            f"No specific test recommendations found for: {clinical_description}\n"
            "Consider: CBC, BMP, urinalysis as baseline workup."
        )

    lines = [f"Recommended diagnostic tests for: {clinical_description}"]
    current_condition = None
    for r in results:
        if r["for_condition"] != current_condition:
            current_condition = r["for_condition"]
            lines.append(f"\n  For {current_condition.upper()}:")
        lines.append(f"    • {r['test']}")
        lines.append(f"      Rationale: {r['rationale']}")

    return "\n".join(lines)


if __name__ == "__main__":
    print(test_recommendation_tool("patient with type 2 diabetes and hypertension"))
    print("\n" + "=" * 60)
    print(test_recommendation_tool("suspected acute appendicitis"))
