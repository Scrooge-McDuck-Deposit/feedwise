import pytest
from src.charts.bubble_chart import generate_bubble_chart

def test_generate_bubble_chart():
    test_data = [
        {"title": "Test News 1", "interactions": 1000, "trend_score": 50, "category": "Tech"},
        {"title": "Test News 2", "interactions": 5000, "trend_score": 80, "category": "Health"},
        {"title": "Test News 3", "interactions": 3000, "trend_score": 70, "category": "Science"},
    ]
    
    fig = generate_bubble_chart(test_data)
    
    assert fig is not None
    assert 'data' in fig
    assert len(fig['data']) == len(test_data)
    
    for i, news in enumerate(test_data):
        assert fig['data'][i]['text'] == news['title']
        assert fig['data'][i]['marker']['size'] == news['trend_score'] * 10  # Assuming size is scaled by 10
        assert fig['data'][i]['x'] == news['interactions']
        assert fig['data'][i]['y'] == news['trend_score']