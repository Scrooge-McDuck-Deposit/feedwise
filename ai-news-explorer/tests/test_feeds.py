import pytest
from src.feeds.rss_parser import parse_rss_feed
from src.feeds.social_scraper import scrape_social_media
from src.feeds.source_registry import get_sources

def test_parse_rss_feed():
    # Test parsing a valid RSS feed
    feed_url = "https://www.ansa.it/sito/ansait_rss.xml"
    articles = parse_rss_feed(feed_url)
    assert len(articles) > 0
    assert all('title' in article for article in articles)
    assert all('link' in article for article in articles)

def test_scrape_social_media():
    # Test scraping social media for trending topics
    platform = "Twitter"
    trending_topics = scrape_social_media(platform)
    assert len(trending_topics) > 0
    assert all('topic' in topic for topic in trending_topics)

def test_get_sources():
    # Test retrieving sources from the source registry
    sources = get_sources()
    assert len(sources) > 0
    assert all('name' in source for source in sources)
    assert all('url' in source for source in sources)