"""
MediMate — One-Command Data Setup
==================================
Run this script once to download all data and build the vector store.

Usage:
    python setup_data.py

This will:
  1. Generate ICD-10-CM codes (instant, offline)
  2. Fetch drug reference data from OpenFDA (~5 min)
  3. Scrape NICE clinical guidelines (~2-3 min)
  4. Process and chunk all data
  5. Build the ChromaDB vector store
"""

import os
import sys
import time

# Ensure we can import from the same directory
sys.path.insert(0, os.path.dirname(__file__))


def main():
    start_time = time.time()
    data_dir = os.path.join(os.path.dirname(__file__), "data")

    print("=" * 60)
    print("  MediMate — Data Setup")
    print("=" * 60)
    print()

    # Step 1: ICD-10 Codes (instant, no network needed)
    print("━" * 60)
    print("STEP 1/4: Generating ICD-10-CM codes...")
    print("━" * 60)
    try:
        from scrape_icd10 import download_icd10_codes
        download_icd10_codes(data_dir)
    except Exception as e:
        print(f"⚠️  ICD-10 generation failed: {e}")
    print()

    # Step 2: Drug Reference Data (needs network, ~5 min)
    print("━" * 60)
    print("STEP 2/4: Fetching drug reference data from OpenFDA...")
    print("━" * 60)
    try:
        from scrape_drug_data import download_drug_data
        download_drug_data(data_dir)
    except Exception as e:
        print(f"⚠️  Drug data fetch failed: {e}")
    print()

    # Step 3: NICE Guidelines (needs network, ~2-3 min)
    print("━" * 60)
    print("STEP 3/4: Scraping NICE clinical guidelines...")
    print("━" * 60)
    try:
        from scrape_nice import download_nice_guidelines
        nice_dir = os.path.join(data_dir, "nice_guidelines")
        download_nice_guidelines(nice_dir)
    except Exception as e:
        print(f"⚠️  NICE scraping failed: {e}")
    print()

    # Step 4: Build Vector Store
    print("━" * 60)
    print("STEP 4/4: Building ChromaDB vector store...")
    print("━" * 60)
    try:
        from rag_engine import build_vector_store
        build_vector_store(data_dir, force_rebuild=True)
    except ImportError as e:
        print(f"⚠️  Missing dependencies: {e}")
        print("   Install with: pip install chromadb sentence-transformers")
    except Exception as e:
        print(f"⚠️  Vector store build failed: {e}")

    elapsed = time.time() - start_time
    print()
    print("=" * 60)
    print(f"  ✅ SETUP COMPLETE — {elapsed:.1f}s elapsed")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Run: streamlit run app.py")
    print("  2. The knowledge base sidebar will show indexed document counts.")
    print("  3. SOAP notes will now reference NICE guidelines automatically.")
    print()


if __name__ == "__main__":
    main()
