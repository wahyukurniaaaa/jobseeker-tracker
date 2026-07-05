# n8n Pipeline Architecture — Job Application Automation

> Blueprint integrasi lengkap: **Scraper → n8n → AI → Supabase → Dashboard SvelteKit**

---

## Gambaran Besar (Bird's Eye View)

```
┌────────────────┐     HTTP POST      ┌──────────────────────────────────────────────────────┐
│  Python Scraper│ ─────────────────► │                  n8n Workflow                        │
│  (Docker)      │   JSON Payload     │                                                      │
└────────────────┘                    │  [Webhook] → [Validate] → [AI Node] → [Supabase]     │
                                      │                                ↓                     │
                                      │                         [Notifikasi]                  │
                                      └──────────────────────────────────────────────────────┘
                                                                       │
                                                                       ▼
                                                          ┌────────────────────┐
                                                          │  Supabase DB       │
                                                          │  job_applications  │
                                                          └────────────────────┘
                                                                       │
                                                                       ▼
                                                          ┌────────────────────┐
                                                          │  SvelteKit         │
                                                          │  Dashboard         │
                                                          └────────────────────┘
```

---

## Node-by-Node Workflow Specification

### Node 1 — Webhook Trigger

| Property | Value |
|----------|-------|
| **Type** | `n8n-nodes-base.webhook` |
| **HTTP Method** | `POST` |
| **Path** | `/job-scraper` |
| **Response Mode** | `Last Node` |
| **Authentication** | Header Auth (recommended: `X-Scraper-Token`) |

#### Input Schema (Payload dari `main.py`)

Ini adalah JSON yang akan diterima oleh node Webhook dari scraper:

```json
{
  "job_title": "Senior Backend Engineer",
  "company_name": "PT Teknologi Maju Indonesia",
  "job_description": "Kami mencari Backend Engineer berpengalaman dengan keahlian di Node.js, PostgreSQL, dan arsitektur microservice. Kandidat ideal memiliki pengalaman minimal 3 tahun dalam membangun API RESTful yang scalable. Tanggung jawab meliputi desain database, code review, dan kolaborasi dengan tim frontend. Skill yang dibutuhkan: Node.js, TypeScript, PostgreSQL, Docker, Kubernetes, Redis.",
  "job_url": "https://example-portal.com/jobs/senior-backend-12345",
  "source_url": "https://example-portal.com/jobs"
}
```

**Field Mapping:**
| Field | Type | Sumber | Keterangan |
|-------|------|--------|------------|
| `job_title` | `string` | Scraper | Judul posisi lowongan |
| `company_name` | `string` | Scraper | Nama perusahaan |
| `job_description` | `string` | Scraper | Deskripsi lengkap lowongan |
| `job_url` | `string` | Scraper | URL halaman detail lowongan |
| `source_url` | `string` | Scraper | URL portal kerja sumber |

---

### Node 2 — Validate & Deduplicate (Code Node)

| Property | Value |
|----------|-------|
| **Type** | `n8n-nodes-base.code` |
| **Language** | JavaScript |

**Tujuan:** Validasi field wajib dan normalisasi data sebelum diproses AI.

```javascript
// n8n Code Node — Validasi Input
const item = $input.first().json;

// Validasi field wajib
const required = ['job_title', 'company_name', 'job_description', 'job_url'];
for (const field of required) {
  if (!item[field] || item[field].trim() === '') {
    throw new Error(`Field wajib kosong: ${field}`);
  }
}

// Normalisasi data
return [{
  json: {
    job_title: item.job_title.trim(),
    company_name: item.company_name.trim(),
    job_description: item.job_description.trim(),
    job_url: item.job_url.trim(),
    source_url: item.source_url?.trim() || '',
    received_at: new Date().toISOString(),
  }
}];
```

---

### Node 3 — AI Processing (OpenAI / Gemini Node)

| Property | Value |
|----------|-------|
| **Type** | `@n8n/n8n-nodes-langchain.openAi` atau HTTP Request ke Gemini API |
| **Model** | `gpt-4o-mini` / `gemini-1.5-flash` |
| **Operation** | Chat completion |

**Tujuan:** Menganalisis `job_description` terhadap CV kandidat untuk:
1. Menghitung **match score** (0–100)
2. Mengidentifikasi **skill gap** (`missing_skills`)
3. Membuat **cover letter** yang dipersonalisasi

**System Prompt Template:**

