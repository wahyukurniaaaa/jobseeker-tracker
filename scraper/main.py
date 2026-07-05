"""
Job Scraper Microservice — Multi-Source (API Mode)
===================================================
Menarik lowongan kerja dari portal Indonesia via API internal mereka
(lebih stabil dari CSS scraping karena tidak bergantung pada struktur HTML).

Sources:
  - Kalibrr (via internal search API)
  - Glints Indonesia (via internal search API)
  - JobStreet Indonesia (via internal search API)

Konfigurasi via environment variables:
  - N8N_WEBHOOK_URL   : URL Webhook n8n yang menerima payload JSON
  - SEARCH_KEYWORD    : Kata kunci pencarian (default: "Customer Service")
  - MAX_JOBS_PER_SOURCE : Maks lowongan per sumber (default: 10)
"""

import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from typing import Optional

import requests
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
    source_name: str
    source_url: str

    def to_dict(self) -> dict:
        return asdict(self)


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

            if title and company:
                listings.append(JobListing(
                    job_title=title,
                    company_name=company,
                    job_description=str(description)[:1000],
                    job_url=job_url,
                    source_name="Kalibrr",
                    source_url="https://www.kalibrr.com",
                ))
        except Exception as e:
            logger.warning(f"  [Kalibrr] Gagal parse job: {e}")
            continue

    return listings


