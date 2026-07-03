"""
NICE Guidelines Scraper
=======================
Downloads NICE clinical guidelines for the MediMate medical copilot.
Supports 20 high-value primary care conditions.

Strategy:
  1. Try to find and download the PDF from the guideline page.
  2. Fall back to scraping the HTML recommendations page for structured text.
  3. Save both raw files and extracted .txt for RAG consumption.
"""

import os
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime


# --- Guideline Registry ---
# Each entry: { "name": ..., "code": ..., "url": ... }
# Covers the most common primary care conditions a medical copilot would encounter.

NICE_GUIDELINES = [
    {"name": "Asthma",                    "code": "ng245", "url": "https://www.nice.org.uk/guidance/ng245"},
    {"name": "Hypertension",              "code": "ng136", "url": "https://www.nice.org.uk/guidance/ng136"},
    {"name": "Diabetes_Type2",            "code": "ng28",  "url": "https://www.nice.org.uk/guidance/ng28"},
    {"name": "Depression_Adults",         "code": "ng222", "url": "https://www.nice.org.uk/guidance/ng222"},
    {"name": "Generalised_Anxiety",       "code": "cg113", "url": "https://www.nice.org.uk/guidance/cg113"},
    {"name": "COPD",                      "code": "ng115", "url": "https://www.nice.org.uk/guidance/ng115"},
    {"name": "Heart_Failure",             "code": "ng106", "url": "https://www.nice.org.uk/guidance/ng106"},
    {"name": "Atrial_Fibrillation",       "code": "ng196", "url": "https://www.nice.org.uk/guidance/ng196"},
    {"name": "Chest_Pain",               "code": "cg95",  "url": "https://www.nice.org.uk/guidance/cg95"},
    {"name": "Urinary_Tract_Infections",  "code": "ng109", "url": "https://www.nice.org.uk/guidance/ng109"},
    {"name": "Diabetes_Type1_Adults",     "code": "ng17",  "url": "https://www.nice.org.uk/guidance/ng17"},
    {"name": "Chronic_Kidney_Disease",    "code": "ng203", "url": "https://www.nice.org.uk/guidance/ng203"},
    {"name": "Headaches",                 "code": "cg150", "url": "https://www.nice.org.uk/guidance/cg150"},
    {"name": "Low_Back_Pain",             "code": "ng59",  "url": "https://www.nice.org.uk/guidance/ng59"},
    {"name": "Osteoarthritis",            "code": "cg177", "url": "https://www.nice.org.uk/guidance/cg177"},
    {"name": "Epilepsy",                  "code": "ng217", "url": "https://www.nice.org.uk/guidance/ng217"},
    {"name": "Pneumonia_Community",       "code": "ng191", "url": "https://www.nice.org.uk/guidance/ng191"},
    {"name": "Stroke_TIA",               "code": "ng128", "url": "https://www.nice.org.uk/guidance/ng128"},
    {"name": "Venous_Thromboembolism",    "code": "ng158", "url": "https://www.nice.org.uk/guidance/ng158"},
    {"name": "Sepsis",                    "code": "ng51",  "url": "https://www.nice.org.uk/guidance/ng51"},
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
}


def _find_pdf_link(soup, base_url):
    """Look for the guideline PDF download link on a NICE page."""
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if "/resources/" in href and "-pdf-" in href:
            return urljoin(base_url, a["href"])
    return None


def _download_pdf(pdf_url, file_path):
    """Stream-download a PDF to disk."""
    resp = requests.get(pdf_url, headers=HEADERS, stream=True, timeout=60)
    resp.raise_for_status()
    with open(file_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)


