"""
Job Scraper Microservice (Multi-Source Support)
==============================================
Menarik data lowongan kerja dari berbagai portal kerja target,
menyesuaikan selector HTML tiap website secara otomatis, dan
mengirimkan hasilnya ke N8N_WEBHOOK_URL via HTTP POST.

Konfigurasi via environment variables (file .env):
  - N8N_WEBHOOK_URL   : URL Webhook n8n yang menerima payload JSON
"""

import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ─── Logging Setup ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── Data Model ───────────────────────────────────────────────────────────────


@dataclass
class JobListing:
    """Merepresentasikan satu entri lowongan kerja hasil scraping."""

    job_title: str
    company_name: str
    job_description: str
    job_url: str
    source_name: str  # Nama website sumber (misal: Glints, Jobstreet)
    source_url: str

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Konfigurasi Sumber (Source Configurations) ────────────────────────────────

# Di sini kamu bisa mendaftarkan berbagai portal lowongan kerja target.
# Kamu hanya perlu menyesuaikan selector CSS berdasarkan struktur HTML website target.
SOURCES_CONFIG = [
    {
        "name": "Portal Generik A",
        "url": "https://www.example-job-portal.com/jobs",
        "selectors": {
            "card": "div.job-card",
            "title": "h2.job-title",
            "company": "span.company-name",
            "desc": "p.job-description",
            "link": "a.job-link"
        }
    },
    {
        "name": "Portal Generik B",
        "url": "https://www.another-job-site.org/vacancies",
        "selectors": {
            "card": "article.vacancy-item",
            "title": "h3.vacancy-title",
            "company": "div.employer-name",
            "desc": "div.vacancy-summary",
            "link": "a.apply-link"
        }
    }
    # Contoh untuk real-world portal tinggal ditambahkan di sini:
    # {
    #     "name": "Glints",
    #     "url": "https://glints.com/id/opportunities/jobs?keyword=backend+developer",
    #     "selectors": {
    #         "card": "div[class*='CompactOpportunityCardsc__CardWrapper']",
    #         "title": "h3[class*='CompactOpportunityCardsc__JobTitle']",
    #         "company": "a[class*='CompactOpportunityCardsc__CompanyLink']",
    #         "desc": "div[class*='CompactOpportunityCardsc__OpportunityInfo']",
    #         "link": "a[class*='CompactOpportunityCardsc__CardAnchorWrapper']"
    #     }
    # }
]


# ─── HTTP Helpers ─────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}


def fetch_html(url: str, timeout: int = 15) -> Optional[str]:
    """Mengambil konten HTML dari URL target."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        logger.info(f"Berhasil fetch: {url} [{response.status_code}]")
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Gagal mengambil URL {url}: {e}")
    return None


# ─── Parser Engine ────────────────────────────────────────────────────────────


def parse_source(html: str, source_config: dict) -> list[JobListing]:
    """Mem-parsing HTML berdasarkan konfigurasi selector spesifik dari portal target."""
    soup = BeautifulSoup(html, "lxml")
    listings: list[JobListing] = []
    
    cfg = source_config
    selectors = cfg["selectors"]

    # Cari semua job card di halaman
    job_cards = soup.select(selectors["card"])
    logger.info(f"[{cfg['name']}] Ditemukan {len(job_cards)} elemen lowongan")

    for idx, card in enumerate(job_cards, start=1):
        try:
            # Ekstrak data menggunakan selector spesifik sumber ini
            title_el = card.select_one(selectors["title"])
            company_el = card.select_one(selectors["company"])
            desc_el = card.select_one(selectors["desc"])
            link_el = card.select_one(selectors["link"])

            job_title = title_el.get_text(strip=True) if title_el else ""
            company_name = company_el.get_text(strip=True) if company_el else ""
            job_description = desc_el.get_text(strip=True) if desc_el else ""
            
            raw_href = link_el.get("href", "") if link_el else ""
            job_url = urljoin(cfg["url"], raw_href) if raw_href else ""

            # Validasi minimal
            if not job_title or not company_name:
                continue

            listing = JobListing(
                job_title=job_title,
                company_name=company_name,
                job_description=job_description or "Deskripsi tidak tersedia",
                job_url=job_url,
                source_name=cfg["name"],
                source_url=cfg["url"]
            )
            listings.append(listing)
            logger.debug(f"Ekstrak sukses: {job_title} @ {company_name}")

        except Exception as e:
            logger.warning(f"Gagal mengekstrak item ke-{idx} di {cfg['name']}: {e}")
            continue

    return listings


# ─── Webhook Delivery ─────────────────────────────────────────────────────────


def send_to_webhook(webhook_url: str, listing: JobListing) -> bool:
    """Mengirim satu job listing ke n8n Webhook via HTTP POST."""
    payload = listing.to_dict()
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        response.raise_for_status()
        logger.info(f"✓ Terkirim ke webhook: '{listing.job_title}' dari {listing.source_name}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Gagal kirim webhook untuk '{listing.job_title}': {e}")
    return False


# ─── Main Controller ──────────────────────────────────────────────────────────


def main() -> None:
    load_dotenv()
    webhook_url = os.getenv("N8N_WEBHOOK_URL", "").strip()

    if not webhook_url:
        logger.error("N8N_WEBHOOK_URL tidak ditemukan di .env")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("  Starting Job Scraper Engine — Multi-Source Mode")
    logger.info("=" * 60)

    all_listings: list[JobListing] = []

    # Loop mengunjungi setiap sumber lowongan kerja
    for source in SOURCES_CONFIG:
        logger.info(f"\nProcessing Source: {source['name']}")
        logger.info(f"Target URL       : {source['url']}")

        html = fetch_html(source["url"])
        if not html:
            logger.warning(f"Skip sumber {source['name']} karena gagal mengambil HTML.")
            continue

        listings = parse_source(html, source)
        logger.info(f"Sukses mengekstrak {len(listings)} lowongan dari {source['name']}")
        all_listings.extend(listings)

    if not all_listings:
        logger.warning("\nTidak ada lowongan kerja yang ditemukan dari seluruh sumber.")
        sys.exit(0)

    # Kirim semua lowongan yang terkumpul ke n8n
    logger.info(f"\nMengirim total {len(all_listings)} lowongan ke n8n webhook...")
    success_count = 0
    for item in all_listings:
        if send_to_webhook(webhook_url, item):
            success_count += 1

    logger.info("\n" + "=" * 60)
    logger.info("  Execution Summary")
    logger.info("=" * 60)
    logger.info(f"  Total Di-scrape   : {len(all_listings)}")
    logger.info(f"  Sukses Terkirim   : {success_count}")
    logger.info(f"  Gagal Terkirim    : {len(all_listings) - success_count}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
