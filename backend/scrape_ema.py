"""
EMA Guidelines Scraper
=======================
Downloads European Medicines Agency clinical guidelines and key
drug approval summaries for the MediMate medical copilot RAG pipeline.

Strategy:
  - Fetches EMA "medicines" overview pages and key therapeutic guidelines.
  - EMA publishes EPARs (European Public Assessment Reports) in English.
  - Covers EU-wide clinical guidance that applies to all EU/EEA member states
    including Germany, Netherlands, Sweden, Norway, etc.
  - Saves structured .txt files for RAG chunking.
"""

import os
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime


# --- EMA Guideline Registry ---
# Key EMA guideline pages and therapeutic area overviews.
# These are available in English and provide EU-wide clinical guidance.

EMA_GUIDELINES = [
    {
        "name": "Diabetes_EMA",
        "url": "https://www.ema.europa.eu/en/human-regulatory-overview/research-development/scientific-guidelines/clinical-efficacy-safety-guidelines/diabetes-endocrinology",
        "category": "Endocrine",
    },
    {
        "name": "Cardiovascular_EMA",
        "url": "https://www.ema.europa.eu/en/human-regulatory-overview/research-development/scientific-guidelines/clinical-efficacy-safety-guidelines/cardiovascular-diseases",
        "category": "Cardiovascular",
    },
    {
        "name": "Respiratory_EMA",
        "url": "https://www.ema.europa.eu/en/human-regulatory-overview/research-development/scientific-guidelines/clinical-efficacy-safety-guidelines/respiratory-diseases",
        "category": "Respiratory",
    },
    {
        "name": "Oncology_EMA",
        "url": "https://www.ema.europa.eu/en/human-regulatory-overview/research-development/scientific-guidelines/clinical-efficacy-safety-guidelines/anticancer-agents-antineoplastic-immunomodulating-agents",
        "category": "Oncology",
    },
    {
        "name": "Neurology_EMA",
        "url": "https://www.ema.europa.eu/en/human-regulatory-overview/research-development/scientific-guidelines/clinical-efficacy-safety-guidelines/nervous-system-diseases",
        "category": "Neurology",
    },
    {
        "name": "Psychiatry_EMA",
        "url": "https://www.ema.europa.eu/en/human-regulatory-overview/research-development/scientific-guidelines/clinical-efficacy-safety-guidelines/psychiatric-disorders",
        "category": "Mental Health",
    },
    {
        "name": "Infectious_Disease_EMA",
        "url": "https://www.ema.europa.eu/en/human-regulatory-overview/research-development/scientific-guidelines/clinical-efficacy-safety-guidelines/anti-infective-agents",
        "category": "Infectious Disease",
    },
    {
        "name": "Rheumatology_EMA",
        "url": "https://www.ema.europa.eu/en/human-regulatory-overview/research-development/scientific-guidelines/clinical-efficacy-safety-guidelines/musculoskeletal-diseases",
        "category": "Rheumatology",
    },
    {
        "name": "Gastroenterology_EMA",
        "url": "https://www.ema.europa.eu/en/human-regulatory-overview/research-development/scientific-guidelines/clinical-efficacy-safety-guidelines/gastrointestinal-diseases",
        "category": "Gastroenterology",
    },
    {
        "name": "Dermatology_EMA",
        "url": "https://www.ema.europa.eu/en/human-regulatory-overview/research-development/scientific-guidelines/clinical-efficacy-safety-guidelines/dermatology-allergology",
        "category": "Dermatology",
    },
    {
        "name": "Vaccines_EMA",
        "url": "https://www.ema.europa.eu/en/human-regulatory-overview/research-development/scientific-guidelines/clinical-efficacy-safety-guidelines/vaccines-antigens",
        "category": "Preventive Care",
    },
    {
        "name": "Pharmacovigilance_EMA",
        "url": "https://www.ema.europa.eu/en/human-regulatory-overview/post-authorisation/pharmacovigilance-post-authorisation",
        "category": "Safety",
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
}


def _scrape_ema_page(url):
    """Scrape an EMA guideline page for its main content."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove nav, header, footer, scripts
        for tag in soup.find_all(["nav", "header", "footer", "script", "style", "aside"]):
            tag.decompose()

        # EMA pages typically use <main>, <article>, or content wrappers
        main = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", class_="field--name-body")
            or soup.find("div", {"role": "main"})
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


def download_ema_guidelines(data_dir=None):
    """
    Main entry point: download EMA guidelines.
    Returns metadata dict summarising what was downloaded.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data", "ema_guidelines")
    os.makedirs(data_dir, exist_ok=True)

    metadata = {
        "source": "EMA (European Medicines Agency)",
        "scraped_at": datetime.now().isoformat(),
        "guidelines": [],
    }

    total = len(EMA_GUIDELINES)
    for idx, guideline in enumerate(EMA_GUIDELINES, 1):
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

        text_content = _scrape_ema_page(url)
        if text_content:
            txt_path = os.path.join(data_dir, f"{name}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"EMA Guideline: {name}\n")
                f.write(f"Source: {url}\n")
                f.write(f"Category: {category}\n")
                f.write(f"Region: Europe\n")
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
    print(f"SUMMARY: {texts}/{total} EMA guidelines extracted.")
    print(f"{'=' * 50}")

    return metadata


if __name__ == "__main__":
    download_ema_guidelines()
