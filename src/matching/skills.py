"""Hebrew/English skill alias normalization and weighting."""
from __future__ import annotations

SKILL_ALIASES: dict[str, str] = {
    # English canonical
    "sql": "sql",
    "t-sql": "sql",
    "tsql": "sql",
    "python": "python",
    "pandas": "pandas",
    "numpy": "numpy",
    "tableau": "tableau",
    "power bi": "power bi",
    "powerbi": "power bi",
    "excel": "excel",
    "microsoft excel": "excel",
    "etl": "etl",
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "mysql": "mysql",
    "docker": "docker",
    "git": "git",
    "github": "github",
    "rest api": "rest api",
    "rest apis": "rest api",
    "data visualization": "data visualization",
    "machine learning": "machine learning",
    "looker": "looker",
    "snowflake": "snowflake",
    "dbt": "dbt",
    "airflow": "airflow",
    "spark": "spark",
    "kafka": "kafka",
    "linux": "linux",
    "oracle": "oracle database",
    "oracle database": "oracle database",
    # Hebrew → English canonical
    "פייתון": "python",
    "אקסל": "excel",
    "טבלו": "tableau",
    "פאוור בי איי": "power bi",
    "פאוורביאיי": "power bi",
    "ויזואליזציית נתונים": "data visualization",
    "ויזואליזציה": "data visualization",
    "מסד נתונים": "sql",
    "בסיסי נתונים": "sql",
}


HIGH_WEIGHT_SKILLS = {"sql", "python", "tableau", "power bi", "excel"}


def normalize_skill(skill: str) -> str:
    key = skill.strip().lower()
    return SKILL_ALIASES.get(key, key)


def normalize_skills(skills: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for skill in skills:
        canonical = normalize_skill(skill)
        if canonical and canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result
