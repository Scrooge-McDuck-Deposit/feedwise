import feedparser


def parse_rss_feed(url, max_entries=10):
    """Parsa un singolo feed RSS e restituisce una lista di articoli."""
    try:
        feed = feedparser.parse(url)
        articles = []

        for entry in feed.entries[:max_entries]:
            image = ""
            if hasattr(entry, "media_content") and entry.media_content:
                image = entry.media_content[0].get("url", "")
            elif hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                image = entry.media_thumbnail[0].get("url", "")
            elif hasattr(entry, "enclosures") and entry.enclosures:
                for enc in entry.enclosures:
                    if "image" in enc.get("type", ""):
                        image = enc.get("href", "")
                        break

            articles.append({
                "title": entry.get("title", "No Title"),
                "link": entry.get("link", "#"),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", "")[:200],
                "image": image,
            })

        return articles
    except Exception:
        return []


def fetch_all_feeds(feed_urls, max_per_feed=10):
    """Scarica articoli da una lista di URL RSS."""
    all_articles = []
    for url in feed_urls:
        articles = parse_rss_feed(url, max_entries=max_per_feed)
        all_articles.extend(articles)
    return all_articles