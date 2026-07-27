# Deployment guide

## Local production-like run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-prod.txt
cp .env.example .env
# edit secrets
PYTHONPATH=. streamlit run app/Home.py --server.port=8501
```

Health check:

```bash
python -m src.healthcheck 8081
curl http://127.0.0.1:8081/health
```

## Docker

```bash
docker build -t job-scout-ai .
docker run --env-file .env -p 8501:8501 -p 8081:8081 \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/outputs:/app/outputs" \
  -v "$(pwd)/reports:/app/reports" \
  job-scout-ai
```

## HTTPS & domain

Put Streamlit behind a reverse proxy (Caddy/Nginx) with TLS:

```nginx
server {
  listen 443 ssl;
  server_name jobs.example.com;
  location / {
    proxy_pass http://127.0.0.1:8501;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
  }
}
```

## Database

- Alpha/beta: SQLite at `data/jobs.db`
- Backups: Settings → Backup, or `python -c "from src.security import backup_database; print(backup_database())"`
- Postgres: set `DATABASE_URL` and follow `migrations/README.md` (schema port required before full cutover)

## Monitoring

- App logs: `data/logs/jobscout.log`
- Health endpoint: `/health` on port 8081
- Search runs stored in `search_runs` table

## Limits for free / local users

- AI daily token budget via `AI_DAILY_TOKEN_BUDGET`
- Upload max size via `config.yaml` → `security.max_upload_mb`
- Search mutex prevents concurrent runs

## Future web split

Keep using `src/` as the API core. Replace Streamlit with FastAPI + React/PWA when ready for a public web product. Native phone apps remain out of scope until the web UX is stable.
