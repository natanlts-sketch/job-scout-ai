import re


STOPWORDS = {
    "the", "and", "with", "for", "from", "into",
    "using", "work", "experience", "years",
    "skills", "ability", "our", "you", "your",
    "analyst", "data", "cleaning", "dashboard", "dashboards",
}


TECH_PHRASES = {
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
}


def extract_keywords(text):
    normalized_text = text.lower()
    keywords = set()
    phrase_words = set()

    for phrase in TECH_PHRASES:
        if phrase in normalized_text:
            keywords.add(phrase)
            phrase_words.update(phrase.split())

    words = re.findall(r"[A-Za-z+#.]{3,}", normalized_text)

    for word in words:
        if word not in STOPWORDS and word not in phrase_words:
            keywords.add(word)

    return sorted(keywords)
