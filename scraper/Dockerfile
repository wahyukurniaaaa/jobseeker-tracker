# ─── Build Stage ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dan install dependencies ke virtual environment
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


# ─── Runtime Stage ────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Metadata
LABEL maintainer="jobseeker-pipeline"
LABEL description="Job scraper microservice — menarik lowongan dan push ke n8n webhook"
LABEL version="1.0.0"

# Security: jalankan sebagai non-root user
RUN groupadd --gid 1001 scraper \
    && useradd --uid 1001 --gid scraper --no-create-home scraper

WORKDIR /app

# Copy venv dari build stage (tidak perlu reinstall)
COPY --from=builder /opt/venv /opt/venv

# Copy source code
COPY main.py .

# Pastikan Python gunakan venv
ENV PATH="/opt/venv/bin:$PATH"

# Env vars wajib diisi saat runtime (via --env-file atau -e)
# ENV TARGET_URL=""
# ENV N8N_WEBHOOK_URL=""

# Python optimizations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switch ke non-root user
USER scraper

# Health check: verifikasi Python dan dependencies tersedia
HEALTHCHECK --interval=30s --timeout=5s --retries=1 \
    CMD python -c "import requests, bs4, dotenv; print('OK')" || exit 1

# Jalankan scraper
CMD ["python", "main.py"]
