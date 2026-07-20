"""
Data Processor
==============
Extracts text from clinical guideline PDFs and text files, chunks all
data sources (guidelines, ICD-10, drugs) for RAG ingestion.

Supported guideline sources:
  - NICE (UK)     — region: UK
  - WHO  (Global) — region: Global
  - CDC  (US)     — region: North America
  - EMA  (EU)     — region: Europe

Chunking strategy:
  - Clinical guidelines: section-based splitting using headings
  - ICD-10 codes: one chunk per code (small, searchable)
  - Drug data: one chunk per drug with structured fields
"""

import os
import csv
import json
import re
from typing import List, Dict, Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file using pdfplumber.
    Falls back to a simple message if pdfplumber is not installed.
    """
    if pdfplumber is None:
        print(f"  ⚠️  pdfplumber not installed. Skipping PDF: {pdf_path}")
        return ""

    try:
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except Exception as e:
        print(f"  ⚠️  Error extracting PDF {pdf_path}: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks of approximately chunk_size characters.
    Tries to split at paragraph/sentence boundaries for cleaner chunks.
    """
    if not text or len(text) < chunk_size:
        return [text] if text else []

    chunks = []
    # Split by double newlines (paragraphs) first
    paragraphs = re.split(r'\n\s*\n', text)

    current_chunk = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk += ("\n\n" + para) if current_chunk else para
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # If a single paragraph is longer than chunk_size, split by sentences
            if len(para) > chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                current_chunk = ""
                for sent in sentences:
                    if len(current_chunk) + len(sent) + 1 <= chunk_size:
                        current_chunk += (" " + sent) if current_chunk else sent
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sent
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk.strip())

    # Add overlap: prepend last `overlap` chars of previous chunk to the next
    if overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-overlap:]
            overlapped.append(prev_tail + "\n..." + chunks[i])
        chunks = overlapped

    return chunks


def process_nice_guidelines(data_dir: str = None) -> List[Dict]:
    """
    Process all NICE guideline text files into chunks for RAG.
    
    Returns a list of dicts:
      { "text": ..., "metadata": { "source": ..., "guideline": ..., "chunk_id": ... } }
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data", "nice_guidelines")

    if not os.path.exists(data_dir):
        print("⚠️  NICE guidelines directory not found. Run scrape_nice.py first.")
        return []

    documents = []
    txt_files = sorted([f for f in os.listdir(data_dir) if f.endswith(".txt")])

    if not txt_files:
        # Try extracting from PDFs if no .txt files exist
        pdf_files = sorted([f for f in os.listdir(data_dir) if f.endswith(".pdf")])
        for pdf_file in pdf_files:
            pdf_path = os.path.join(data_dir, pdf_file)
            name = os.path.splitext(pdf_file)[0]
            print(f"  Extracting text from PDF: {pdf_file}...")
            text = extract_text_from_pdf(pdf_path)
            if text:
                txt_path = os.path.join(data_dir, f"{name}.txt")
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(f"NICE Guideline: {name}\n")
                    f.write(f"Source: PDF extraction\n")
                    f.write("=" * 80 + "\n\n")
                    f.write(text)
                txt_files.append(f"{name}.txt")

    for txt_file in txt_files:
        txt_path = os.path.join(data_dir, txt_file)
        guideline_name = os.path.splitext(txt_file)[0]

        print(f"  Chunking: {guideline_name}...")
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text, chunk_size=1000, overlap=150)

        for i, chunk in enumerate(chunks):
            documents.append({
                "text": chunk,
                "metadata": {
                    "source": "NICE",
                    "region": "UK",
                    "guideline": guideline_name,
                    "chunk_id": f"nice_{guideline_name}_{i}",
                    "type": "clinical_guideline",
                },
            })

    print(f"  ✅ Processed {len(txt_files)} guidelines into {len(documents)} chunks.")
    return documents


def process_who_guidelines(data_dir: str = None) -> List[Dict]:
    """
    Process all WHO guideline text files into chunks for RAG.
    Each chunk is tagged with region='Global'.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data", "who_guidelines")

    if not os.path.exists(data_dir):
        print("⚠️  WHO guidelines directory not found. Run scrape_who.py first.")
        return []

    documents = []
    txt_files = sorted([f for f in os.listdir(data_dir) if f.endswith(".txt")])

    for txt_file in txt_files:
        txt_path = os.path.join(data_dir, txt_file)
        guideline_name = os.path.splitext(txt_file)[0]

        print(f"  Chunking: {guideline_name}...")
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text, chunk_size=1000, overlap=150)

        for i, chunk in enumerate(chunks):
            documents.append({
                "text": chunk,
                "metadata": {
                    "source": "WHO",
                    "region": "Global",
                    "guideline": guideline_name,
                    "chunk_id": f"who_{guideline_name}_{i}",
                    "type": "clinical_guideline",
                },
            })

    print(f"  ✅ Processed {len(txt_files)} WHO guidelines into {len(documents)} chunks.")
    return documents


