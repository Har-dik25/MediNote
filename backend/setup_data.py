"""
MediMate — One-Command Data Setup
==================================
Run this script once to download all data and build the vector store.

Usage:
    python setup_data.py
    python setup_data.py --dry-run     # parse-only, no embedding

This will:
  1. Generate ICD-10-CM codes (instant, offline)
  2. Fetch drug reference data from OpenFDA (~5 min)
  3. Scrape NICE clinical guidelines — UK (~2-3 min)
  4. Scrape WHO clinical guidelines — Global (~1-2 min)
  5. Scrape CDC/USPSTF guidelines — North America (~1-2 min)
  6. Scrape EMA guidelines — Europe (~1-2 min)
  7. Process and chunk all data
  8. Build the ChromaDB vector store
"""

import os
import sys
import time

# Ensure we can import from the same directory
sys.path.insert(0, os.path.dirname(__file__))

DRY_RUN = "--dry-run" in sys.argv


def main():
    start_time = time.time()
    data_dir = os.path.join(os.path.dirname(__file__), "data")

    print("=" * 60)
    print("  MediMate — Data Setup (Global Knowledge Base)")
    print("=" * 60)
    if DRY_RUN:
        print("  ⚡ DRY RUN — scrapers will run but vector store will NOT be built.")
    print()

    # Step 1: ICD-10 Codes (instant, no network needed)
    print("━" * 60)
    print("STEP 1/7: Generating ICD-10-CM codes...")
    print("━" * 60)
    try:
        from scrape_icd10 import download_icd10_codes
        download_icd10_codes(data_dir)
    except Exception as e:
        print(f"⚠️  ICD-10 generation failed: {e}")
    print()

    # Step 2: Drug Reference Data (needs network, ~5 min)
    print("━" * 60)
    print("STEP 2/7: Fetching drug reference data from OpenFDA...")
    print("━" * 60)
    try:
        from scrape_drug_data import download_drug_data
        download_drug_data(data_dir)
    except Exception as e:
        print(f"⚠️  Drug data fetch failed: {e}")
    print()

    # Step 3: NICE Guidelines — UK (needs network, ~2-3 min)
    print("━" * 60)
    print("STEP 3/7: Scraping NICE clinical guidelines (UK)...")
    print("━" * 60)
    try:
        from scrape_nice import download_nice_guidelines
        nice_dir = os.path.join(data_dir, "nice_guidelines")
        download_nice_guidelines(nice_dir)
    except Exception as e:
        print(f"⚠️  NICE scraping failed: {e}")
    print()

    # Step 4: WHO Guidelines — Global (needs network, ~1-2 min)
    print("━" * 60)
    print("STEP 4/7: Scraping WHO clinical guidelines (Global)...")
    print("━" * 60)
    try:
        from scrape_who import download_who_guidelines
        who_dir = os.path.join(data_dir, "who_guidelines")
        download_who_guidelines(who_dir)
    except Exception as e:
        print(f"⚠️  WHO scraping failed: {e}")
    print()

    # Step 5: CDC/USPSTF Guidelines — North America (needs network, ~1-2 min)
    print("━" * 60)
    print("STEP 5/7: Scraping CDC/USPSTF guidelines (North America)...")
    print("━" * 60)
    try:
        from scrape_cdc import download_cdc_guidelines
        cdc_dir = os.path.join(data_dir, "cdc_guidelines")
        download_cdc_guidelines(cdc_dir)
    except Exception as e:
        print(f"⚠️  CDC scraping failed: {e}")
    print()

    # Step 6: EMA Guidelines — Europe (needs network, ~1-2 min)
    print("━" * 60)
    print("STEP 6/7: Scraping EMA guidelines (Europe)...")
    print("━" * 60)
    try:
        from scrape_ema import download_ema_guidelines
        ema_dir = os.path.join(data_dir, "ema_guidelines")
        download_ema_guidelines(ema_dir)
    except Exception as e:
        print(f"⚠️  EMA scraping failed: {e}")
    print()

    # Step 7: Build Vector Store
    print("━" * 60)
    print("STEP 7/7: Building ChromaDB vector store...")
    print("━" * 60)
    if DRY_RUN:
        print("  ⚡ Skipped (dry run mode).")
    else:
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
    print("Knowledge base regions indexed:")
    print("  🇬🇧  UK        → NICE guidelines")
    print("  🌍  Global    → WHO guidelines")
    print("  🇺🇸  N. America → CDC / USPSTF guidelines")
    print("  🇪🇺  Europe    → EMA guidelines")
    print()
    print("Next steps:")
    print("  1. Run: uvicorn main:app --reload")
    print("  2. Set your preferred region in Settings → Clinical guidelines.")
    print("  3. SOAP notes will now reference region-appropriate guidelines.")
    print()


if __name__ == "__main__":
    main()
