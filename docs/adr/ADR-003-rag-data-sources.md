# ADR-003: RAG Data Sources — NICE Guidelines, OpenFDA, and ICD-10

## Context
MediMate's RAG pipeline needs authoritative medical knowledge to ground the LLM's SOAP note generation in evidence-based clinical practice. The data sources must be: (a) publicly available and free, (b) authoritative and clinician-trusted, (c) structured enough to chunk and embed meaningfully, and (d) covering the three core use cases: clinical guidelines, drug information, and diagnostic coding.

## Decision
We chose three data sources, each covering a distinct clinical need:

| Source | Purpose | Collection | Documents |
|--------|---------|------------|-----------|
| **NICE Clinical Guidelines** | Evidence-based treatment recommendations | `nice_guidelines` | 792 chunks from 20 guidelines |
| **OpenFDA Drug Database** | Drug information, interactions, adverse events | `drug_reference` | 765 chunks |
| **ICD-10-CM Codes** | Diagnostic coding for billing and records | `icd10_codes` | 123 entries |

## Consequences

### Positive
- **Authoritative:** NICE (National Institute for Health and Care Excellence) guidelines are the gold standard for evidence-based medicine in the UK and are widely respected globally. OpenFDA is the US FDA's official public data portal. ICD-10-CM is the universal medical coding standard.
- **Free and public:** All three sources are openly available without API keys or subscriptions. NICE guidelines are published as PDFs and web pages. OpenFDA has a free REST API. ICD-10 codes are public domain.
- **Complementary coverage:** Guidelines tell the LLM *what to recommend*, drug data tells it *what to watch out for*, and ICD-10 codes help it *classify* the diagnosis. Together they cover the full SOAP workflow.
- **Refreshable:** The scraper scripts (`scrape_nice.py`, `scrape_drug_data.py`, `scrape_icd10.py`) can be re-run to update the knowledge base without code changes.

### Negative
- **UK-centric guidelines:** NICE guidelines are UK-specific. A production system serving Indian or US doctors would need to add local guidelines (e.g., ICMR for India, AHA/ACC for the US).
- **Limited drug coverage:** OpenFDA's free API returns structured adverse event data, not full drug monographs. A production system would integrate DailyMed, RxNorm, or a commercial drug database.
- **Shallow ICD-10 coverage:** We include 123 commonly-used codes generated locally. The full ICD-10-CM has ~70,000 codes. A production system would need the complete CMS code set.
- **Static data:** The scraped data is a snapshot. NICE guidelines update periodically. There's no automated refresh pipeline — someone must re-run `setup_data.py`.

## Alternatives Considered

| Source | Why rejected / deferred |
|--------|----------------------|
| **UpToDate / BMJ Best Practice** | Gold-standard clinical reference, but behind a paywall. Not feasible for a zero-cost project. |
| **PubMed / MEDLINE** | Huge corpus but articles are research papers, not actionable clinical guidelines. Would need significant processing to extract recommendations. |
| **DailyMed (NLM)** | Excellent drug label database. Considered for v2 but OpenFDA was faster to integrate for the MVP. |
| **WHO ICD-11** | The newer standard, but adoption is still limited. ICD-10-CM remains the billing standard in the US and is more widely recognized. |
| **SNOMED CT** | Comprehensive clinical terminology but requires a license agreement. ICD-10 is simpler and sufficient for our coding use case. |
