"""
Job Scraper Microservice — Multi-Source (Hybrid Mode)
======================================================
Menarik lowongan kerja dari portal Indonesia. Kalibrr diambil via API
internal (stabil), sedangkan Glints & JobStreet via headless browser
(Playwright) karena API-nya memblokir request langsung dari server (403).

Sources:
  - Kalibrr (via internal search API)
  - Glints Indonesia (via headless browser — intercept GraphQL)
  - JobStreet Indonesia (via headless browser — intercept chalice-search)
  - LinkedIn (via guest jobs API — tanpa login/browser)

Konfigurasi via environment variables:
  - N8N_WEBHOOK_URL   : URL Webhook n8n yang menerima payload JSON
  - SEARCH_KEYWORD    : Kata kunci pencarian (default: "Customer Service")
  - MAX_JOBS_PER_SOURCE : Maks lowongan per sumber (default: 10)
"""

import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from browser_scraper import scrape_glints_browser, scrape_jobstreet_browser

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
    source_name: str
    source_url: str
    location: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Location Prioritization ────────────────────────────────────────────────

# Area yang diprioritaskan (urutan = prioritas tertinggi ke terendah).
PREFERRED_LOCATIONS = [
    "Depok",
    "Jakarta Selatan",
    "Jakarta Pusat",
    "Jakarta Timur",
]


# Beberapa sumber (mis. Kalibrr) memakai nama Inggris untuk area Jakarta.
_LOCATION_ALIASES = {
    "south jakarta": "Jakarta Selatan",
    "central jakarta": "Jakarta Pusat",
    "east jakarta": "Jakarta Timur",
    "west jakarta": "Jakarta Barat",
    "north jakarta": "Jakarta Utara",
    "jakarta": "Jakarta",
}


def _normalize_location(location: str) -> str:
    """Menyeragamkan nama lokasi (Inggris → Indonesia) untuk konsistensi."""
    if not location:
        return ""
    key = location.strip().lower()
    return _LOCATION_ALIASES.get(key, location.strip())


def location_priority(location: str) -> int:
    """
    Mengembalikan skor prioritas lokasi (semakin kecil semakin diutamakan).
      0..n-1 : cocok dengan salah satu PREFERRED_LOCATIONS (sesuai urutannya)
      99     : lokasi lain / kosong
    """
    if not location:
        return 99
    loc = location.lower()
    for idx, area in enumerate(PREFERRED_LOCATIONS):
        if area.lower() in loc:
            return idx
    return 99


# ─── HTTP Client ──────────────────────────────────────────────────────────────

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
}


