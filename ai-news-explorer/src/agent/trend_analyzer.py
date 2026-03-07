class TrendAnalyzer:
    def __init__(self, interaction_data=None):
        self.interaction_data = interaction_data or []

    def calculate_trend_score(self, article):
        interactions = article.get("interactions", 0)
        speed = article.get("speed", 1)
        coverage = article.get("coverage", 1)
        relevance = article.get("relevance", 1)

        score = (
            interactions * 0.4 +
            speed * 0.3 +
            coverage * 0.2 +
            relevance * 0.1
        )
        return max(score, 0)

    def analyze_trends(self):
        trend_scores = {}
        for article in self.interaction_data:
            article_id = article.get("id", "")
            score = self.calculate_trend_score(article)
            trend_scores[article_id] = score
        return trend_scores

    def get_top_trending(self, n=10):
        scores = self.analyze_trends()
        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[:n]

    @staticmethod
    def evaluate_relevance(content):
        keywords = ["breaking", "urgente", "esclusivo", "ultimo momento", "viral"]
        content_lower = content.lower()
        score = sum(1 for kw in keywords if kw in content_lower)
        return min(score, 5)