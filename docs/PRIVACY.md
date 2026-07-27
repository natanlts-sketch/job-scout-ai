# Privacy & security notes

- Passwords: bcrypt hashes only
- API keys: environment variables only (never Streamlit secrets in git)
- CV uploads: type/size checks, sanitized names, per-user directories
- AI: off by default; requires `AI_ENABLED`, `ANTHROPIC_API_KEY`, and user consent
- Account deletion: Settings → type DELETE
- Retention: operational logs/search runs intended for periodic purge (180 days recommended)
- Backups: `data/backups/`
