def calculate_trend_score(interactions, speed, media_coverage, relevance):
    """Formula base per il calcolo del trend score."""
    score = (
        interactions * 0.4 +
        speed * 0.3 +
        media_coverage * 0.2 +
        relevance * 0.1
    )
    return max(score, 0)


def evaluate_relevance(content):
    """Valuta la rilevanza di un contenuto basandosi su keyword."""
    keywords = ["breaking", "urgente", "esclusivo", "ultimo momento", "viral", "shock"]
    content_lower = content.lower()
    score = sum(1 for kw in keywords if kw in content_lower)
    return min(score, 5)