def api_get(url: str, params: dict = None, headers: dict = None, timeout: int = 15) -> Optional[dict]:
    """Melakukan GET request ke API dan mengembalikan JSON response."""
    merged_headers = {**BASE_HEADERS, **(headers or {})}
    try:
        response = requests.get(url, params=params, headers=merged_headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.JSONDecodeError:
        logger.error(f"Respons bukan JSON dari {url}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error untuk {url}: {e}")
    return None


# ─── Source Scrapers ──────────────────────────────────────────────────────────


def scrape_kalibrr(keyword: str, max_jobs: int = 10) -> list[JobListing]:
    """
    Scrape Kalibrr via internal search API.
    Kalibrr menyediakan endpoint JSON yang bisa diakses langsung.
    """
    logger.info("  [Kalibrr] Memulai pencarian...")
    listings = []

    url = "https://www.kalibrr.com/kjs/job_board/search"
    params = {
        "limit": max_jobs,
        "offset": 0,
        "text": keyword,
        "country_code": "ID",
    }
    headers = {
        "Referer": "https://www.kalibrr.com/job-board/te/customer-service",
    }

    data = api_get(url, params=params, headers=headers)
    if not data:
        logger.warning("  [Kalibrr] Gagal mendapatkan data dari API.")
        return listings

    jobs = data.get("jobs", [])
    logger.info(f"  [Kalibrr] Ditemukan {len(jobs)} lowongan.")

    for job in jobs[:max_jobs]:
        try:
            title = job.get("name", "").strip()
            company = job.get("company", {}).get("name", "").strip()
            description = job.get("description", "") or job.get("requirements", "") or "Lihat detail di Kalibrr."
            job_id = job.get("slug") or job.get("id", "")
            job_url = f"https://www.kalibrr.com/c/{job_id}/jobs/{job_id}" if job_id else "https://www.kalibrr.com"

            # Lokasi dari google_location (city + region)
            geo = (job.get("google_location") or {}).get("address_components", {})
            location = _normalize_location(geo.get("city") or geo.get("region") or "")

            if title and company:
                listings.append(JobListing(
                    job_title=title,
                    company_name=company,
                    job_description=str(description)[:1000],
                    job_url=job_url,
                    source_name="Kalibrr",
                    source_url="https://www.kalibrr.com",
                    location=location.strip(),
                ))
        except Exception as e:
            logger.warning(f"  [Kalibrr] Gagal parse job: {e}")
            continue

    return listings


def scrape_glints(keyword: str, max_jobs: int = 10) -> list[JobListing]:
    """
    Scrape Glints Indonesia via headless browser (anti-403).

    Request API GraphQL langsung diblokir dari IP datacenter (403 Forbidden),
    jadi kita jalankan browser yang membuka halaman aslinya lalu intercept
    response GraphQL-nya. Lihat browser_scraper.scrape_glints_browser.
    """
    raw = scrape_glints_browser(keyword, max_jobs)
    return [JobListing(**item) for item in raw]


def scrape_jobstreet(keyword: str, max_jobs: int = 10) -> list[JobListing]:
    """
    Scrape JobStreet Indonesia via headless browser (anti-403).

    Endpoint chalice-search (SEEK) menolak request langsung dari server
    dengan 403, jadi kita buka halaman pencarian di browser dan intercept
    response API-nya. Lihat browser_scraper.scrape_jobstreet_browser.
    """
    raw = scrape_jobstreet_browser(keyword, max_jobs)
    return [JobListing(**item) for item in raw]


def scrape_linkedin(keyword: str, max_jobs: int = 10) -> list[JobListing]:
    """
    Scrape LinkedIn via guest jobs API (tanpa login).

    LinkedIn mengekspos endpoint publik `/jobs-guest/jobs/api/...` yang bisa
    diakses tanpa autentikasi maupun browser. Kartu lowongan (judul, perusahaan,
    lokasi, URL) diambil dari endpoint pencarian; deskripsi diambil dari
    endpoint detail per-lowongan (dengan throttle agar tidak kena rate-limit).
    """
    logger.info("  [LinkedIn] Memulai pencarian...")
    listings: list[JobListing] = []

    search_url = (
        "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    )
    params = {
        "keywords": keyword,
        "location": "Indonesia",
        "start": 0,
    }
    headers = {"Referer": "https://www.linkedin.com/jobs"}

    try:
        resp = requests.get(
            search_url,
            params=params,
            headers={**BASE_HEADERS, **headers},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.warning(f"  [LinkedIn] Gagal mendapatkan daftar lowongan: {e}")
        return listings

    soup = BeautifulSoup(resp.text, "lxml")
    cards = soup.select("li")
    logger.info(f"  [LinkedIn] Ditemukan {len(cards)} kandidat, mengambil detail...")

    for card in cards:
        if len(listings) >= max_jobs:
            break

        title_el = card.select_one(".base-search-card__title")
        company_el = card.select_one(".base-search-card__subtitle")
        location_el = card.select_one(".job-search-card__location")
        link_el = card.select_one("a.base-card__full-link") or card.select_one("a")

        if not title_el or not company_el:
            continue

        title = title_el.get_text(strip=True)
        company = company_el.get_text(strip=True)
        location = location_el.get_text(strip=True) if location_el else ""
        job_url = (link_el.get("href") if link_el else "") or ""
        job_url = job_url.split("?")[0]

        if not title or not company:
            continue

        # Hanya terima kartu lowongan asli (punya URL /jobs/view/),
        # buang elemen promosi/sign-in seperti "Click here to add your information".
        if "/jobs/view/" not in job_url:
            continue

        # Buang kartu promosi/CTA yang lolos (bukan lowongan sungguhan).
        low = title.lower()
        if any(p in low for p in ("click here", "sign in", "add your information")):
            continue

        # Buang lowongan berjudul skrip non-Latin dominan (lowongan luar negeri,
        # mis. Cyrillic) — judul lowongan Indonesia memakai huruf Latin.
        non_ascii = sum(1 for ch in title if ord(ch) > 127)
        if title and non_ascii > len(title) * 0.3:
            continue

        # Ambil ID lowongan dari URL (angka terakhir) untuk endpoint detail
        job_id = ""
        for part in reversed(job_url.rstrip("/").split("-")):
            if part.isdigit():
                job_id = part
                break

        description = _linkedin_description(job_id) if job_id else ""
        if not description:
            description = "Lihat detail di LinkedIn."

        listings.append(
            JobListing(
                job_title=title,
                company_name=company,
                job_description=description[:1000],
                job_url=job_url or "https://www.linkedin.com/jobs",
                source_name="LinkedIn",
                source_url="https://www.linkedin.com/jobs",
                location=_normalize_location(location),
            )
        )

    logger.info(f"  [LinkedIn] {len(listings)} lowongan diproses.")
    return listings


def _linkedin_description(job_id: str, delay: float = 0.4) -> str:
    """Ambil deskripsi lowongan dari endpoint detail guest LinkedIn."""
    detail_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    try:
        resp = requests.get(detail_url, headers=BASE_HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException:
        return ""
    finally:
        time.sleep(delay)  # throttle agar tidak kena rate-limit

    soup = BeautifulSoup(resp.text, "lxml")
    desc_el = soup.select_one(".description__text, .show-more-less-html__markup")
    return desc_el.get_text(" ", strip=True) if desc_el else ""


# ─── Webhook Delivery ─────────────────────────────────────────────────────────


def send_to_webhook(webhook_url: str, listing: JobListing, delay: float = 0.5) -> bool:
    """Mengirim satu job listing ke n8n Webhook via HTTP POST."""
    payload = listing.to_dict()
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        response.raise_for_status()
        logger.info(f"  ✓ Terkirim: '{listing.job_title}' dari {listing.source_name}")
        time.sleep(delay)  # throttle agar tidak spam webhook
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"  ✗ Gagal kirim '{listing.job_title}': {e}")
    return False


# ─── Main Controller ──────────────────────────────────────────────────────────


def scrape_all_sources(keyword: str, max_jobs: int) -> list[JobListing]:
    """Jalankan semua sumber untuk satu keyword; error per-sumber diisolasi."""
    results: list[JobListing] = []
    sources = [
        ("Kalibrr", scrape_kalibrr),
        ("Glints", scrape_glints),
        ("JobStreet", scrape_jobstreet),
        ("LinkedIn", scrape_linkedin),
    ]
    for name, fn in sources:
        try:
            results.extend(fn(keyword, max_jobs))
        except Exception as e:
            logger.error(f"[{name}] Error tidak terduga: {e}")
    return results


def _dedup_key(job: JobListing) -> str:
    """Kunci unik lowongan: URL bila ada, jika tidak pakai judul+perusahaan."""
    url = (job.job_url or "").split("?")[0].rstrip("/").lower()
    if url and url not in (
        "https://www.kalibrr.com",
        "https://glints.com/id",
        "https://id.jobstreet.com",
        "https://www.linkedin.com/jobs",
    ):
        return url
    return f"{job.job_title.strip().lower()}|{job.company_name.strip().lower()}"


def main() -> None:
    load_dotenv()

    webhook_url = os.getenv("N8N_WEBHOOK_URL", "").strip()
    # SEARCH_KEYWORD boleh berisi beberapa keyword dipisah koma.
    raw_keywords = os.getenv("SEARCH_KEYWORD", "Customer Service")
    keywords = [k.strip() for k in raw_keywords.split(",") if k.strip()]
    max_jobs = int(os.getenv("MAX_JOBS_PER_SOURCE", "10"))

    if not webhook_url:
        logger.error("N8N_WEBHOOK_URL tidak ditemukan di environment.")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("  Job Scraper Engine — Multi-Source, Multi-Keyword")
    logger.info(f"  Keywords : {', '.join(keywords)}")
    logger.info(f"  Max/src  : {max_jobs}")
    logger.info("=" * 60)

    # Kumpulkan hasil semua keyword, deduplikasi lintas keyword & sumber.
    seen: set[str] = set()
    all_listings: list[JobListing] = []
    for kw in keywords:
        logger.info(f"\n▶ Keyword: {kw}")
        for job in scrape_all_sources(kw, max_jobs):
            key = _dedup_key(job)
            if key in seen:
                continue
            seen.add(key)
            all_listings.append(job)

    if not all_listings:
        logger.warning("\nTidak ada lowongan ditemukan dari semua sumber.")
        logger.warning("Kemungkinan penyebab: API berubah, rate-limited, atau koneksi gagal.")
        sys.exit(0)

    # Urutkan: lowongan di area prioritas (Depok, Jaksel, Jakpus, Jaktim) didahulukan
    all_listings.sort(key=lambda j: location_priority(j.location))
    prioritized = sum(1 for j in all_listings if location_priority(j.location) < 99)

    logger.info(
        f"\nTotal {len(all_listings)} lowongan ditemukan "
        f"({prioritized} di area prioritas). Mulai kirim ke n8n..."
    )

    success_count = 0
    for item in all_listings:
        if send_to_webhook(webhook_url, item):
            success_count += 1

    logger.info("\n" + "=" * 60)
    logger.info("  Execution Summary")
    logger.info("=" * 60)
    logger.info(f"  Sumber aktif       : Kalibrr, Glints, JobStreet, LinkedIn")
    logger.info(f"  Total ditemukan    : {len(all_listings)}")
    logger.info(f"  Sukses terkirim    : {success_count}")
    logger.info(f"  Gagal terkirim     : {len(all_listings) - success_count}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()