```
Kamu adalah AI career advisor yang ahli dalam analisis lowongan kerja.

CV Kandidat (Siti Miftahul Jannah):
---
- Nama: Siti Miftahul Jannah
- Posisi: Customer Service & Administrative Professional
- Pengalaman: Lebih dari 4 tahun di bidang administrasi, pengelolaan data, dan operasional layanan pelanggan (PT. Bank Mandiri Tbk & PT. Astra World).
- Keahlian Teknis: Microsoft Office, Google Workspace, CRM System, Helpdesk Ticketing, Data Entry & Reporting, Email Correspondence, Administrasi Kantor, SPSS.
- Soft Skills: Komunikasi Persuasif, Negosiasi & Resolusi Konflik, Problem Solving, Kerja Sama Tim, Adaptif, Multitasking, Empati, Detail-Oriented.
- Pendidikan: S1 Manajemen, Universitas Yarsi (GPA 3.6/4.00), fokus manajemen operasional & bisnis.
- Bahasa: Bahasa Indonesia (Native), Bahasa Inggris (Basic).
---

Tugas kamu:
1. Baca job_description yang diberikan.
2. Cocokkan dengan CV kandidat.
3. Hitung match_score (0-100) berdasarkan kesesuaian skill dan kualifikasi (CS, Admin, Data Entry, CRM, dll).
4. Identifikasi missing_skills: skill/kualifikasi yang dibutuhkan lowongan tapi tidak ada di CV.
5. Tulis cover_letter yang profesional dan singkat (maksimal 250 kata) dalam Bahasa Indonesia.

Kembalikan response HARUS berbentuk JSON murni seperti ini:
{
  "match_score": 85,
  "missing_skills": ["English Advanced", "Zendesk"],
  "cover_letter": "Kepada Yth..."
}
```

**User Message:**
```
Analisis lowongan berikut:

Posisi: {{ $json.job_title }}
Perusahaan: {{ $json.company_name }}
Deskripsi: {{ $json.job_description }}
```

**Expected AI Output:**

```json
{
  "match_score": 82,
  "missing_skills": ["Pengalaman spesifik di e-commerce/marketplace", "English Advanced (untuk komunikasi internasional)", "Advanced CRM customization"],
  "cover_letter": "Kepada Yth. Tim Rekrutmen Tokopedia,\n\nSaya, Siti Miftahul Jannah, sangat tertarik dengan posisi Customer Service Specialist & Data Administrator di Tokopedia. Dengan lebih dari 4 tahun pengalaman di bidang customer service dan administrasi data di PT. Bank Mandiri Tbk dan PT. Astra World, saya percaya memiliki fondasi kuat untuk berkontribusi pada tim Anda.\n\nKompetesi saya mencakup pengelolaan database yang akurat melalui CRM System, penanganan user inquiries dengan detail-oriented approach, dan resolusi konflik yang efektif. Saya mahir menggunakan Google Workspace dan CRM ticketing systems, yang sejalan dengan kebutuhan posisi ini. Pengalaman di layanan pelanggan telah mengasah kemampuan komunikasi interpersonal dan problem-solving saya dalam menghadapi berbagai skenario kompleks.\n\nSebagai S1 Manajemen dengan GPA 3.6/4.00 dan fokus pada manajemen operasional, saya memahami pentingnya efisiensi proses dan kepuasan pelanggan. Saya juga menguasai data entry, reporting, dan memiliki kemampuan multitasking yang kuat dalam lingkungan fast-paced.\n\nSaya siap untuk berkembang di ekosistem e-commerce Tokopedia dan berkontribusi pada kesuksesan tim customer service Anda.\n\nTerima kasih atas pertimbangan Anda.\n\nHormat,\nSiti Miftahul Jannah"
}
```

---

### Node 4 — Parse AI Response (Code Node)

| Property | Value |
|----------|-------|
| **Type** | `n8n-nodes-base.code` |
| **Language** | JavaScript |

**Tujuan:** Menggabungkan data scraper + output AI menjadi payload final untuk Supabase.

```javascript
// n8n Code Node — Merge & Prepare Supabase Payload
const scraperData = $('Validate & Deduplicate').first().json;
const aiRaw = $input.first().json;

// Parse JSON dari response AI (handle jika berbentuk string)
let aiData;
try {
  const content = aiRaw?.choices?.[0]?.message?.content
    ?? aiRaw?.candidates?.[0]?.content?.parts?.[0]?.text
    ?? JSON.stringify(aiRaw);
  aiData = typeof content === 'string' ? JSON.parse(content) : content;
} catch (e) {
  throw new Error(`Gagal parse AI response: ${e.message}`);
}

// Validasi match_score
const matchScore = Math.min(100, Math.max(0, Number(aiData.match_score) || 0));

return [{
  json: {
    company_name: scraperData.company_name,
    job_title: scraperData.job_title,
    job_url: scraperData.job_url,
    match_score: matchScore,
    missing_skills: aiData.missing_skills ?? [],
    cover_letter: aiData.cover_letter ?? '',
    status: 'To Apply',
  }
}];
```

---

