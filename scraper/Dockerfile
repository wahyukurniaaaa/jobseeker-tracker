# ─── Base: Playwright Python (Chromium + system deps sudah terpasang) ──────────
# Versi image HARUS sinkron dengan versi playwright di requirements.txt (1.48.0).
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy AS runtime

# Metadata
LABEL maintainer="jobseeker-pipeline"
LABEL description="Job scraper microservice — menarik lowongan dan push ke n8n webhook"
LABEL version="2.0.0"

WORKDIR /app

# Python optimizations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && playwright install chromium

# Copy source code
COPY main.py browser_scraper.py ./

# Jalankan sebagai user non-root bawaan image Playwright
RUN chown -R pwuser:pwuser /app
USER pwuser

# Health check: verifikasi Python & dependencies tersedia
HEALTHCHECK --interval=30s --timeout=10s --retries=1 \
    CMD python -c "import requests, bs4, dotenv, playwright; print('OK')" || exit 1

# Jalankan scraper
CMD ["python", "main.py"]
