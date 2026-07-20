"""
CDC & USPSTF Guidelines Scraper
================================
Downloads key US clinical guidelines from the CDC (Centers for Disease
Control and Prevention) and USPSTF (US Preventive Services Task Force)
for the MediMate medical copilot RAG pipeline.

Strategy:
  - Fetches CDC fact sheet / condition pages for structured text.
  - Covers high-value primary care conditions from a North American perspective.
  - Saves structured .txt files for RAG chunking.
"""

import os
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime


# --- CDC / USPSTF Guideline Registry ---
# Key US guidelines that complement existing NICE (UK) and WHO (Global) data.

CDC_GUIDELINES = [
    {
        "name": "Hypertension_CDC",
        "url": "https://www.cdc.gov/high-blood-pressure/about/index.html",
        "category": "Cardiovascular",
    },
    {
        "name": "Diabetes_Type2_CDC",
        "url": "https://www.cdc.gov/diabetes/about/about-type-2-diabetes.html",
        "category": "Endocrine",
    },
    {
        "name": "Heart_Disease_CDC",
        "url": "https://www.cdc.gov/heart-disease/about/index.html",
        "category": "Cardiovascular",
    },
    {
        "name": "Stroke_CDC",
        "url": "https://www.cdc.gov/stroke/about/index.html",
        "category": "Cardiovascular",
    },
    {
        "name": "COPD_CDC",
        "url": "https://www.cdc.gov/copd/about/index.html",
        "category": "Respiratory",
    },
    {
        "name": "Asthma_CDC",
        "url": "https://www.cdc.gov/asthma/about/index.html",
        "category": "Respiratory",
    },
    {
        "name": "Chronic_Kidney_Disease_CDC",
        "url": "https://www.cdc.gov/kidney-disease/about/index.html",
        "category": "Renal",
    },
    {
        "name": "Depression_CDC",
        "url": "https://www.cdc.gov/mental-health/about/index.html",
        "category": "Mental Health",
    },
    {
        "name": "Influenza_CDC",
        "url": "https://www.cdc.gov/flu/about/index.html",
        "category": "Infectious Disease",
    },
    {
        "name": "COVID19_CDC",
        "url": "https://www.cdc.gov/covid/about/index.html",
        "category": "Infectious Disease",
    },
    {
        "name": "Pneumonia_CDC",
        "url": "https://www.cdc.gov/pneumonia/about/index.html",
        "category": "Respiratory",
    },
    {
        "name": "Obesity_CDC",
        "url": "https://www.cdc.gov/obesity/about-obesity/index.html",
        "category": "Endocrine",
    },
    {
        "name": "Antibiotic_Prescribing_CDC",
        "url": "https://www.cdc.gov/antibiotic-use/about/index.html",
        "category": "Infectious Disease",
    },
    {
        "name": "Immunization_Schedule_CDC",
        "url": "https://www.cdc.gov/vaccines/schedules/hcp/imz/adult.html",
        "category": "Preventive Care",
    },
    {
        "name": "Cancer_Screening_USPSTF",
        "url": "https://www.uspreventiveservicestaskforce.org/uspstf/topic_search_results?topic_status=P",
        "category": "Preventive Care",
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
}


def _scrape_cdc_page(url):
    """Scrape a CDC or USPSTF page for its main content."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove nav, header, footer, scripts
        for tag in soup.find_all(["nav", "header", "footer", "script", "style", "aside"]):
            tag.decompose()

        # CDC pages typically use <main>, <article>, or specific content divs
        main = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", {"role": "main"})
            or soup.find("div", class_="content")
        )
        if main:
            text = main.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        # Clean up
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        cleaned = "\n".join(lines)

        if len(cleaned) > 200:
            return cleaned
    except Exception as e:
        print(f"    ⚠️  Error scraping {url}: {e}")
    return None


def download_cdc_guidelines(data_dir=None):
    """
    Main entry point: download CDC/USPSTF guidelines.
    Returns metadata dict summarising what was downloaded.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data", "cdc_guidelines")
    os.makedirs(data_dir, exist_ok=True)

    metadata = {
        "source": "CDC (Centers for Disease Control and Prevention) & USPSTF",
        "scraped_at": datetime.now().isoformat(),
        "guidelines": [],
    }

    total = len(CDC_GUIDELINES)
    for idx, guideline in enumerate(CDC_GUIDELINES, 1):
        name = guideline["name"]
        url = guideline["url"]
        category = guideline["category"]

        print(f"\n[{idx}/{total}] Processing {name}...")
        entry = {
            "name": name,
            "url": url,
            "category": category,
            "text_extracted": False,
        }

        text_content = _scrape_cdc_page(url)
        if text_content:
            txt_path = os.path.join(data_dir, f"{name}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"CDC/USPSTF Guideline: {name}\n")
                f.write(f"Source: {url}\n")
                f.write(f"Category: {category}\n")
                f.write(f"Region: North America\n")
                f.write(f"Scraped: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n\n")
                f.write(text_content)
            entry["text_extracted"] = True
            print(f"  ✅ Text extracted ({len(text_content)} chars)")
        else:
            print(f"  ❌ Could not extract text for {name}")

        metadata["guidelines"].append(entry)
        time.sleep(2)  # Be polite

    # Save metadata
    meta_path = os.path.join(data_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"\n📋 Metadata saved to {meta_path}")

    texts = sum(1 for g in metadata["guidelines"] if g["text_extracted"])
    print(f"\n{'=' * 50}")
    print(f"SUMMARY: {texts}/{total} CDC/USPSTF guidelines extracted.")
    print(f"{'=' * 50}")

    return metadata


if __name__ == "__main__":
    download_cdc_guidelines()