def scrape_glints(keyword: str, max_jobs: int = 10) -> list[JobListing]:
    """
    Scrape Glints Indonesia via GraphQL API internal.
    Glints menggunakan GraphQL endpoint yang bisa diakses.
    """
    logger.info("  [Glints] Memulai pencarian...")
    listings = []

    url = "https://glints.com/api/graphql"
    headers = {
        "Content-Type": "application/json",
        "Referer": "https://glints.com/id/opportunities/jobs/explore",
        "x-glints-client": "web",
    }
    query = """
    query SearchJobs($keyword: String!, $limit: Int!, $offset: Int!) {
      searchJobs(keyword: $keyword, limit: $limit, offset: $offset, countryCode: "ID") {
        data {
          id
          title
          salaryEstimate
          country { name }
          city { name }
          company { name }
          isEasyApply
          descriptionText: description
        }
      }
    }
    """
    payload = {
        "query": query,
        "variables": {"keyword": keyword, "limit": max_jobs, "offset": 0}
    }

    try:
        resp = requests.post(url, json=payload, headers={**BASE_HEADERS, **headers}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        jobs = data.get("data", {}).get("searchJobs", {}).get("data", [])
        logger.info(f"  [Glints] Ditemukan {len(jobs)} lowongan.")

        for job in jobs[:max_jobs]:
            try:
                title = job.get("title", "").strip()
                company = job.get("company", {}).get("name", "").strip()
                desc = job.get("descriptionText") or "Lihat detail di Glints."
                job_id = job.get("id", "")
                job_url = f"https://glints.com/id/opportunities/jobs/{job_id}" if job_id else "https://glints.com/id"

                if title and company:
                    listings.append(JobListing(
                        job_title=title,
                        company_name=company,
                        job_description=str(desc)[:1000],
                        job_url=job_url,
                        source_name="Glints",
                        source_url="https://glints.com/id",
                    ))
            except Exception as e:
                logger.warning(f"  [Glints] Gagal parse job: {e}")
                continue

    except Exception as e:
        logger.warning(f"  [Glints] Gagal mendapatkan data: {e}")

    return listings


def scrape_jobstreet(keyword: str, max_jobs: int = 10) -> list[JobListing]:
    """
    Scrape JobStreet Indonesia via Chalice API.
    JobStreet (SEEK Asia) mengekspos endpoint API yang dapat diakses.
    """
    logger.info("  [JobStreet] Memulai pencarian...")
    listings = []

    # JobStreet Indonesia menggunakan SEEK Chalice API
    url = "https://id.jobstreet.com/api/chalice-search/v4/search"
    params = {
        "siteKey": "ID-Main",
        "sourcesystem": "JobStreet",
        "userqueryid": "customer-service",
        "userid": "0",
        "usersessionid": "0",
        "eventCaptureSessionId": "0",
        "where": "Indonesia",
        "what": keyword,
        "page": 1,
        "pageSize": max_jobs,
        "include": "seodata",
        "locale": "id-ID",
    }
    headers = {
        "Referer": "https://id.jobstreet.com/",
        "Accept": "application/json",
    }

    data = api_get(url, params=params, headers=headers)
    if not data:
        logger.warning("  [JobStreet] Gagal mendapatkan data dari API.")
        return listings

    jobs = data.get("data", []) or data.get("jobs", [])
    logger.info(f"  [JobStreet] Ditemukan {len(jobs)} lowongan.")

    for job in jobs[:max_jobs]:
        try:
            title = job.get("title", "").strip()
            company = (job.get("companyName") or job.get("advertiser", {}).get("description", "")).strip()
            desc = job.get("teaser") or job.get("abstract") or "Lihat detail di JobStreet."
            job_id = job.get("id", "")
            job_url = f"https://id.jobstreet.com/id/job/{job_id}" if job_id else "https://id.jobstreet.com"

            if title and company:
                listings.append(JobListing(
                    job_title=title,
                    company_name=company,
                    job_description=str(desc)[:1000],
                    job_url=job_url,
                    source_name="JobStreet",
                    source_url="https://id.jobstreet.com",
                ))
        except Exception as e:
            logger.warning(f"  [JobStreet] Gagal parse job: {e}")
            continue

    return listings


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


def main() -> None:
    load_dotenv()

    webhook_url = os.getenv("N8N_WEBHOOK_URL", "").strip()
    keyword = os.getenv("SEARCH_KEYWORD", "Customer Service").strip()
    max_jobs = int(os.getenv("MAX_JOBS_PER_SOURCE", "10"))

    if not webhook_url:
        logger.error("N8N_WEBHOOK_URL tidak ditemukan di environment.")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("  Job Scraper Engine — Multi-Source API Mode")
    logger.info(f"  Keyword  : {keyword}")
    logger.info(f"  Max/src  : {max_jobs}")
    logger.info("=" * 60)

    all_listings: list[JobListing] = []

    # ── Source 1: Kalibrr ──
    try:
        kalibrr_jobs = scrape_kalibrr(keyword, max_jobs)
        all_listings.extend(kalibrr_jobs)
    except Exception as e:
        logger.error(f"[Kalibrr] Error tidak terduga: {e}")

    # ── Source 2: Glints ──
    try:
        glints_jobs = scrape_glints(keyword, max_jobs)
        all_listings.extend(glints_jobs)
    except Exception as e:
        logger.error(f"[Glints] Error tidak terduga: {e}")

    # ── Source 3: JobStreet ──
    try:
        jobstreet_jobs = scrape_jobstreet(keyword, max_jobs)
        all_listings.extend(jobstreet_jobs)
    except Exception as e:
        logger.error(f"[JobStreet] Error tidak terduga: {e}")

    if not all_listings:
        logger.warning("\nTidak ada lowongan ditemukan dari semua sumber.")
        logger.warning("Kemungkinan penyebab: API berubah, rate-limited, atau koneksi gagal.")
        sys.exit(0)

    logger.info(f"\nTotal {len(all_listings)} lowongan ditemukan. Mulai kirim ke n8n...")

    success_count = 0
    for item in all_listings:
        if send_to_webhook(webhook_url, item):
            success_count += 1

    logger.info("\n" + "=" * 60)
    logger.info("  Execution Summary")
    logger.info("=" * 60)
    logger.info(f"  Sumber aktif       : Kalibrr, Glints, JobStreet")
    logger.info(f"  Total ditemukan    : {len(all_listings)}")
    logger.info(f"  Sukses terkirim    : {success_count}")
    logger.info(f"  Gagal terkirim     : {len(all_listings) - success_count}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()


