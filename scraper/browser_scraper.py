"""
Browser-based Scraper — Glints & JobStreet (Anti-403 Mode)
===========================================================
Glints dan JobStreet memblokir request API langsung dari IP datacenter
(HTTP 403 Forbidden). Modul ini menjalankan headless browser (Playwright)
yang membuka halaman aslinya sehingga request internal (GraphQL / chalice-search)
lolos proteksi bot, lalu kita *intercept* response JSON-nya.

Pendekatan ini lebih tahan banting dibanding scraping DOM karena tidak
bergantung pada CSS class yang sering berubah — kita membaca payload API
yang sama persis dengan yang dipakai website.

Teknik ini terinspirasi dari:
  - https://github.com/anhvi02/GlintScraping      (Selenium + browser render)
  - https://github.com/okzapradhana/jobstreet-scrapper (Selenium + pagination)
Bedanya: kita intercept response API, bukan parse DOM.
"""

import logging
from typing import Callable, Optional
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

# Playwright diimpor lazily agar modul tetap bisa di-import walau belum terinstall
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    PLAYWRIGHT_AVAILABLE = True
except ImportError:  # pragma: no cover
    PLAYWRIGHT_AVAILABLE = False
    logger.warning(
        "Playwright belum terinstall. Scraper Glints/JobStreet dilewati. "
        "Jalankan: pip install playwright && playwright install chromium"
    )


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


def _deep_find_jobs(obj, results: list, key_hints: tuple = ("title", "name")) -> None:
    """
    Menelusuri struktur JSON secara rekursif untuk menemukan objek yang
    kemungkinan besar merupakan entri lowongan (punya field title/name +
    petunjuk company). Membuat parser tahan terhadap perubahan skema API.
    """
    if isinstance(obj, dict):
        has_title = any(k in obj for k in key_hints)
        has_company = "company" in obj or "companyName" in obj or "advertiser" in obj
        if has_title and has_company:
            results.append(obj)
        else:
            for v in obj.values():
                _deep_find_jobs(v, results, key_hints)
    elif isinstance(obj, list):
        for item in obj:
            _deep_find_jobs(item, results, key_hints)


def _glints_location(job: dict) -> str:
    """
    Bangun string lokasi ringkas dari objek job Glints.
    Contoh: "Tanjung Priok, Jakarta Utara" atau fallback ke nama distrik/kota.
    """
    loc = job.get("location")
    if not isinstance(loc, dict):
        city = job.get("city")
        if isinstance(city, dict):
            return city.get("name", "") or ""
        return ""

    district = loc.get("formattedName") or loc.get("name") or ""
    city = ""
    for parent in loc.get("parents") or []:
        if isinstance(parent, dict) and parent.get("administrativeLevelName") == "City":
            city = parent.get("formattedName") or parent.get("name") or ""
            break

    if district and city and district != city:
        return f"{district}, {city}"
    return district or city or ""