def _scrape_recommendations_html(guideline_url):
    """
    Fall back to scraping the guideline's /chapter/Recommendations page
    for structured text. NICE recommendations pages are well-structured
    HTML which is actually better for RAG than raw PDF text.
    """
    # NICE recommendation pages follow patterns like:
    #   /guidance/ng245/chapter/Recommendations
    #   /guidance/cg113/chapter/1-guidance  (older CG guidelines)
    possible_paths = [
        f"{guideline_url}/chapter/Recommendations",
        f"{guideline_url}/chapter/recommendations",
        f"{guideline_url}/chapter/1-Guidance",
        f"{guideline_url}/chapter/1-guidance",
    ]

    for page_url in possible_paths:
        try:
            resp = requests.get(page_url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")

                # Remove navigation, headers, footers
                for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
                    tag.decompose()

                # Try to find the main content area
                main = soup.find("main") or soup.find("div", class_="chapter-body") or soup.find("article")
                if main:
                    text = main.get_text(separator="\n", strip=True)
                else:
                    text = soup.get_text(separator="\n", strip=True)

                # Basic cleanup: collapse multiple blank lines
                lines = [line.strip() for line in text.split("\n")]
                lines = [line for line in lines if line]
                cleaned = "\n".join(lines)

                if len(cleaned) > 200:  # Only accept if meaningful content
                    return cleaned, page_url
        except Exception:
            continue

    return None, None


def _extract_text_from_main_page(guideline_url):
    """
    Last resort: scrape the main guideline overview page for any useful text.
    """
    try:
        resp = requests.get(guideline_url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
            tag.decompose()

        main = soup.find("main") or soup.find("article") or soup.body
        if main:
            text = main.get_text(separator="\n", strip=True)
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            return "\n".join(lines)
    except Exception:
        pass
    return None


def download_nice_guidelines(data_dir=None):
    """
    Main entry point: download all NICE guidelines.
    Returns a metadata dict summarising what was downloaded.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data", "nice_guidelines")
    os.makedirs(data_dir, exist_ok=True)

    metadata = {
        "source": "NICE (National Institute for Health and Care Excellence)",
        "scraped_at": datetime.now().isoformat(),
        "guidelines": [],
    }

    total = len(NICE_GUIDELINES)
    for idx, guideline in enumerate(NICE_GUIDELINES, 1):
        name = guideline["name"]
        code = guideline["code"]
        url = guideline["url"]

        print(f"\n[{idx}/{total}] Processing {name} ({code})...")
        entry = {
            "name": name,
            "code": code,
            "url": url,
            "pdf_downloaded": False,
            "text_extracted": False,
            "text_source": None,
        }

        try:
            # Step 1: Fetch the main guideline page
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Step 2: Try PDF download
            pdf_link = _find_pdf_link(soup, url)
            if pdf_link:
                pdf_path = os.path.join(data_dir, f"{name}.pdf")
                print(f"  📄 Downloading PDF from {pdf_link}...")
                try:
                    _download_pdf(pdf_link, pdf_path)
                    entry["pdf_downloaded"] = True
                    print(f"  ✅ PDF saved: {name}.pdf")
                except Exception as e:
                    print(f"  ⚠️  PDF download failed: {e}")
            else:
                print(f"  ℹ️  No PDF link found on main page.")

            # Step 3: Scrape recommendations HTML for text (always do this for RAG)
            text_content, source_url = _scrape_recommendations_html(url)
            if text_content:
                txt_path = os.path.join(data_dir, f"{name}.txt")
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(f"NICE Guideline: {name} ({code.upper()})\n")
                    f.write(f"Source: {source_url}\n")
                    f.write(f"Scraped: {datetime.now().isoformat()}\n")
                    f.write("=" * 80 + "\n\n")
                    f.write(text_content)
                entry["text_extracted"] = True
                entry["text_source"] = "recommendations_page"
                print(f"  ✅ Text extracted from recommendations page.")
            else:
                # Last resort: extract from main page
                text_content = _extract_text_from_main_page(url)
                if text_content:
                    txt_path = os.path.join(data_dir, f"{name}.txt")
                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write(f"NICE Guideline: {name} ({code.upper()})\n")
                        f.write(f"Source: {url}\n")
                        f.write(f"Scraped: {datetime.now().isoformat()}\n")
                        f.write("=" * 80 + "\n\n")
                        f.write(text_content)
                    entry["text_extracted"] = True
                    entry["text_source"] = "main_page"
                    print(f"  ✅ Text extracted from main page (fallback).")
                else:
                    print(f"  ❌ Could not extract text for {name}.")

        except Exception as e:
            print(f"  ❌ Error processing {name}: {e}")

        metadata["guidelines"].append(entry)

        # Be polite to the NICE servers
        time.sleep(2)

    # Save metadata
    meta_path = os.path.join(data_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"\n📋 Metadata saved to {meta_path}")

    # Summary
    pdfs = sum(1 for g in metadata["guidelines"] if g["pdf_downloaded"])
    texts = sum(1 for g in metadata["guidelines"] if g["text_extracted"])
    print(f"\n{'=' * 50}")
    print(f"SUMMARY: {pdfs}/{total} PDFs downloaded, {texts}/{total} text files extracted.")
    print(f"{'=' * 50}")

    return metadata


if __name__ == "__main__":
    download_nice_guidelines()