def process_cdc_guidelines(data_dir: str = None) -> List[Dict]:
    """
    Process all CDC/USPSTF guideline text files into chunks for RAG.
    Each chunk is tagged with region='North America'.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data", "cdc_guidelines")

    if not os.path.exists(data_dir):
        print("⚠️  CDC guidelines directory not found. Run scrape_cdc.py first.")
        return []

    documents = []
    txt_files = sorted([f for f in os.listdir(data_dir) if f.endswith(".txt")])

    for txt_file in txt_files:
        txt_path = os.path.join(data_dir, txt_file)
        guideline_name = os.path.splitext(txt_file)[0]

        print(f"  Chunking: {guideline_name}...")
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text, chunk_size=1000, overlap=150)

        for i, chunk in enumerate(chunks):
            documents.append({
                "text": chunk,
                "metadata": {
                    "source": "CDC",
                    "region": "North America",
                    "guideline": guideline_name,
                    "chunk_id": f"cdc_{guideline_name}_{i}",
                    "type": "clinical_guideline",
                },
            })

    print(f"  ✅ Processed {len(txt_files)} CDC guidelines into {len(documents)} chunks.")
    return documents


def process_ema_guidelines(data_dir: str = None) -> List[Dict]:
    """
    Process all EMA guideline text files into chunks for RAG.
    Each chunk is tagged with region='Europe'.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data", "ema_guidelines")

    if not os.path.exists(data_dir):
        print("⚠️  EMA guidelines directory not found. Run scrape_ema.py first.")
        return []

    documents = []
    txt_files = sorted([f for f in os.listdir(data_dir) if f.endswith(".txt")])

    for txt_file in txt_files:
        txt_path = os.path.join(data_dir, txt_file)
        guideline_name = os.path.splitext(txt_file)[0]

        print(f"  Chunking: {guideline_name}...")
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text, chunk_size=1000, overlap=150)

        for i, chunk in enumerate(chunks):
            documents.append({
                "text": chunk,
                "metadata": {
                    "source": "EMA",
                    "region": "Europe",
                    "guideline": guideline_name,
                    "chunk_id": f"ema_{guideline_name}_{i}",
                    "type": "clinical_guideline",
                },
            })

    print(f"  ✅ Processed {len(txt_files)} EMA guidelines into {len(documents)} chunks.")
    return documents