### Node 5 — Supabase Insert

| Property | Value |
|----------|-------|
| **Type** | `n8n-nodes-base.supabase` |
| **Operation** | `Create` |
| **Table Name** | `job_applications` |

#### Supabase Insert Schema (Payload Final)

Ini adalah JSON yang di-mapping oleh n8n untuk dikirim ke tabel `job_applications`:

```json
{
  "company_name": "PT Teknologi Maju Indonesia",
  "job_title": "Senior Backend Engineer",
  "job_url": "https://example-portal.com/jobs/senior-backend-12345",
  "match_score": 78,
  "missing_skills": ["Kubernetes", "Redis", "TypeScript"],
  "cover_letter": "Dengan hormat,\n\nSaya Siti Miftahul Jannah...",
  "status": "To Apply"
}
```

> **Catatan:** `id` dan `created_at` tidak perlu dikirim — keduanya di-generate otomatis oleh Supabase.

**Field Mapping di n8n Supabase Node:**

| Kolom Supabase | n8n Expression | Tipe |
|----------------|----------------|------|
| `company_name` | `{{ $json.company_name }}` | `text` |
| `job_title` | `{{ $json.job_title }}` | `text` |
| `job_url` | `{{ $json.job_url }}` | `text` |
| `match_score` | `{{ $json.match_score }}` | `numeric` |
| `missing_skills` | `{{ $json.missing_skills }}` | `jsonb` |
| `cover_letter` | `{{ $json.cover_letter }}` | `text` |
| `status` | `{{ $json.status }}` | `text` |

---

### Node 6 — Notifikasi (Optional)

| Channel | n8n Node | Trigger |
|---------|----------|---------|
| **Telegram** | `n8n-nodes-base.telegram` | Setiap insert sukses |
| **Slack** | `n8n-nodes-base.slack` | Batch harian (match_score > 80) |
| **Email** | `n8n-nodes-base.emailSend` | Jika ada Interview |

**Contoh Telegram Message:**
```
Lamaran Baru Ditambahkan!

Posisi: {{ $json.job_title }}
Perusahaan: {{ $json.company_name }}
Match Score: {{ $json.match_score }}%
Status: {{ $json.status }}

{{ $json.job_url }}
```

---

## Ringkasan Alur Data

```
main.py (Scraper)
    |
    |  POST /webhook/job-scraper
    |  { job_title, company_name, job_description, job_url, source_url }
    v
[Node 1: Webhook Trigger]
    |
    |  Menerima & meneruskan payload
    v
[Node 2: Validate & Deduplicate]
    |
    |  Validasi field, normalisasi string
    v
[Node 3: AI Processing]
    |
    |  Input: job_description + CV template
    |  Output: { match_score, missing_skills, cover_letter }
    v
[Node 4: Parse AI Response]
    |
    |  Merge scraper + AI data
    |  Final payload siap insert
    v
[Node 5: Supabase Insert]
    |
    |  INSERT INTO job_applications (...)
    v
[Node 6: Notifikasi Telegram/Slack]
    |
    |  "Lamaran baru: Senior Backend Engineer (78%)"
    v
  DONE
```

---

## Supabase Table Schema (Reference)

Pastikan tabel `job_applications` memiliki struktur berikut:

```sql
create table public.job_applications (
  id             uuid        primary key default gen_random_uuid(),
  company_name   text        not null,
  job_title      text        not null,
  job_url        text,
  match_score    numeric     default 0 check (match_score >= 0 and match_score <= 100),
  missing_skills jsonb       default '[]'::jsonb,
  cover_letter   text,
  status         text        default 'To Apply'
                             check (status in ('To Apply', 'Applied', 'Rejected', 'Interview')),
  created_at     timestamptz default now()
);

-- Index untuk performa query dashboard
create index idx_job_applications_match_score on job_applications (match_score desc);
create index idx_job_applications_status      on job_applications (status);
create index idx_job_applications_created_at  on job_applications (created_at desc);
```

---

## Cara Setup & Menjalankan

### 1. Konfigurasi Scraper `.env`
```env
TARGET_URL=https://url-portal-kerja-target.com/jobs
N8N_WEBHOOK_URL=http://your-n8n-instance:5678/webhook/job-scraper
```

### 2. Jalankan Scraper

```bash
# Via Python langsung
cd scraper/
cp .env.example .env
# Edit .env dengan nilai asli
python main.py

# Via Docker
docker build -t job-scraper .
docker run --env-file .env job-scraper

# Via Podman
podman build -t job-scraper .
podman run --env-file .env job-scraper
```

### 3. Jadwalkan (Cron)
```bash
# Jalankan scraper setiap hari pukul 08:00
0 8 * * * docker run --env-file /path/to/scraper/.env job-scraper
```
