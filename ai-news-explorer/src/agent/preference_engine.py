class PreferenceEngine:
    def __init__(self):
        self.likes = []
        self.dislikes = []
        self.excluded_sources = []

    def add_like(self, article_id):
        if article_id not in self.likes:
            self.likes.append(article_id)

    def add_dislike(self, article_id):
        if article_id not in self.dislikes:
            self.dislikes.append(article_id)

    def exclude_source(self, source_name, reason=None):
        if source_name not in self.excluded_sources:
            self.excluded_sources.append({'source': source_name, 'reason': reason})

    def get_preferences(self):
        return {
            'likes': self.likes,
            'dislikes': self.dislikes,
            'excluded_sources': self.excluded_sources
        }

    def clear_preferences(self):
        self.likes.clear()
        self.dislikes.clear()
        self.excluded_sources.clear()