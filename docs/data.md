# Data Sources Documentation

## Overview
MediMate uses three curated medical data sources, all publicly available and free. The data is scraped/generated locally, processed into text chunks, embedded using `sentence-transformers/all-MiniLM-L6-v2`, and stored in a local ChromaDB vector database.

**Total documents indexed:** 1,680
- NICE Guidelines: 792 chunks
- ICD-10 Codes: 123 entries
- Drug Reference: 765 chunks

---

## 1. NICE Clinical Guidelines

| Field | Value |
|-------|-------|
| **Source** | [NICE (National Institute for Health and Care Excellence)](https://www.nice.org.uk/) |
| **Format** | PDFs + HTML scraping |
| **License** | [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) — free to use with attribution |
| **Script** | `scrape_nice.py` |
| **Output** | `data/nice_guidelines/` (20 guideline text files + metadata.json) |
| **Schema** | Each chunk: `{text, metadata: {guideline, chunk_id, source_type}}` |

### Guidelines Included (20)
Asthma, Hypertension, Diabetes (Type 2), Depression (Adults), Generalised Anxiety, COPD, Heart Failure, Atrial Fibrillation, Chest Pain, UTI, Diabetes (Type 1 Adults), Chronic Kidney Disease, Headaches, Low Back Pain, Osteoarthritis, Epilepsy, Pneumonia (Community), Stroke/TIA, Venous Thromboembolism, Sepsis.

### How to Refresh
```bash
python scrape_nice.py
python setup_data.py  # Rebuilds vector store
```

---

## 2. OpenFDA Drug Reference

| Field | Value |
|-------|-------|
| **Source** | [OpenFDA API](https://open.fda.gov/) |
| **Format** | REST API (JSON) |
| **License** | Public domain (US Government work) |
| **Script** | `scrape_drug_data.py` |
| **Output** | `data/drug_reference/` |
| **Schema** | Each chunk: `{text, metadata: {drug_name, chunk_id, source_type}}` |

### Data Fields Extracted
- Generic name, brand name
- Indications and usage
- Warnings and precautions
- Drug interactions
- Adverse reactions
- Dosage and administration

### How to Refresh
```bash
python scrape_drug_data.py
python setup_data.py  # Rebuilds vector store
```

---

## 3. ICD-10-CM Codes

| Field | Value |
|-------|-------|
| **Source** | Generated locally from curated medical coding reference |
| **Format** | Python-generated (structured text) |
| **License** | Public domain (CMS/WHO) |
| **Script** | `scrape_icd10.py` |
| **Output** | `data/icd10_codes/` |
| **Schema** | Each entry: `{text: "Code: X00.0\nDescription: ...\nCategory: ...", metadata: {code, category, chunk_id}}` |

### Coverage
123 commonly-used ICD-10-CM codes across categories including:
- Infectious diseases
- Neoplasms
- Endocrine/metabolic disorders
- Mental health
- Nervous system
- Circulatory system
- Respiratory system
- Digestive system
- Musculoskeletal
- Genitourinary
- Symptoms/signs (R-codes)

### How to Refresh
```bash
python scrape_icd10.py
python setup_data.py  # Rebuilds vector store
```

---

## Data Pipeline Architecture

```
scrape_nice.py ──────┐
scrape_drug_data.py ──┼──→ data/ ──→ data_processor.py ──→ rag_engine.py ──→ ChromaDB
scrape_icd10.py ──────┘     (raw)     (chunk + clean)       (embed + index)   (vector store)
```

The full pipeline is orchestrated by `setup_data.py` and takes ~8-10 minutes on a standard internet connection.
