"""
WHO Guidelines Scraper
======================
Downloads World Health Organization clinical guidelines for global
coverage in the MediMate medical copilot RAG pipeline.

Strategy:
  - Fetches key WHO clinical recommendations from their public pages.
  - Covers conditions common across APAC and global contexts.
  - Saves structured .txt files for RAG chunking.
"""

import os
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime


# --- WHO Guideline Registry ---
# Key WHO guidelines covering global primary care conditions.
# These complement (not replace) the existing NICE guidelines.

WHO_GUIDELINES = [
    {
        "name": "Hypertension_WHO",
        "url": "https://www.who.int/news-room/fact-sheets/detail/hypertension",
        "category": "Cardiovascular",
    },
    {
        "name": "Diabetes_WHO",
        "url": "https://www.who.int/news-room/fact-sheets/detail/diabetes",
        "category": "Endocrine",
    },
    {
        "name": "Asthma_WHO",
        "url": "https://www.who.int/news-room/fact-sheets/detail/asthma",
        "category": "Respiratory",
    },
    {
        "name": "COPD_WHO",
        "url": "https://www.who.int/news-room/fact-sheets/detail/chronic-obstructive-pulmonary-disease-(copd)",
        "category": "Respiratory",
    },
    {
        "name": "Depression_WHO",
        "url": "https://www.who.int/news-room/fact-sheets/detail/depression",
        "category": "Mental Health",
    },
    {
        "name": "Cancer_WHO",
        "url": "https://www.who.int/news-room/fact-sheets/detail/cancer",
        "category": "Oncology",
    },
    {
        "name": "Cardiovascular_Diseases_WHO",
        "url": "https://www.who.int/news-room/fact-sheets/detail/cardiovascular-diseases-(cvds)",
        "category": "Cardiovascular",
    },
    {
        "name": "Obesity_WHO",
        "url": "https://www.who.int/news-room/fact-sheets/detail/obesity-and-overweight",
        "category": "Endocrine",
    },
    {
        "name": "Epilepsy_WHO",
        "url": "https://www.who.int/news-room/fact-sheets/detail/epilepsy",
        "category": "Neurology",
    },
    {
        "name": "Tuberculosis_WHO",
        "url": "https://www.who.int/news-room/fact-sheets/detail/tuberculosis",
        "category": "Infectious Disease",
    },
    {
        "name": "Malaria_WHO",
        "url": "https://www.who.int/news-room/fact-sheets/detail/malaria",
        "category": "Infectious Disease",
    },
    {
        "name": "HIV_AIDS_WHO",
        "url": "https://www.who.int/news-room/fact-sheets/detail/hiv-aids",
        "category": "Infectious Disease",
    },
    {
        "name": "Hepatitis_B_WHO",
        "url": "https://www.who.int/news-room/fact-sheets/detail/hepatitis-b",
        "category": "Infectious Disease",
    },
    {
        "name": "Dementia_WHO",
        "url": "https://www.who.int/news-room/fact-sheets/detail/dementia",
        "category": "Neurology",
    },
    {
        "name": "Maternal_Health_WHO",
        "url": "https://www.who.int/news-room/fact-sheets/detail/maternal-mortality",
        "category": "Obstetrics",
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
}


def _scrape_who_page(url):
    """Scrape a WHO fact sheet page for its main content."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove nav, header, footer, scripts
        for tag in soup.find_all(["nav", "header", "footer", "script", "style", "aside"]):
            tag.decompose()

        # WHO fact sheets usually have content in <article> or main
        main = soup.find("article") or soup.find("main") or soup.find("div", class_="sf-detail-body-wrapper")
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


def download_who_guidelines(data_dir=None):
    """
    Main entry point: download WHO guidelines.
    Returns metadata dict summarising what was downloaded.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data", "who_guidelines")
    os.makedirs(data_dir, exist_ok=True)

    metadata = {
        "source": "WHO (World Health Organization)",
        "scraped_at": datetime.now().isoformat(),
        "guidelines": [],
    }

    total = len(WHO_GUIDELINES)
    for idx, guideline in enumerate(WHO_GUIDELINES, 1):
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

        text_content = _scrape_who_page(url)
        if text_content:
            txt_path = os.path.join(data_dir, f"{name}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"WHO Guideline: {name}\n")
                f.write(f"Source: {url}\n")
                f.write(f"Category: {category}\n")
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
    print(f"SUMMARY: {texts}/{total} WHO guidelines extracted.")
    print(f"{'=' * 50}")

    return metadata


if __name__ == "__main__":
    download_who_guidelines()
