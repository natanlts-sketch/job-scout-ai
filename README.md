# Job Scout AI

Automated junior-data job scout with multi-user CV matching, ATS scoring, Hebrew/English support, application packages, and an optional Anthropic AI layer.

Alpha/beta target: **local multi-user Streamlit + SQLite**.  
Finished product direction: **responsive web** (phone native app deferred).

---

## Features

- Multi-source job fetch (Remotive, RemoteOK, Arbeitnow) with per-source error isolation
- SQLite dedupe, new-job flags, date + minimum-score filters
- HE/EN title, location, remote/hybrid/onsite detection
- Weighted ATS score, matched/missing skills, match explanations
- Israel / Remote / Overseas bucketing + Excel multi-sheet export
- Multi-user auth (bcrypt), per-user CV upload (DOCX/PDF), preferences
- Streamlit UI: Dashboard, CV, Search, Jobs, Applications, Settings, Statistics
- Manual Search Now + scheduler mutex + last/next run tracking
- Application tracking statuses and one-click application packages (no auto-submit)
- Optional Anthropic AI (feature-flagged, consent-gated, cached, budget-limited)
- Email daily reports + high-match alerts (deduped)
- Security helpers: upload validation, backups, delete-account, privacy notice
- Docker + health endpoint for web deployment path

---

## Architecture

```text
app/ (Streamlit UI)
        │
        ▼
src/core · sources · matching · cv · auth · search · applications · ai · notify · stats
        │
        ▼
   SQLite (alpha/beta) ──► Postgres-ready schema notes in migrations/
```

Business logic lives in `src/` so a future FastAPI + React/PWA UI can reuse the same core.

---

## Project structure

```text
app/                 Streamlit multipage UI
src/
  core/              config, db, models, logging
  sources/           Remotive, RemoteOK, Arbeitnow
  matching/          scoring, location, export, skills
  cv/                parse, keywords, tailor, upload
  auth/              users + preferences
  search/            orchestrated search runs + locks
  applications/      tracking + packages
  ai/                Anthropic client + rule fallbacks
  notify/            email
  stats/             analytics
  security/          encryption helpers, privacy, backup
  scheduler/         APScheduler
tests/
migrations/          Postgres upgrade path notes
config.yaml
.env.example
Dockerfile
```

---

## Installation (local)

```bash
git clone https://github.com/natanlts-sketch/job-scout-ai.git
cd job-scout-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Place your master CV at `data/cv/master_cv.docx` (optional for CLI; UI users upload their own).

---

## Environment variables

See [`.env.example`](.env.example):

| Variable | Purpose |
|----------|---------|
| `EMAIL_*` | SMTP daily reports |
| `AI_ENABLED` / `ANTHROPIC_API_KEY` | Optional Claude features |
| `AI_MODEL` / `AI_DAILY_TOKEN_BUDGET` | Model + cost guardrail |
| `SETTINGS_ENCRYPTION_KEY` | Fernet key for sensitive settings |
| `APP_SECRET_KEY` | App secret |
| `DATABASE_URL` | SQLite default; Postgres later |

A ChatGPT Plus subscription does **not** include API usage. This project uses **Anthropic** API billing when AI is enabled.

---

## Running

CLI scout:

```bash
python -m src.job_scout
```

Streamlit UI:

```bash
PYTHONPATH=. streamlit run app/Home.py
```

Health endpoint (deployments):

```bash
python -m src.healthcheck 8081
```

---

## Testing

```bash
PYTHONPATH=. pytest -q
```

Coverage includes matching, HE/EN keywords, dedupe, CV upload, application packages, user isolation, and email HTML.

---

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for Docker, HTTPS notes, backups, and the Postgres path.

```bash
docker build -t job-scout-ai .
docker run --env-file .env -p 8501:8501 -p 8081:8081 job-scout-ai
```

---

## Privacy & security

- Passwords hashed with bcrypt
- Uploads validated by type/size; filenames sanitized
- Per-user upload/application folders
- AI CV transmission requires explicit user consent
- Delete-account removes cascaded user data
- Do not commit `.env`, CVs, or `data/jobs.db`

---

## Limitations

- No native mobile app yet (responsive web only)
- No automatic form submission / CAPTCHA bypass
- PDF tailored CVs are text-based exports (DOCX keeps richer formatting)
- Public APIs only — no scraping of sites that forbid it
- Salary preference stored but unused until salary data exists

---

## Roadmap

- Production Postgres cutover
- FastAPI + PWA frontend split
- More legal public sources
- Richer PDF layout preservation
- Optional PWA install for phone home-screen use

---

## Sample output (no personal data)

```text
outputs/applications/1/Acme_Junior_Data_Analyst_2026-07-27/
  tailored_cv.docx
  tailored_cv.pdf
  cover_letter.txt
  job_description.txt
  match_explanation.txt
  missing_skills.txt
  interview_notes.txt
  recruiter_message.txt
  source_link.txt
```

---

## Author

**Natan Mamedov** — Junior Data Analyst · Python · SQL · Tableau · Automation
