import pytest
from src.agent.recommender import RecommenderAgent
from src.agent.preference_engine import PreferenceEngine

def test_recommender_agent_initialization():
    agent = RecommenderAgent()
    assert agent is not None

def test_filtering_news_based_on_likes():
    agent = RecommenderAgent()
    agent.preference_engine = PreferenceEngine()
    agent.preference_engine.likes = [1, 2]  # Simulating user likes
    news_articles = [
        {'id': 1, 'title': 'News A', 'category': 'Tech'},
        {'id': 2, 'title': 'News B', 'category': 'Health'},
        {'id': 3, 'title': 'News C', 'category': 'Tech'},
    ]
    recommended = agent.filter_news(news_articles)
    assert len(recommended) == 2  # Should return articles with IDs 1 and 2

def test_excluding_sources():
    agent = RecommenderAgent()
    agent.preference_engine = PreferenceEngine()
    agent.preference_engine.excluded_sources = ['Source A']  # Simulating excluded source
    news_articles = [
        {'id': 1, 'title': 'News A', 'source': 'Source A'},
        {'id': 2, 'title': 'News B', 'source': 'Source B'},
    ]
    recommended = agent.filter_news(news_articles)
    assert len(recommended) == 1  # Should exclude 'News A'

def test_recommendation_adjustment_based_on_dislikes():
    agent = RecommenderAgent()
    agent.preference_engine = PreferenceEngine()
    agent.preference_engine.dislikes = [3]  # Simulating user dislikes
    news_articles = [
        {'id': 1, 'title': 'News A', 'trend_score': 10},
        {'id': 2, 'title': 'News B', 'trend_score': 20},
        {'id': 3, 'title': 'News C', 'trend_score': 30},
    ]
    recommended = agent.filter_news(news_articles)
    assert all(article['id'] != 3 for article in recommended)  # Should not include disliked article

def test_recommendation_with_no_preferences():
    agent = RecommenderAgent()
    news_articles = [
        {'id': 1, 'title': 'News A'},
        {'id': 2, 'title': 'News B'},
    ]
    recommended = agent.filter_news(news_articles)
    assert len(recommended) == 2  # Should return all articles if no preferences are set