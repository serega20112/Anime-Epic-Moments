from datetime import datetime


class Favorite:
    def __init__(self, user_id: int, anime_id: int, added_at: datetime = None):
        self.user_id = user_id
        self.anime_id = anime_id
        self.added_at = added_at or datetime.utcnow()