def _run_with_browser(worker: Callable, headless: bool = True):
    """Menjalankan `worker(page)` di dalam konteks browser Playwright."""
    if not PLAYWRIGHT_AVAILABLE:
        return []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )
        context = browser.new_context(
            user_agent=USER_AGENT,
            locale="id-ID",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        try:
            return worker(page)
        finally:
            context.close()
            browser.close()


# ─── Glints (intercept GraphQL) ────────────────────────────────────────────────


def scrape_glints_browser(keyword: str, max_jobs: int = 10) -> list[dict]:
    """
    Buka halaman explore Glints di browser, tangkap response GraphQL
    yang berisi hasil pencarian job, lalu normalisasi ke format standar.
    """
    logger.info("  [Glints] Memulai pencarian (browser mode)...")
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("  [Glints] Playwright tidak tersedia, dilewati.")
        return []

    search_url = (
        "https://glints.com/id/opportunities/jobs/explore"
        f"?keyword={quote_plus(keyword)}&country=ID&locationName=Indonesia"
    )

    def worker(page) -> list[dict]:
        captured: list = []

        def handle_response(response):
            url = response.url
            if "graphql" not in url and "searchJobs" not in url:
                return
            try:
                data = response.json()
            except Exception:
                return
            jobs: list = []
            _deep_find_jobs(data, jobs)
            if jobs:
                captured.extend(jobs)

        page.on("response", handle_response)

        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
        except PWTimeout:
            logger.warning("  [Glints] Timeout saat memuat halaman (lanjut dgn data yg ada).")

        # Polling: tunggu response GraphQL tertangkap (maks ~15 dtk)
        for _ in range(15):
            if captured:
                page.wait_for_timeout(1000)  # beri waktu response lanjutan
                break
            page.wait_for_timeout(1000)

        # Deduplikasi berdasarkan id/title+company
        seen = set()
        listings = []
        for job in captured:
            title = (job.get("title") or job.get("name") or "").strip()
            company = job.get("company")
            company_name = (
                company.get("name", "").strip() if isinstance(company, dict) else ""
            )
            if not title or not company_name:
                continue
            job_id = str(job.get("id") or f"{title}|{company_name}")
            if job_id in seen:
                continue
            seen.add(job_id)

            desc = (
                job.get("descriptionText")
                or job.get("description")
                or "Lihat detail di Glints."
            )
            slug = job.get("id", "")
            job_url = (
                f"https://glints.com/id/opportunities/jobs/{slug}"
                if slug
                else "https://glints.com/id"
            )
            listings.append(
                {
                    "job_title": title,
                    "company_name": company_name,
                    "job_description": str(desc)[:1000],
                    "job_url": job_url,
                    "source_name": "Glints",
                    "source_url": "https://glints.com/id",
                    "location": _glints_location(job),
                }
            )
            if len(listings) >= max_jobs:
                break

        logger.info(f"  [Glints] Ditemukan {len(listings)} lowongan. Mengambil deskripsi detail...")
        for item in listings:
            if item["job_url"] != "https://glints.com/id":
                try:
                    logger.info(f"  [Glints] Membuka detail: {item['job_url']}")
                    page.goto(item["job_url"], wait_until="domcontentloaded", timeout=20000)
                    page.wait_for_timeout(1000)
                    desc_el = page.query_selector("div[class*='JobDescription']")
                    if desc_el:
                        item["job_description"] = desc_el.inner_text().strip()
                except Exception as e:
                    logger.warning(f"  [Glints] Gagal mengambil deskripsi detail {item['job_url']}: {e}")

        return listings

    try:
        return _run_with_browser(worker)
    except Exception as e:
        logger.warning(f"  [Glints] Gagal (browser): {e}")
        return []


# ─── JobStreet (intercept chalice-search) ───────────────────────────────────────


def scrape_jobstreet_browser(keyword: str, max_jobs: int = 10) -> list[dict]:
    """
    Buka halaman pencarian JobStreet Indonesia (platform SEEK) di browser
    lalu ekstrak kartu lowongan dari DOM.

    JobStreet me-render hasil pencarian via SSR (bukan API JSON terpisah),
    jadi kita baca dari DOM menggunakan atribut `data-automation` milik SEEK
    yang relatif stabil (normalJob / jobTitle / jobCompany / jobShortDescription).
    """
    logger.info("  [JobStreet] Memulai pencarian (browser mode)...")
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("  [JobStreet] Playwright tidak tersedia, dilewati.")
        return []

    search_url = (
        "https://id.jobstreet.com/id/jobs"
        f"?keywords={quote_plus(keyword)}&where=Indonesia"
    )

    def worker(page) -> list[dict]:
        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
        except PWTimeout:
            logger.warning("  [JobStreet] Timeout saat memuat halaman (lanjut dgn data yg ada).")

        # Tunggu kartu lowongan muncul (SSR + hydration)
        try:
            page.wait_for_selector("[data-automation='normalJob']", timeout=15000)
        except PWTimeout:
            logger.warning("  [JobStreet] Kartu lowongan tidak muncul.")
            return []

        cards = page.query_selector_all("[data-automation='normalJob']")
        listings = []
        seen = set()

        for card in cards:
            if len(listings) >= max_jobs:
                break
            title_el = card.query_selector("[data-automation='jobTitle']")
            company_el = card.query_selector("[data-automation='jobCompany']")
            if not title_el or not company_el:
                continue

            title = (title_el.inner_text() or "").strip()
            company = (company_el.inner_text() or "").strip()
            if not title or not company:
                continue

            key = f"{title}|{company}"
            if key in seen:
                continue
            seen.add(key)

            # URL job dari href judul
            job_url = title_el.get_attribute("href") or ""
            if job_url and job_url.startswith("/"):
                job_url = "https://id.jobstreet.com" + job_url
            if not job_url:
                job_url = search_url

            desc_el = card.query_selector("[data-automation='jobShortDescription']")
            desc = (desc_el.inner_text().strip() if desc_el else "") or "Lihat detail di JobStreet."

            loc_el = card.query_selector("[data-automation='jobLocation']")
            location = loc_el.inner_text().strip() if loc_el else ""

            listings.append(
                {
                    "job_title": title,
                    "company_name": company,
                    "job_description": str(desc)[:1000],
                    "job_url": job_url,
                    "source_name": "JobStreet",
                    "source_url": "https://id.jobstreet.com",
                    "location": location,
                }
            )

        logger.info(f"  [JobStreet] Ditemukan {len(listings)} lowongan. Mengambil deskripsi detail...")
        for item in listings:
            if item["job_url"] != search_url:
                try:
                    logger.info(f"  [JobStreet] Membuka detail: {item['job_url']}")
                    page.goto(item["job_url"], wait_until="domcontentloaded", timeout=20000)
                    page.wait_for_timeout(1000)
                    desc_el = page.query_selector("[data-automation='jobAdDetails']")
                    if desc_el:
                        item["job_description"] = desc_el.inner_text().strip()
                except Exception as e:
                    logger.warning(f"  [JobStreet] Gagal mengambil deskripsi detail {item['job_url']}: {e}")

        return listings

    try:
        return _run_with_browser(worker)
    except Exception as e:
        logger.warning(f"  [JobStreet] Gagal (browser): {e}")
        return []
