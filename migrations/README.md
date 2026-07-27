"""
SQLite schema is created automatically by src.core.db.initialize_database().

For production PostgreSQL:
1. Set DATABASE_URL=postgresql://user:pass@host:5432/jobscout
2. Install requirements-prod.txt
3. Future: use Alembic with SQLAlchemy models mirroring SCHEMA_SQL

This folder reserves migration scripts for the Postgres upgrade path.
"""

NOTES = """
Migration path checklist:
- Export SQLite with: python -c "from src.security import backup_database; print(backup_database())"
- Create Postgres database
- Port schema from src/core/db.py SCHEMA_SQL (types: TEXT→TIMESTAMP/JSONB as needed)
- Point DATABASE_URL to Postgres and dual-write during cutover
"""
