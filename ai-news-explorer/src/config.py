# File: /ai-news-explorer/ai-news-explorer/src/config.py

class Config:
    API_KEYS = {
        "twitter": "YOUR_TWITTER_API_KEY",
        "facebook": "YOUR_FACEBOOK_API_KEY",
        "instagram": "YOUR_INSTAGRAM_API_KEY",
        "tiktok": "YOUR_TIKTOK_API_KEY"
    }
    
    DEFAULT_SOURCES = {
        "social_media": [
            {"name": "Twitter", "url": "https://twitter.com"},
            {"name": "Facebook", "url": "https://facebook.com"},
            {"name": "Instagram", "url": "https://instagram.com"},
            {"name": "TikTok", "url": "https://tiktok.com"}
        ],
        "news_websites": [
            {"name": "Ansa", "url": "https://www.ansa.it/sito/ansait_rss.xml"},
            {"name": "Il Post", "url": "https://www.ilpost.it/feed/"},
            {"name": "Hardware Upgrade", "url": "https://www.hwupgrade.it/rss_news.xml"},
            {"name": "Punto Informatico", "url": "https://www.punto-informatico.it/feed/"},
            {"name": "Le Scienze", "url": "https://www.lescienze.it/rss/all/rss2.0.xml"}
        ],
        "blogs": [
            {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
            {"name": "Wired", "url": "https://www.wired.com/feed"},
            {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
            {"name": "Medium", "url": "https://medium.com/feed"}
        ],
        "video_platforms": [
            {"name": "YouTube", "url": "https://www.youtube.com/"},
            {"name": "Vimeo", "url": "https://vimeo.com/"}
        ],
        "podcasts": [
            {"name": "Spotify", "url": "https://www.spotify.com"},
            {"name": "Apple Podcasts", "url": "https://podcasts.apple.com"}
        ]
    }
    
    TREND_CRITERIA = {
        "interaction_volume": "High volume of shares, likes, comments, and clicks.",
        "speed_of_dissemination": "Rapid rise in popularity across social media.",
        "media_coverage": "Coverage by multiple news outlets and influencers.",
        "timeliness": "Current events or trending topics.",
        "newsworthiness": "Impact, uniqueness, conflict, or celebrity involvement."
    }