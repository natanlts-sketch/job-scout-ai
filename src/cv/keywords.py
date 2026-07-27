import re

from src.matching.skills import SKILL_ALIASES, normalize_skills

STOPWORDS = {
    "the", "and", "with", "for", "from", "into",
    "using", "work", "experience", "years",
    "skills", "ability", "our", "you", "your",
    "analyst", "data", "cleaning", "dashboard", "dashboards",
    "את", "של", "על", "עם", "או", "הוא", "היא",
}

TECH_PHRASES = set(SKILL_ALIASES.keys()) | {
    "power bi",
    "sql server",
    "machine learning",
    "data analysis",
    "data visualization",
    "rest api",
    "rest apis",
    "google colab",
    "generative ai",
    "microsoft excel",
    "oracle database",
    "postgresql",
    "webhooks",
    "github",
    "docker",
    "linux",
    "tableau",
    "python",
    "sql",
    "excel",
    "etl",
    "looker",
    "snowflake",
    "dbt",
    "airflow",
}


def extract_keywords(text: str) -> list[str]:
    if not text:
        return []
    normalized_text = text.lower()
    keywords = set()
    phrase_words = set()

    # Longer phrases first
    for phrase in sorted(TECH_PHRASES, key=len, reverse=True):
        if phrase in normalized_text:
            keywords.add(phrase)
            phrase_words.update(phrase.split())

    # Latin tokens
    words = re.findall(r"[A-Za-z+#.]{3,}", normalized_text)
    for word in words:
        if word not in STOPWORDS and word not in phrase_words:
            keywords.add(word)

    # Hebrew tokens (3+ letters)
    hebrew_words = re.findall(r"[\u0590-\u05FF]{3,}", text)
    for word in hebrew_words:
        if word not in STOPWORDS:
            keywords.add(word)

    return normalize_skills(sorted(keywords))