def process_icd10_codes(data_dir: str = None) -> List[Dict]:
    """
    Process ICD-10 codes into searchable documents for RAG.
    Each code becomes one document for precise retrieval.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data")

    json_path = os.path.join(data_dir, "icd10_codes.json")
    csv_path = os.path.join(data_dir, "icd10_codes.csv")

    documents = []

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for code_entry in data.get("codes", []):
            text = (
                f"ICD-10 Code: {code_entry['code']}\n"
                f"Description: {code_entry['description']}\n"
                f"Category: {code_entry['category']}"
            )
            documents.append({
                "text": text,
                "metadata": {
                    "source": "ICD-10-CM",
                    "code": code_entry["code"],
                    "category": code_entry["category"],
                    "chunk_id": f"icd10_{code_entry['code']}",
                    "type": "icd10_code",
                },
            })
    elif os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                text = (
                    f"ICD-10 Code: {row['code']}\n"
                    f"Description: {row['description']}\n"
                    f"Category: {row['category']}"
                )
                documents.append({
                    "text": text,
                    "metadata": {
                        "source": "ICD-10-CM",
                        "code": row["code"],
                        "category": row["category"],
                        "chunk_id": f"icd10_{row['code']}",
                        "type": "icd10_code",
                    },
                })
    else:
        print("⚠️  ICD-10 codes not found. Run scrape_icd10.py first.")
        return []

    print(f"  ✅ Processed {len(documents)} ICD-10 codes.")
    return documents


def process_drug_data(data_dir: str = None) -> List[Dict]:
    """
    Process drug reference data into searchable documents for RAG.
    Each drug becomes one document with all its fields.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data")

    json_path = os.path.join(data_dir, "drug_reference.json")

    if not os.path.exists(json_path):
        print("⚠️  Drug reference data not found. Run scrape_drug_data.py first.")
        return []

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    documents = []
    for drug_idx, drug in enumerate(data.get("drugs", [])):
        # Build a comprehensive text block for each drug
        pharm_classes = ", ".join(drug.get("pharm_class", [])) if drug.get("pharm_class") else "N/A"

        text = (
            f"Drug: {drug['generic_name']} (Brand: {drug['brand_name']})\n"
            f"Manufacturer: {drug['manufacturer']}\n"
            f"Route: {drug['route']}\n"
            f"Pharmacological Class: {pharm_classes}\n\n"
            f"Indications: {drug['indications_and_usage']}\n\n"
            f"Contraindications: {drug['contraindications']}\n\n"
            f"Warnings: {drug['warnings']}\n\n"
            f"Drug Interactions: {drug['drug_interactions']}\n\n"
            f"Adverse Reactions: {drug['adverse_reactions']}\n\n"
            f"Dosage: {drug['dosage_and_administration']}"
        )

        safe_name = drug['generic_name'].replace(' ', '_')[:20]
        # If the drug text is very long, chunk it
        if len(text) > 2000:
            chunks = chunk_text(text, chunk_size=1500, overlap=100)
            for i, chunk in enumerate(chunks):
                documents.append({
                    "text": chunk,
                    "metadata": {
                        "source": "OpenFDA",
                        "drug_name": drug["generic_name"],
                        "brand_name": drug["brand_name"],
                        "chunk_id": f"drug_{safe_name}_{drug_idx}_{i}",
                        "type": "drug_reference",
                    },
                })
        else:
            documents.append({
                "text": text,
                "metadata": {
                    "source": "OpenFDA",
                    "drug_name": drug["generic_name"],
                    "brand_name": drug["brand_name"],
                    "chunk_id": f"drug_{safe_name}_{drug_idx}_0",
                    "type": "drug_reference",
                },
            })

    print(f"  ✅ Processed {len(documents)} drug reference chunks.")
    return documents


def process_all_data(data_dir: str = None) -> Dict[str, List[Dict]]:
    """
    Process all data sources and return categorised documents.
    Includes NICE (UK), WHO (Global), CDC (North America),
    EMA (Europe), ICD-10, and drug reference data.
    """
    print("\n📄 Processing NICE Guidelines (UK)...")
    nice_docs = process_nice_guidelines(
        os.path.join(data_dir, "nice_guidelines") if data_dir else None
    )

    print("\n🌍 Processing WHO Guidelines (Global)...")
    who_docs = process_who_guidelines(
        os.path.join(data_dir, "who_guidelines") if data_dir else None
    )

    print("\n🇺🇸 Processing CDC/USPSTF Guidelines (North America)...")
    cdc_docs = process_cdc_guidelines(
        os.path.join(data_dir, "cdc_guidelines") if data_dir else None
    )

    print("\n🇪🇺 Processing EMA Guidelines (Europe)...")
    ema_docs = process_ema_guidelines(
        os.path.join(data_dir, "ema_guidelines") if data_dir else None
    )

    print("\n🏥 Processing ICD-10 Codes...")
    icd10_docs = process_icd10_codes(data_dir)

    print("\n💊 Processing Drug Reference Data...")
    drug_docs = process_drug_data(data_dir)

    guideline_total = len(nice_docs) + len(who_docs) + len(cdc_docs) + len(ema_docs)
    total = guideline_total + len(icd10_docs) + len(drug_docs)
    print(f"\n{'=' * 50}")
    print(f"TOTAL: {total} documents ready for vector store ingestion.")
    print(f"  - NICE Guidelines (UK):    {len(nice_docs)} chunks")
    print(f"  - WHO  Guidelines (Global): {len(who_docs)} chunks")
    print(f"  - CDC  Guidelines (US):     {len(cdc_docs)} chunks")
    print(f"  - EMA  Guidelines (EU):     {len(ema_docs)} chunks")
    print(f"  - ICD-10 Codes:             {len(icd10_docs)} entries")
    print(f"  - Drug Reference:           {len(drug_docs)} chunks")
    print(f"{'=' * 50}")

    return {
        "nice_guidelines": nice_docs,
        "who_guidelines": who_docs,
        "cdc_guidelines": cdc_docs,
        "ema_guidelines": ema_docs,
        "icd10_codes": icd10_docs,
        "drug_reference": drug_docs,
    }


if __name__ == "__main__":
    process_all_data()
