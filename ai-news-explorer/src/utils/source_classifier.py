def classify_source_type(source_name):
    """Classifica il tipo di una fonte basandosi sul nome."""
    social_keywords = ["twitter", "facebook", "instagram", "tiktok", "reddit"]
    news_keywords = ["ansa", "repubblica", "corriere", "bbc", "cnn", "reuters"]
    tech_keywords = ["techcrunch", "verge", "wired", "ars technica"]

    name_lower = source_name.lower()

    for kw in social_keywords:
        if kw in name_lower:
            return "social"
    for kw in news_keywords:
        if kw in name_lower:
            return "news"
    for kw in tech_keywords:
        if kw in name_lower:
            return "tech"

    return "general"