import pytest
from src.utils.session_manager import SessionManager
from src.utils.trend_scoring import calculate_trend_score
from src.utils.source_classifier import classify_source

def test_session_manager_initialization():
    session_manager = SessionManager()
    assert session_manager.likes == []
    assert session_manager.dislikes == []
    assert session_manager.excluded_sources == []

def test_calculate_trend_score():
    interactions = 1000
    velocity = 2.5
    expected_score = (interactions * 0.4) + (velocity * 10000 * 0.3)
    assert calculate_trend_score(interactions, velocity) == expected_score

def test_classify_source():
    assert classify_source("https://www.ansa.it") == "free"
    assert classify_source("premium_mock_1") == "paid"
    assert classify_source("https://www.hwupgrade.it") == "free"